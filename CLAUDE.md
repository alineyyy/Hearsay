# Hearsay — project context for Claude Code

**Hearsay** checks the paperwork advice international students pass around against dated
official French sources — and tells you exactly what changed.

The name is the problem it solves: the advice students rely on is hearsay — confident,
specific, and often two years out of date. Use this name and this pitch in the README,
the UI and the Devpost entry.

Read this first. It carries the decisions and constraints that are not obvious from the code.

## What this is

A submission to the **Agents for Humans Hackathon** (AWS / Devpost), track **Good Neighbor
Agents**. Deadline **2026-09-14 17:00 PT**. Built with the **AWS Strands Agents SDK** on
Amazon Bedrock. Deploying to AWS AgentCore is an optional scoring bonus we still intend to do.

The author is an international student in France and the product's own target user.

## The product thesis (this drives every design decision)

International students in France navigate administrative procedures using two kinds of
information, each broken in a different way:

| | Official sources (service-public.fr, préfecture, ANEF) | Community advice (social platforms, senior students) |
|---|---|---|
| Authority | definitive | unverifiable |
| Edge cases | not covered | this is its whole value |
| Freshness | maintained, dated | **posts never expire, rules do** |
| Readability | French administrative register | plain language |

Nothing on the market cross-references the two. **That gap is the product**: this agent does
not just retrieve — it checks community claims against dated official sources and reports a
per-claim verdict with confidence and citation.

Two entry modes, one pipeline — not a toggle. Whether the verification stages run depends
on whether anything was pasted:
- **Ask**: a question in any language → an actionable checklist.
- **Verify**: paste community advice → a per-claim verdict, plus the checklist.

**It is a conversation, not a lookup.** French procedures depend on permit type, département
and nationality — details the user often doesn't know matter. So the agent must be able to
ask and be answered. History is kept per session (`_sessions` in `src/web/server.py`, keyed
by a browser-generated id) and fed to the planner and guide writer. A guide with no steps is
a bug, not a safe default: when something is missing, give the steps that hold regardless,
mark the ones that depend on it, and put the question in `open_questions` so the user can
simply reply.

## Language rules

- **The product is multilingual.** The user writes in any language; the agent answers in that
  same language. Retrieval always goes through French, because the corpus is French. The
  language barrier is part of the problem being solved, not a feature bolted on.
- **The repository is English** — prompts, code, comments, docs, README, demo video. This is an
  internationally judged submission.
- French administrative terms stay in French in every language (titre de séjour, récépissé,
  préfecture, CAF, Ameli, timbre fiscal) — the user meets those exact words on real forms.
- The author converses with Claude in Chinese. That does not change the repo language.

## Architecture

```
question / pasted community advice   (any language)
              │
   1. Planner agent        → QueryPlan   (French search terms, user's situation, language)
              │
   2. Retrieval            → official passages + URL + last official update date
      (deterministic BM25, no LLM)
              │
   3. Claim extractor      → ClaimSet    (checkable assertions)     [verify mode only]
              │
   4. Verifier agent       → VerdictSet  (per-claim verdict + recency check)
      (tools: search_official_docs, check_information_recency)
              │
   5. Guide writer agent   → Guide       (checklist, sources labelled)
```

**Governing rule:** facts come from deterministic tools (retrieval, date arithmetic);
judgement comes from agents. Every conclusion traces to an official document ID and URL.
When evidence is absent the correct output is `not_covered` — never a confident guess.
For this user, "the official documents don't say" is a genuinely useful answer.

## Layout

```
src/ingest/parse_spf.py     official XML → data/corpus.jsonl   (run once)
src/retrieval/corpus.py     chunking + BM25 index (2027 docs / 24457 chunks)
src/community/sources.py    pluggable community-source interface
src/agents/schemas.py       Pydantic contracts between stages
src/agents/tools.py         deterministic tools exposed to agents
src/agents/pipeline.py      the five-stage orchestration
run.py                      CLI entry point with built-in demo material
learning/                   early SDK exploration, not part of the product
```

## Data source (attribution is a licence condition)

Official corpus: **Service-Public.gouv.fr / DILA**, published on data.gouv.fr under
**Licence Ouverte 2.0 (Etalab)**. Reuse requires naming the source, the download URL and the
file date. Keep that attribution in the README and in the UI.

Regenerate the corpus (the raw file is gitignored — 23 MB zip, 148 MB extracted):

```bash
mkdir -p data && curl -L -o data/service-public.xml \
  "https://www.data.gouv.fr/api/1/datasets/r/0ed10f28-d197-4324-97b3-037f625095ac"
mkdir -p data/spf_raw && unzip -oq data/service-public.xml -d data/spf_raw
python3 src/ingest/parse_spf.py
```

The file is served with an `.xml` extension but **is actually a ZIP** of ~5552 per-fiche XML
files. Each fiche carries `dateDerniereModificationImportante` and `spUrl` — those two fields
are what make the recency verdicts possible, so never drop them in any transformation.

## Decisions already made (do not silently revisit)

- **No scraping of closed social platforms.** Considered and rejected: heavy anti-bot
  measures, ToS exposure on a public judged repo, and above all demo fragility — a live
  scrape that breaks on recording day loses the submission. Community input arrives instead
  through `src/community/sources.py`, which abstracts the source. Pasted text is the primary
  implementation and mirrors the real user workflow. Adding a connector later is a plug-in.
- **Queries are translated to formal French by the planner agent**, not matched literally.
  A literal translation of the user's phrasing retrieves nothing; the corpus uses
  administrative register.
- **Scope is France + international students.** Wider Europe is future work, in the README.
- **Breadth is cheap, depth is not.** The pipeline is topic-agnostic, so it already covers
  residence permits, CAF housing aid, sécurité sociale and banking. The demo video should
  still go deep on one or two stories rather than skim four.

## Known gotchas

- **`structured_output()` needs a prompt argument** when it follows a tool-using `agent(...)`
  call. Bedrock's `global.anthropic.claude-sonnet-4-6` rejects a conversation ending on an
  assistant turn: *"This model does not support assistant message prefill."* Both call sites
  in `pipeline.py` pass an explicit prompt for this reason. Keep it that way.
- One `run()` makes several Bedrock calls and takes a minute or two. That is expected.
- `get_corpus()` is an `lru_cache` singleton; the BM25 index costs ~1s to build, once.

## Running it

```bash
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py verify        # community advice in English
python3 run.py verify-zh     # the same advice in Chinese — shows the multilingual path
python3 run.py ask "My student residence permit expires soon. How do I renew it?"
```

Requires AWS credentials with Bedrock access (region us-west-2) and model access enabled for
Anthropic Claude.

## Still to do

- [ ] Web UI (the deliverable is meant to be a real web app, not a CLI)
- [ ] Architecture diagram + README (both are submission requirements)
- [ ] AgentCore deployment (bonus scoring; also yields the optional live demo link)
- [ ] Demo video, ≤5 min, must contain both a working demo and a pitch
- [ ] Push to a public GitHub repo with an MIT or Apache licence
