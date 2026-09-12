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

### `[demo — paste the sample post]`

Here's a real post of the kind that circulates every year. Renewal advice from someone who
went through it in March 2024.

I paste it in, tell Hearsay when it was written, and it goes to work.

`[while the pipeline runs — this is sped up in the edit]`

It translates the question into formal French administrative terms, because the official
corpus doesn't use the words students use. It searches five and a half thousand official
documents. Then it breaks the post into individual claims, and rules on each one.

`[results appear — scroll slowly, stop on the €3,000 verdict]`

And here's what it found.

"You need to show three thousand euros in your account." Not covered. The official
documents require proof of sufficient means — they never name a figure. That number came
from one préfecture, one year, and it has been repeated ever since.

`[stop on an OUTDATED verdict, point at the date]`

This one was true when it was written, and the rules changed afterwards. Hearsay knows
because every official document carries the date it was last updated.

Every verdict links to the source, with that date.

---

### `[demo — ask a question in Chinese]`

It also works the other way round — you can just ask. And you can ask in your own language.

`[answer appears in Chinese — scroll to the green card with the tappable options]`

Notice what it does here. It doesn't hand me a generic procedure. It asks which permit I
actually hold, and offers the likely answers so I can tap one.

Because in France the honest answer is "it depends" — and a tool that pretends otherwise
is how bad advice gets made in the first place.

`[now type the reply in English]`

And here's the part I like most. I'll answer it — but in English this time.

`[answer comes back in English]`

It switches with me. It keeps the thread. And underneath, both turns searched the exact
same French government documents.

Because the language you ask in, and the language the law is written in, are two different
problems. Hearsay keeps them separate.

⏸

For this audience, that isn't a feature. It's the point.

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
