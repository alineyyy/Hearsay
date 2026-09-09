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
4. Note which key facts are still missing for an accurate answer. Be demanding about this.
   In French administration the same question has different answers depending on:
     - which permit the person holds (étudiant, passeport talent, vie privée et familiale,
       Algerian nationals under the 1968 accord, EU/EEA…),
     - which département or préfecture handles them — practice varies a great deal,
     - their nationality, where a bilateral agreement may override the general rule,
     - where they are in the timeline (how long until expiry, first renewal or not).
   If the user has not told you the ones that matter for their question, list them. Saying
   nothing is missing when something is means the answer comes out generic — which is the
   exact failure that sends people back to asking their friends.
5. Record the language the user wrote in, so later stages answer in it.
6. Decide whether the input actually contains anything to verify. Users type whatever is on
   their mind into one box — sometimes a plain question about their own situation, sometimes
   advice someone gave them, sometimes both. Only set contains_claims_to_check when there
   are assertions from someone else that official sources could confirm or contradict.
   "My permit expires soon, how do I renew it?" is a question, not a claim. Never route a
   plain question into verification: ruling on the user's own question is nonsense.

When earlier turns of the conversation are supplied, read them first. A follow-up like
"then what documents do I need?" or "I have a passeport talent" only makes sense against
what was already discussed — resolve it against that context rather than treating it as a
fresh question, and carry forward any detail the user has now supplied.
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
- Keep each explanation to two sentences at most. Lead with what is wrong. The reader is
  scanning several verdicts at once, not reading an essay.
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

TWO DIFFERENT THINGS, DO NOT CONFUSE THEM:

- `follow_up_question` — what YOU need from the USER. Required. If any detail you do not
  know would change your answer (permit type, département, nationality, time until expiry),
  ask for it here, in one replyable line. This is how the conversation continues, and it is
  the difference between an answer written for this person and a generic procedure they
  could have found themselves. On a first exchange you will nearly always have something to
  ask; leaving it empty is a claim that nothing could change your answer.

- `open_questions` — what the USER must confirm with an AUTHORITY, because official
  documents are silent on their case. Name who to ask. Not a place to interrogate the user.

BREVITY IS A FEATURE. This is read on a screen by someone who is stressed and short on
time. Summary: two sentences. Steps: at most six, one imperative line each. Traps: at most
three. Cut every sentence that does not change what the reader does next. A wall of text is
the same failure as no answer.

NEVER return a guide with no steps. Missing information is normal — French procedures
depend on permit type, département and nationality, and the user often does not know which
details matter. When something is missing:
  - give the steps that hold regardless of the unknown,
  - mark the steps that depend on it and say what changes either way,
  - put the specific question you need answered in open_questions, phrased so the user can
    simply reply to it.
A guide that says only "I need more information" is a failure. The user came here stuck;
send them away with something they can do today, plus one clear question.
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


def _format_history(history):
    """Render prior turns compactly so later stages can resolve follow-ups."""
    if not history:
        return ""
    lines = []
    for i, turn in enumerate(history, 1):
        lines.append(f"--- turn {i} ---")
        if turn.get("question"):
            lines.append(f"User asked: {turn['question']}")
        if turn.get("community_text"):
            lines.append("User pasted community advice to be checked.")
        if turn.get("procedure"):
            lines.append(f"Identified procedure: {turn['procedure']}")
        if turn.get("situation"):
            lines.append(f"Situation established: {turn['situation']}")
        if turn.get("summary"):
            lines.append(f"You answered: {turn['summary']}")
        if turn.get("open_questions"):
            lines.append("You asked the user to confirm: " + "; ".join(turn["open_questions"]))
    return "\n".join(lines)


