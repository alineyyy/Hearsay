"""
The core pipeline: cross-checking official sources against community advice.

Five specialised agents, handing structured data to each other:

    question / pasted community advice  (any language)
                    │
        1. Planner  ──────> QueryPlan   (French search terms + user's situation)
                    │
        2. Retrieval (deterministic tool, no LLM)
                    │       official passages, each with URL + last update date
                    │
        3. Claim extractor ──> ClaimSet  (checkable assertions)   [verify mode only]
                    │
        4. Verifier ───────> VerdictSet  (per-claim judgement + recency check)
                    │
        5. Guide writer ───> Guide       (actionable checklist,每 step 标注来源)

Design rule: facts come from deterministic tools (retrieval, date comparison);
judgement comes from agents. Every conclusion traces back to an official
document ID and URL.
"""

import os
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.schemas import ClaimSet, Guide, QueryPlan, VerdictSet  # noqa: E402
from agents.tools import check_information_recency, search_official_docs  # noqa: E402
from community.sources import CommunityItem, PastedSource, gather  # noqa: E402
from retrieval.corpus import get_corpus  # noqa: E402

MODEL_ID = os.getenv("NAVIGATOR_MODEL_ID") or None

SHARED_CONTEXT = f"""
You help international students in France deal with administrative procedures.
Today is {date.today().isoformat()}.

Non-negotiable principles:

- French administrative procedures vary by permit type, university, département and
  nationality. Never present a "standard procedure" as if it applied to everyone.
- Official sources are the only authority. Community advice is a supplementary lead,
  valuable mainly for edge cases official documents do not cover.
- Every conclusion must trace back to an official document ID and URL. Never answer
  from impression or memory.
- Keep French administrative terms in French (titre de séjour, récépissé, préfecture,
  CAF, Ameli, timbre fiscal) even when writing in another language — the user will
  encounter these exact words on forms and websites.

LANGUAGE: reply in the same language the user wrote in. If they wrote in Chinese,
reply in Chinese; in Spanish, reply in Spanish; and so on. Default to English when
the language is unclear. This matters: the language barrier is a large part of the
problem you exist to solve.
"""

PLANNER_PROMPT = SHARED_CONTEXT + """
YOUR ROLE: understand the request and plan the search.

Given a question in any language:

1. Work out which administrative procedure this actually is.
2. Identify what is unusual about this person's situation — that is usually where
   they are really stuck, and where generic advice fails them.
3. Translate the question into formal French administrative search terms. This step
   decides whether anything is found at all, so use the wording that genuinely appears
   in French government documents, not a literal translation.
4. Note which key facts are still missing for an accurate answer.
5. Record the language the user wrote in, so later stages answer in it.
"""

CLAIM_PROMPT = SHARED_CONTEXT + """
YOUR ROLE: break community advice into checkable claims.

The user pastes advice from a social platform, a forum, or a senior student. Split it
into individual assertions that can be checked against official documents.

Rules:
- Extract only factual assertions (procedure, documents, deadlines, amounts, eligibility).
  Ignore pure sentiment.
- Each claim must be specific. "It's a hassle" is not a claim; "you must book an
  appointment two months in advance" is.
- Attach French search terms for verifying each claim.
- Watch for time cues (post date, "last year", "the new rules") — these are critical
  for judging whether the advice has since gone stale.
"""

VERIFIER_PROMPT = SHARED_CONTEXT + """
YOUR ROLE: cross-verification. This is the heart of the product.

For each community claim, deliver one verdict:

- confirmed:      official sources support it
- outdated:       it was correct once, but official documents were updated since and it
                  no longer holds
- partially_true: broadly right, details differ — say exactly which details
- not_covered:    official sources are silent on this situation. Say so plainly, do not
                  invent an answer, and flag that this is a case to take directly to the
                  préfecture or the relevant office
- contradicted:   official sources state the opposite

Requirements:
- Call search_official_docs to check. Never rule from memory.
- Call check_information_recency to compare dates whenever timing could matter.
- Attach the official document ID, URL and last update date to every verdict.
- When you cannot find evidence, return not_covered. An honest "the official documents
  don't say" is far more useful to this user than a confident guess.
"""

