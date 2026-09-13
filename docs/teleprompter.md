# Read-aloud script

Just the words. Open this on your phone or a second window and read straight down.
`⏸` means stop talking for about two seconds — those pauses are doing work.
`[…]` are cues, not spoken.

---

### `[slide 1]`

Every international student in France has a senior who helped them.

⏸

Someone who had already been through it. Who told you which documents to bring, how early
to book the appointment, what the préfecture actually wants to see.

---

### `[slide 2]`

That advice is generous. It's specific.

⏸ `[press → to reveal the last line]`

And it's usually from last year.

⏸

French administrative rules change constantly. Forum posts don't. So the advice keeps
circulating long after it stopped being true — passed from one student to the next in
group chats and forums.

Get it wrong, and you don't just waste a trip to the préfecture. You can lose your legal
status.

---

### `[slide 3]`

This is Hearsay.

It takes the advice you were given and checks it, line by line, against official French
government sources — and tells you exactly what changed.

⏸ `[switch to the browser]`

---

### `[demo — click the "English post" sample, set the date to 2024-03-15, press Enter]`

This is the kind of advice that circulates every year. Someone who renewed their permit in
March 2024, passing on what worked.

`[the pipeline runs — sped up in the edit]`

It's turning my question into formal French administrative terms, searching five and a half
thousand official documents, then splitting the post into separate claims.

`[results appear — scroll slowly, stop on the €3,000 verdict]`

"You need three thousand euros in your account." Not covered. The official documents ask for
proof of sufficient means — they never name a figure. That number came from one préfecture,
one year, and it's been repeated ever since.

`[point at the date on any citation — "updated 2026-08-01"]`

And every verdict carries the date of the document it rests on. This one was last updated in
August 2026. The advice was written in March 2024.

`[scroll to the amber note at the bottom of the verdicts]`

Which is what it's telling me here. This post predates official changes, so even the parts
that look right are worth re-checking. Forum posts don't expire. The rules they describe do.

`[scroll to the green card with the tappable options]`

Then it does something I like. It doesn't guess which permit I hold — it asks. And it offers
the likely answers, so I can just tap one. Including "I'm not sure", because plenty of people
genuinely aren't.

⏸

I could tap one of these. But watch what happens if I answer in Chinese instead.

`[type: 我持有的是 titre de séjour étudiant,在里昂  — press Enter]`

`[the pipeline runs — sped up]`

`[the answer comes back in Chinese, continuing the same thread]`

It switches with me. It keeps the thread. And underneath, both turns searched the exact same
French government documents.

⏸

Because the language you ask in, and the language the law is written in, are two different
problems.

⏸ `[switch back to the slides]`

---

### `[slide 4 — architecture]`

Under the hood: five agents built on the AWS Strands SDK, running on Amazon Bedrock.

A planner turns any language into formal French search terms. Retrieval is plain keyword
search over the official corpus — no model involved. A claim extractor splits the advice
up. A verifier rules on each claim, calling tools to check the dates. A writer turns it
into a checklist.

The green boxes are agents. They make judgements. The amber box is deterministic code. It
supplies facts.

That split is the whole design. Every conclusion traces back to a document ID and a URL,
not to the model's memory.

⏸

And when the official documents are silent, Hearsay says so — instead of guessing.

---

### `[slide 5 — 445,000]`

There were nearly four hundred and forty-five thousand international students in France
last year. Almost all of them get through this on hearsay.

⏸

Hearsay doesn't replace that network. The senior who helped you wasn't wrong, and wasn't
careless. They just didn't know the rule had changed.

⏸

This doesn't tell you to stop asking your friends.

⏸

It tells you which parts of what they said are still true.

⏸

---

### `[slide 6 — close]`

Hearsay is open source, MIT licensed, and built on French government open data.

Thanks for watching.

---

## Two notes before you read this aloud

**Read it out loud once before recording.** Anything that trips your tongue, change it —
it's your script. Contractions ("it's", "doesn't") are already in there because they sound
spoken rather than written.

**The pauses matter more than the pace.** Three lines carry this whole video:
*"And it's usually from last year."* · *"It's the point."* · *"…which parts of what they
said are still true."* Land each one, then stop for a beat. Rushing them is the only way
to lose a video that is otherwise good.
