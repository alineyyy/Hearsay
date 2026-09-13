# Hearsay — demo video script

Target length **4:30** (hard limit 5:00 — leave margin).
Narration is ~150 words/minute. Word counts below are sized for the time given.

**Legend:** 🎞 = what is on screen · 🎙 = what you say

---

## 1 · The problem — 0:00–0:45

🎞 Slide 1, then Slide 2. No app yet — earn the attention first.

🎙
> Every international student in France has a senior who helped them.
>
> Someone who had already been through it. Who told you which documents to bring,
> how early to book the appointment, what the préfecture actually wants to see.
>
> That advice is generous. It's specific.
>
> And it's usually from last year.
>
> French administrative rules change constantly. Forum posts don't. So the advice
> keeps circulating long after it stopped being true — passed from one student to
> the next in group chats and forums.
>
> Get it wrong, and you don't just waste a trip to the préfecture. You can lose
> your legal status.

*(~110 words. Slow down on "And it's usually from last year" — that line is the hook.)*

---

## 2 · What Hearsay is — 0:45–1:00

🎞 Slide 3: the name and the one-liner.

🎙
> This is Hearsay.
>
> It takes the advice you were given and checks it, line by line, against official
> French government sources — and tells you exactly what changed.

*(~35 words. Then stop talking for a beat before the demo starts.)*

---

## 3 · Demo — one conversation, everything in it — 1:00–3:00

**Two turns, not two demos.** Three turns means three waits, and three waits will not fit in
two minutes even sped up. One continuous session shows all of it: multilingual input, the
per-claim verdicts, the tappable options, the language switch, and the kept context.

**English first, then Chinese.** The judges can read the verdicts in turn one — that is the
substance. The switch to Chinese in turn two is the thing they only need to *see*, not read.

🎞 Click the **English post** sample, set the date to `2024-03-15`, press Enter.

🎙
> This is the kind of advice that circulates every year. Someone who renewed their permit in
> March 2024, passing on what worked.

🎞 **Pipeline runs. SPEED UP 8× IN EDITING**, keeping the first 3–4 seconds at normal speed
so the stages are visible.

🎙 *(over the sped-up section)*
> It's turning my question into formal French administrative terms, searching five and a half
> thousand official documents, then splitting the post into separate claims.

🎞 Results appear. Scroll slowly. **Stop on the €3,000 verdict and let it sit.**

🎙
> "You need three thousand euros in your account." Not covered. The official documents ask for
> proof of sufficient means — they never name a figure. That number came from one préfecture,
> one year, and it's been repeated ever since.

🎞 Point at the date on any citation — every verdict shows one ("updated 2026-08-01").
Then scroll to the amber **"Worth knowing"** note under the verdicts.

🎙
> And every verdict carries the date of the document it rests on. This one was last updated
> in August 2026. The advice was written in March 2024.
>
> Which is what it's telling me here. This post predates official changes, so even the parts
> that look right are worth re-checking. Forum posts don't expire. The rules they describe do.

> **Note on what actually appears.** An earlier draft of this script said "stop on an OUTDATED
> verdict" — but on a real run the verdicts came back as *not covered*, *partly true* and
> *confirmed*, with no OUTDATED among them. Do not script around a badge that may not appear.
> The recency argument is carried by two things that are always on screen: the update date on
> every citation, and the amber note. That the tool does not stamp "outdated" on everything is
> a point in its favour, not a gap — and the €3,000 verdict is the stronger finding anyway: a
> number everyone repeats, with no official basis at all.

🎞 Scroll to the green "Hearsay needs to know" card with its option chips.

🎙
> Then it does something I like. It doesn't guess which permit I hold — it asks. And it offers
> the likely answers, so I can just tap one. Including "I'm not sure", because plenty of people
> genuinely aren't.

🎞 Pause. Then, instead of tapping, type in Chinese:
`我持有的是 titre de séjour étudiant,在里昂`

🎙
> I could tap one of these. But watch what happens if I answer in Chinese instead.

🎞 Pipeline runs (speed up). The answer returns **in Chinese**, continuing the same thread.

🎙
> It switches with me. It keeps the thread. And underneath, both turns searched the exact same
> French government documents.
>
> Because the language you ask in, and the language the law is written in, are two different
> problems.

*(~290 words ≈ 2:00 at normal pace. The Chinese answer is the strongest single moment in the
video: the judges cannot read it — and not being able to read it is exactly the experience
this product exists to fix.)*

---

## 5 · How it works — 3:00–3:40

🎞 Slide 4: the architecture diagram, full screen.

🎙
> Under the hood: five agents built on the AWS Strands SDK, running on Amazon Bedrock.
>
> A planner turns any language into formal French search terms. Retrieval is plain
> BM25 over the official corpus — no model involved. A claim extractor splits the
> advice up. A verifier rules on each claim, calling tools to check dates. A writer
> turns it into a checklist.
>
> The green boxes are agents — they make judgements. The amber box is deterministic
> code — it supplies facts.
>
> That split is the whole design. Every conclusion traces back to a document ID and a
> URL, not to the model's memory. And when the official documents are silent, Hearsay
> says so, instead of guessing.

*(~120 words. The last sentence matters — say it deliberately.)*

---

## 6 · Who it's for, why it matters — 3:40–4:15

🎞 Slide 5: the number and the community framing.

🎙
> There were nearly four hundred and forty-five thousand international students in
> France last year. Almost all of them get through this on hearsay.
>
> Hearsay doesn't replace that network. The senior who helped you wasn't wrong, and
> wasn't careless — they just didn't know the rule had changed.
>
> This doesn't tell you to stop asking your friends.
>
> It tells you which parts of what they said are still true.

*(~85 words. That final line is the close of the pitch — pause before it, and after.)*

---

## 7 · Close — 4:15–4:30

🎞 Slide 6: repo link, licence, data attribution.

🎙
> Hearsay is open source, MIT licensed, and built on French government open data.
>
> Thanks for watching.

---

## Production checklist

- [ ] Full dry run of both demos first — confirm the outputs are good before recording
- [ ] Browser cleaned up: no bookmarks bar, no other tabs, window sized so text is legible
- [ ] **Speed up every wait 8×** — this is the single biggest thing between a good and a bad cut
- [ ] Watch it back once with a timer. If it's over 4:45, cut from section 5, not from the demo
- [ ] Upload to YouTube as **Public**