GUIDE_PROMPT = SHARED_CONTEXT + """
YOUR ROLE: write the actionable guide.

Turn the official evidence (and any verdicts on community advice) into a checklist the
user can follow.

Requirements:
- Steps must be concrete: which website or office, which documents, what deadline.
- Label every step's source honestly (official / community / official_and_community).
  This is how the user decides what to trust — never blur it.
- List the traps separately: common rejection reasons, easily forgotten documents,
  timing pitfalls.
- If official documents do not cover the user's situation, do not improvise. Put it in
  open_questions and say who they should ask.
"""


@lru_cache(maxsize=1)
def _model():
    """
    Bedrock with constrained decoding (`strict_tools`) turned on.

    Without it the model is free to hand-serialise a nested field, and on the
    deepest schema here it does: `VerdictSet.verdicts` comes back as a JSON
    *string* rather than a list. Worse, that string is itself invalid JSON as
    soon as an explanation contains an unescaped double quote — which Chinese
    and French prose produces constantly. Strict mode compiles the schema into
    a decoding grammar, so the shape is guaranteed rather than hoped for.
    """
    kwargs = {"strict_tools": True}
    if MODEL_ID:
        kwargs["model_id"] = MODEL_ID
    return BedrockModel(**kwargs)


def _agent(system_prompt, tools=None):
    kwargs = {"system_prompt": system_prompt, "model": _model()}
    if tools:
        kwargs["tools"] = tools
    return Agent(**kwargs)


def _format_evidence(results):
    """Render retrieval hits as an evidence block for an agent to read."""
    if not results:
        return "(no matching content found in the official corpus)"
    blocks = []
    for r in results:
        block = (
            f"[OFFICIAL DOC {r['doc_id']}] {r['title']}\n"
            f"Section: {r['section'] or '(body)'}\n"
            f"Last official update: {r['last_official_update']}\n"
            f"Official URL: {r['official_url']}\n"
            f"Content: {r['text']}"
        )
        svcs = [s for s in r.get("online_services", []) if s.get("url")]
        if svcs:
            block += "\nOnline service: " + "; ".join(
                f"{s['title']} -> {s['url']}" for s in svcs[:2]
            )
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