class Navigator:
    """Administrative navigator for international students in France."""

    def __init__(self):
        self.corpus = get_corpus()

    # ---------- 1. planning ----------
    def plan(self, question: str, profile: str = "", history=None) -> QueryPlan:
        parts = []
        if history:
            parts.append("Earlier in this conversation:\n" + _format_history(history))
        parts.append(f"The user now says:\n{question}")
        if profile:
            parts.append(f"Context the user already provided:\n{profile}")
        return _agent(PLANNER_PROMPT).structured_output(QueryPlan, "\n\n".join(parts))

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
    def build_guide(self, question, plan, evidence_text, verdicts=None, history=None) -> Guide:
        # Deliberately no tools here. Stage 2 already retrieved the evidence and stage 4
        # already dug deeper where it mattered; giving this agent a search tool only makes
        # it re-retrieve in a loop, which is slow and adds nothing. One call, one guide.
        agent = _agent(GUIDE_PROMPT)
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
        if history:
            parts.insert(1, "\nEarlier in this conversation:\n" + _format_history(history)
                         + "\nBuild on this. Do not repeat what you already told them.")
        if plan.missing_info:
            parts.append(
                "\nThe user has not yet told you: " + "; ".join(plan.missing_info)
                + "\nGive the steps that hold regardless, mark the ones that depend on this,"
                " and put the question in open_questions so they can just reply to it."
            )
        else:
            parts.append(
                "\nBefore you finish: is there any detail you do not know that would change "
                "this answer — permit type, département, nationality, time until expiry? "
                "If so, ask for it in open_questions."
            )
        parts.append("\nWrite the guide. Label every step's source honestly.")

        parts.append(
            f"\nWrite the guide in {plan.user_language}. Label every step's source honestly. "
            "Populate `steps` — at least one, at most six, each a single imperative line."
        )
        guide = agent.structured_output(Guide, "\n".join(parts))

        # Belt and braces. Prompting alone has not proved sufficient: the tool-using pass
        # sometimes answers in prose that the extraction step cannot turn into steps, and a
        # guide with no steps is useless to someone who came here stuck.
        if not guide.steps:
            guide = agent.structured_output(
                Guide,
                "\n".join(parts) + "\n\nYour previous attempt returned no steps, which is "
                "not acceptable. Turn the official evidence above into a numbered checklist: "
                "at least one step, at most six, each a single imperative line saying what to "
                "do, where, and by when. If a detail is still missing, give the steps that "
                "hold regardless and put the missing detail in open_questions.",
            )

        return guide

    # ---------- entry point ----------
    def run(self, text="", posted_date="", history=None, on_event=None,
            question="", community_text="", community_date=""):
        """
        One entry point. The user types whatever they have — a question, advice someone
        gave them, or both — and the planner decides whether any of it is checkable.
        Asking the user to classify their own input was a design mistake; this is the fix.

        The question/community_text/community_date arguments are kept for the CLI.
        """
        text = text or "\n\n".join(p for p in (community_text, question) if p).strip()
        posted_date = posted_date or community_date
        if not text:
            raise ValueError("nothing to work with — provide some text")

        def emit(stage, status, detail=""):
            if on_event:
                on_event(stage, status, detail)

        emit("plan", "start")
        plan = self.plan(text, history=history)
        emit("plan", "done",
             f"\u201c{plan.procedure}\u201d \u00b7 answering in {plan.user_language}")

        emit("retrieve", "start")
        official = self.retrieve(plan)
        evidence_text = _format_evidence(official)
        newest = max((r["last_official_update"] for r in official
                      if r["last_official_update"] != "\u672a\u6807\u6ce8"), default="\u2014")
        emit("retrieve", "done",
             f"{len(official)} official passages \u00b7 most recent update {newest}")

        verdicts = None
        claim_set = None
        if plan.contains_claims_to_check:
            emit("extract", "start")
            items = gather([PastedSource(text, posted_date=posted_date)], text)
            claim_set = self.extract_claims(items, plan.user_language)
            emit("extract", "done", f"{len(claim_set.claims)} checkable claims found")

            if claim_set.claims:
                emit("verify", "start", f"checking {len(claim_set.claims)} claims")
                verdicts = self.verify(claim_set, evidence_text, plan.user_language)
                counts = {}
                for v in verdicts.verdicts:
                    counts[v.status] = counts.get(v.status, 0) + 1
                emit("verify", "done",
                     " \u00b7 ".join(f"{n} {s.replace('_', ' ')}" for s, n in counts.items()))

        emit("guide", "start")
        guide = self.build_guide(text, plan, evidence_text, verdicts, history=history)
        emit("guide", "done", f"{len(guide.steps)} steps")

        return {
            "plan": plan,
            "official_sources": official,
            "claims": claim_set,
            "verdicts": verdicts,
            "guide": guide,
        }
