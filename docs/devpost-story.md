## Inspiration

Every international student in France has a senior who helped them.

Someone who had already been through it, who told you which documents to bring, how early
to book the appointment, what the préfecture actually wants to see. That help is generous.
It is specific. And it is usually from last year.

French administrative rules change constantly. Forum posts don't. So advice keeps
circulating long after it stopped being true — passed from one student to the next in
group chats, on social platforms, in hallway conversations. I have been on both ends of
that chain. The official websites exist, but they are written in French administrative
register and they describe the standard case, which is rarely anyone's case. So students
do the rational thing: they ask each other.

The gap isn't that official information doesn't exist. It's that nobody reads it — people
use each other instead. Getting it wrong doesn't just cost you a wasted trip to the
préfecture. It can cost you your legal status.

With nearly [445,000 international students in France in 2024-2025](https://www.campusfrance.org/en/actu/pres-de-445-000-etudiants-etrangers-en-france-en-2024-2025),
that informal network is doing an enormous amount of work — and nothing in it has any way
to tell you whether what you just heard is still true.

## What it does

**Hearsay takes the advice you were given and checks it, line by line, against official
French government sources — with the date each rule was last updated.**

You paste what you heard: a message from a friend, a forum post, a screenshot of a group
chat. Hearsay breaks it into individual checkable claims, searches the official corpus for
each one, and returns a verdict per claim:

| Verdict | Meaning |
| --- | --- |
| **Confirmed** | Official sources support this |
| **Outdated** | It was true once — the rules changed after this advice was written |
| **Partly true** | Broadly right, but a specific detail is wrong |
| **Not covered** | Official documents are silent on this situation |
| **Contradicted** | Official sources say the opposite |

Every verdict carries the official document ID, its canonical URL, and the date that
document was last substantively updated. Alongside the verdicts, Hearsay produces an
actionable checklist for what to actually do — and labels every single step as coming from
official sources, community advice, or both.

Two design commitments shaped everything:

**It answers in your language.** You write in English, Chinese, Spanish, Arabic — the
answer comes back in the same language, while retrieval always runs through formal French,
because that's what the corpus is written in. The language barrier is not a side issue
here; it is a large part of why students rely on hearsay in the first place.

**"The official documents don't say" is a valid answer.** When the corpus is silent —
which happens constantly for edge cases, and edge cases are exactly when people go looking
for advice — Hearsay returns *not covered* and tells you to take it to the préfecture. For
this user, an honest gap is far more useful than a confident guess.

It does not tell you to stop asking your friends. It tells you which parts of what they
said are still true.

## How I built it

**The data foundation.** Service-Public.gouv.fr publishes its entire "your rights and
procedures" guide as open data on data.gouv.fr under the Licence Ouverte 2.0 (Etalab).
That turned out to be the thing that makes this project possible rather than hand-wavy:
5,552 official documents, and critically, **each one carries a
`dateDerniereModificationImportante` field and a canonical URL**. Those two fields are what
let Hearsay say "this advice predates a change made on 2026-08-01" instead of vaguely
warning that rules change. I parse the corpus into structured documents, preserving section
structure — including the `Cas` blocks, which is where the official text itself branches by
situation.

**The pipeline.** Five specialised Strands agents, handing structured Pydantic models to
each other rather than free-form text:

1. **Planner** — reads the question in any language and produces a retrieval plan:
   the procedure, the user's situation, and 3–5 *formal French administrative* search
   phrases. This step matters more than it sounds.
2. **Retrieval** — deterministic BM25 over 24,457 chunks. No LLM. Returns passages with
   their URL and official update date attached.
3. **Claim extractor** — splits pasted advice into individually checkable assertions.
   "It's a hassle" is not a claim; "you must book two months ahead" is.
4. **Verifier** — the heart of it. Rules on each claim, calling `search_official_docs` to
   dig further and `check_information_recency` to compare the post's date against the
   official document's update date.
5. **Guide writer** — turns evidence and verdicts into an actionable checklist with honest
   source labels.

The governing rule throughout: **facts come from deterministic tools, judgement comes from
agents.** Retrieval and date arithmetic are plain Python, so every conclusion traces back
to a specific document ID and URL rather than to the model's memory.

**The stack.** AWS Strands Agents SDK on Amazon Bedrock (Claude Sonnet 4.6), Pydantic
structured outputs for every inter-agent handoff, rank-bm25 for retrieval, FastAPI with
Server-Sent Events for the web app.

## Challenges I ran into

**The official dataset lied about its own format.** The download is served with an `.xml`
extension. It is a ZIP archive containing 5,552 individual XML files. I found this by
opening the file and seeing `PK` where a declaration should have been.

**Retrieval across a language barrier.** The user writes Chinese; the corpus is French.
My first instinct — translate the question literally — retrieves nothing, because official
documents don't use the words people use. "续居留" has to become
`renouvellement titre de séjour étudiant`, in the register the government actually writes
in. Making the planner agent responsible for producing *formal administrative French*,
rather than a translation, was the fix that made retrieval work at all.

**A Bedrock constraint I didn't see coming.** My verifier runs the agent with tools first,
then extracts structured output from the conversation. That crashed with
`This model does not support assistant message prefill. The conversation must end with a
user message.` The tool-using pass leaves the conversation on an assistant turn. Passing an
explicit prompt to `structured_output()` fixes it — the sort of thing that costs an hour
and one line.

**Deciding what NOT to build.** Much of the advice students rely on lives on closed social
platforms, and my first instinct was to scrape one. I talked myself out of it, for a reason
that had nothing to do with difficulty: my demo would then depend on a live fight with
someone's anti-bot system, and if it broke on recording day I would have no submission. So
community input goes through a pluggable source interface instead — pasted text is the
primary implementation, and it mirrors what students actually do anyway.

**Making a two-minute wait not feel broken.** A full run makes several Bedrock calls and
takes a minute or two. A spinner would make it feel dead. So the web app streams each
pipeline stage as it executes, with what it found. The wait became the explanation of what
the product is doing — the multi-agent architecture stopped being invisible plumbing and
became a visible feature.

## What I learned

This was my first hackathon and my first time building an agent. I started the week not
knowing what "agent" meant beyond a buzzword, and the thing that actually clicked was
smaller and more concrete than I expected: an agent is a model, a set of tools, and a loop
that decides which tool to reach for. The `@tool` decorator turning a plain Python function
into something a model can call — with the docstring becoming the instructions — was the
moment it stopped feeling like magic.

The design lesson that mattered more than any API: **decide what belongs to the model and
what belongs to your code.** Everything I let the model do from memory was a place it could
be confidently wrong. Everything I pushed into a deterministic tool became something I
could point at. For a product whose entire value proposition is trustworthiness, that line
is the architecture.

I also learned that scoping down is a design decision and not a retreat. Narrowing from
"an assistant for French bureaucracy" to "the thing that checks whether what you heard is
still true" made the project sharper, not smaller.

## What's next

Hearsay is built on one pluggable ingredient: a corpus of official documents that carry
update dates. This release ships the **French** corpus — 5,552 documents from
Service-Public.gouv.fr — and is validated in **English and Chinese**. The pipeline itself
is country- and language-agnostic; the same five stages work anywhere an equivalent open
dataset exists. Germany, Spain and the Netherlands publish comparable data.

Beyond that:

- Deploying to **Amazon Bedrock AgentCore** for a hosted, shareable endpoint
- Additional community source connectors behind the existing interface
- Letting students submit corrections when the préfecture tells them something the official
  documents don't say — the gap between official text and counter practice is real, and
  nobody is mapping it

---

**Data attribution.** Official corpus: Service-Public.gouv.fr / DILA, published on
[data.gouv.fr](https://www.data.gouv.fr/datasets/service-public-fr-guide-vos-droits-et-demarches-particuliers/)
under Licence Ouverte 2.0 (Etalab). Hearsay reports what official documents say and when
they were last updated. It is not legal advice.