class Navigator:
    """Administrative navigator for international students in France."""

    def __init__(self):
        self.corpus = get_corpus()

    # ---------- 1. planning ----------
    def plan(self, question: str, profile: str = "") -> QueryPlan:
        prompt = f"User question:\n{question}"
        if profile:
            prompt += f"\n\nContext the user already provided:\n{profile}"
        return _agent(PLANNER_PROMPT).structured_output(QueryPlan, prompt)

    # ---------- 2. retrieval (deterministic) ----------
    def retrieve(self, plan: QueryPlan, per_query: int = 4):
        seen, results = set(), []
        themes = plan.themes or [None]
        for query in plan.french_queries:
            for theme in themes:
                for r in self.corpus.search(query, top_k=per_query, theme=theme):
                    key = (r["doc_id"], r["section"])
                    if key not in seen:
                        seen.add(key)
                        results.append(r)
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:12]

    # ---------- 3. claim extraction ----------
    def extract_claims(self, items: list[CommunityItem], language: str) -> ClaimSet:
        joined = "\n\n---\n\n".join(
            f"[source: {it.source_name}"
            + (f" | posted: {it.posted_date}" if it.posted_date else " | post date unknown")
            + f"]\n{it.text}"
            for it in items
        )
        return _agent(CLAIM_PROMPT).structured_output(
            ClaimSet,
            f"The user writes in {language}; phrase the claims in that language.\n\n"
            f"Break down this community advice:\n\n{joined}",
        )

    # ---------- 4. cross-verification ----------
    def verify(self, claim_set: ClaimSet, evidence_text: str, language: str) -> VerdictSet:
        agent = _agent(
            VERIFIER_PROMPT, tools=[search_official_docs, check_information_recency]
        )
        claims_text = "\n".join(
            f"{i}. {c.text}  (topic: {c.topic}; suggested queries: {', '.join(c.french_queries)})"
            for i, c in enumerate(claim_set.claims, 1)
        )
        prompt = (
            f"The user writes in {language}. Write claim text and explanations in that language.\n\n"
            f"Time cues in the community advice: {claim_set.source_hint}\n\n"
            f"Claims to verify:\n{claims_text}\n\n"
            f"Official evidence retrieved so far:\n{evidence_text}\n\n"
            "Verify each claim. Call search_official_docs whenever the evidence above is "
            "insufficient, and check_information_recency whenever timing matters."
        )
        # Pass 1: let the agent verify with tools.
        agent(prompt)
        # Pass 2: extract structured verdicts. A prompt is required here — the model
        # rejects a conversation that ends on an assistant turn (no assistant prefill).
        return agent.structured_output(
            VerdictSet,
            "Now return the structured verdict for every claim you just verified. "
            "Each verdict must carry the official document ID, URL and last update "
            f"date you relied on. Write claim text and explanations in {language}.",
        )

    # ---------- 5. guide ----------
    def build_guide(self, question, plan, evidence_text, verdicts=None) -> Guide:
        agent = _agent(GUIDE_PROMPT, tools=[search_official_docs])
        parts = [
            f"The user writes in {plan.user_language}. Write the entire guide in that language.",
            f"\nUser question: {question}",
            f"Procedure identified: {plan.procedure}",
            f"User's situation: {plan.user_situation}",
            f"\nOfficial evidence:\n{evidence_text}",
        ]
        if verdicts and verdicts.verdicts:
            vt = "\n".join(
                f"- \"{v.claim}\" -> {v.status} (confidence {v.confidence}): {v.explanation}"
                for v in verdicts.verdicts
            )
            parts.append(f"\nVerdicts on the community advice:\n{vt}")
        if plan.missing_info:
            parts.append(
                "\nNote: the user has not yet provided: " + "; ".join(plan.missing_info)
            )
        parts.append("\nWrite the guide. Label every step's source honestly.")

        agent("\n".join(parts))
        # Same constraint as in verify(): end the conversation on a user message.
        return agent.structured_output(
            Guide,
            "Now return the structured guide, written entirely in "
            f"{plan.user_language}. Label every step's source honestly.",
        )

    # ---------- entry point ----------
    def run(self, question="", community_text="", community_date="", profile="",
            on_event=None):
        """
        Ask mode:    pass `question` only.
        Verify mode: pass `community_text` (optionally with a `question` framing it).

        `on_event(stage, status, detail)` is called as each stage starts and finishes,
        so a UI can show the pipeline working instead of an opaque spinner. A run takes
        a minute or two; making the stages visible turns the wait into the story.
        """
        if not question and not community_text:
            raise ValueError("provide either a question or community advice to check")

        def emit(stage, status, detail=""):
            if on_event:
                on_event(stage, status, detail)

        seed = question or "Is the following community advice still accurate?"

        emit("plan", "start")
        plan = self.plan(seed, profile)
        emit("plan", "done",
             f"Identified as \u201c{plan.procedure}\u201d \u00b7 answering in {plan.user_language}")

        emit("retrieve", "start")
        official = self.retrieve(plan)
        evidence_text = _format_evidence(official)
        newest = max((r["last_official_update"] for r in official
                      if r["last_official_update"] != "\u672a\u6807\u6ce8"), default="\u2014")
        emit("retrieve", "done",
             f"{len(official)} official passages \u00b7 most recent update {newest}")

        verdicts = None
        claim_set = None
        if community_text.strip():
            emit("extract", "start")
            items = gather([PastedSource(community_text, posted_date=community_date)], seed)
            claim_set = self.extract_claims(items, plan.user_language)
            emit("extract", "done", f"{len(claim_set.claims)} checkable claims found")

            emit("verify", "start", f"checking {len(claim_set.claims)} claims")
            verdicts = self.verify(claim_set, evidence_text, plan.user_language)
            counts = {}
            for v in verdicts.verdicts:
                counts[v.status] = counts.get(v.status, 0) + 1
            emit("verify", "done",
                 " \u00b7 ".join(f"{n} {s.replace('_', ' ')}" for s, n in counts.items()))

        emit("guide", "start")
        guide = self.build_guide(seed, plan, evidence_text, verdicts)
        emit("guide", "done", f"{len(guide.steps)} steps")

        return {
            "plan": plan,
            "official_sources": official,
            "claims": claim_set,
            "verdicts": verdicts,
            "guide": guide,
        }
