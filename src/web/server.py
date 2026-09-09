"""
Hearsay — web server.

One endpoint does the real work. It streams the pipeline's progress as
Server-Sent Events, because a run takes a minute or two and an opaque spinner
would make the product feel broken. Showing the five stages as they execute
turns the wait into the explanation of what Hearsay actually does.
"""

import asyncio
import json
import sys
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agents.pipeline import Navigator  # noqa: E402

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Hearsay", description="Paperwork advice, checked against the source.")

_navigator = None
_navigator_lock = threading.Lock()


def get_navigator():
    """Built once — the BM25 index costs a second and is then reused."""
    global _navigator
    with _navigator_lock:
        if _navigator is None:
            _navigator = Navigator()
    return _navigator


# Conversations are held in memory, keyed by a session id the browser generates.
# French procedures depend on details the user often doesn't know matter, so the agent
# has to be able to ask and be answered — a one-shot exchange cannot do that.
_sessions: dict[str, list] = {}
_sessions_lock = threading.Lock()

MAX_TURNS = 8


def get_history(session_id):
    if not session_id:
        return []
    with _sessions_lock:
        return list(_sessions.get(session_id, []))


def record_turn(session_id, turn):
    if not session_id:
        return
    with _sessions_lock:
        history = _sessions.setdefault(session_id, [])
        history.append(turn)
        del history[:-MAX_TURNS]


class QueryRequest(BaseModel):
    question: str = ""
    community_text: str = ""
    community_date: str = ""
    session_id: str = ""


def serialise(result):
    """Turn the pipeline's mixed output into plain JSON for the browser."""
    plan = result["plan"]
    guide = result["guide"]
    verdicts = result["verdicts"]
    claims = result["claims"]

    return {
        "plan": plan.model_dump(),
        "official_sources": [
            {
                "doc_id": r["doc_id"],
                "title": r["title"],
                "section": r["section"],
                "url": r["official_url"],
                "last_update": r["last_official_update"],
            }
            for r in result["official_sources"]
        ],
        "claim_source_hint": claims.source_hint if claims else "",
        "verdicts": verdicts.model_dump() if verdicts else None,
        "guide": guide.model_dump(),
    }


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "corpus": get_navigator().corpus.stats()}


@app.post("/api/reset")
async def reset(req: QueryRequest):
    with _sessions_lock:
        _sessions.pop(req.session_id, None)
    return {"status": "cleared"}


@app.post("/api/query")
async def query(req: QueryRequest):
    """Run the pipeline, streaming each stage to the browser as it happens."""

    async def event_stream():
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def push(payload):
            loop.call_soon_threadsafe(queue.put_nowait, payload)

        def on_event(stage, status, detail):
            push({"type": "stage", "stage": stage, "status": status, "detail": detail})

        def work():
            try:
                navigator = get_navigator()
                result = navigator.run(
                    question=req.question,
                    community_text=req.community_text,
                    community_date=req.community_date,
                    history=get_history(req.session_id),
                    on_event=on_event,
                )
                record_turn(req.session_id, {
                    "question": req.question,
                    "community_text": bool(req.community_text.strip()),
                    "procedure": result["plan"].procedure,
                    "situation": result["plan"].user_situation,
                    "summary": result["guide"].summary,
                    "open_questions": result["guide"].open_questions,
                })
                push({"type": "result", "data": serialise(result)})
            except Exception as exc:  # surfaced in the UI rather than swallowed
                push({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
            finally:
                push(None)

        threading.Thread(target=work, daemon=True).start()

        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
