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

## 3 · Demo A — checking what you heard — 1:00–2:15

🎞 Switch to the browser. Paste the sample post. Post date 2024-03-15. Hit send.

🎙
> Here's a real post of the kind that circulates every year — renewal advice from
> someone who went through it in March 2024.
>
> I paste it in, tell Hearsay when it was written, and it goes to work.

🎞 **Pipeline stages light up. SPEED THIS UP 8× IN EDITING.** Keep 3–4 seconds of it
at normal speed first so viewers see the stages, then accelerate through the wait.

🎙 *(over the sped-up section)*
> It translates the question into formal French administrative terms — because the
> official corpus doesn't use the words students use. It searches five and a half
> thousand official documents. Then it breaks the post into individual claims and
> rules on each one.

🎞 Results appear. **Scroll slowly.** Stop on the €3,000 verdict. Let it sit on screen.

🎙
> And here's what it found.
>
> "You need to show three thousand euros in your account." Not covered. The official
> documents require proof of sufficient means — they never name a figure. That number
> came from one préfecture, one year, and it has been repeated ever since.

🎞 Stop on an OUTDATED verdict. Point at the date.

🎙
> This one was true when it was written — and the rules changed afterwards. Hearsay
> knows because every official document carries the date it was last updated.
>
> Every verdict links to the source, with that date.

*(~150 words total across this section.)*

---

## 4 · Demo B — it asks you back — 2:15–3:00

🎞 New question, plain: `My student permit expires in November. How do I renew it?`
Speed up the wait again.

🎙
> It also works the other way round. Just ask.

🎞 Answer appears — scroll to the green "Hearsay needs to know" card.

🎙
> But notice what it does here. It doesn't hand me a generic procedure — it asks me
> which permit I actually hold. Because in France, the honest answer is "it depends",
> and a tool that pretends otherwise is how bad advice gets made in the first place.

🎞 Click "Answer this", type the permit type and city, send. Speed up the wait.

🎙
> I tell it. And it comes back with the version that applies to me.

🎞 *(Optional, 8 seconds)* Ask the same thing in Chinese; show the Chinese answer.

🎙
> Ask in any language — the answer comes back in that language, while the search
> always runs through French. For this audience, that's not a feature. It's the point.

*(~110 words.)*

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
