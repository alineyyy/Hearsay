# How to record the Hearsay demo video

You need no software you don't already have. No Keynote, no experience required.

---

## Before you start

- [ ] Server running: `python3 serve.py`
- [ ] Dry run both demos once — confirm the outputs look good **before** recording
- [ ] Browser cleaned up: hide the bookmarks bar (⇧⌘B), close other tabs, one window only
- [ ] Mac set to **Light appearance** (System Settings → Appearance)
- [ ] Turn on Do Not Disturb so no notification appears mid-take

---

## The slides (no Keynote needed)

The deck is an ordinary web page. Open it in the same browser you'll demo in:

```
open docs/slides.html
```

- **Press `f`** — full screen
- **→ / space / click** — next
- **←** — back
- Slide 2 holds its punchline until the next press. That pause is deliberate: let
  "That advice is generous. It's specific." sit, *then* reveal "And it's usually from
  last year."

Since the deck and the app are both browser tabs, you never show the desktop, the Dock,
or another application. The whole video stays inside one window.

### Three formats, same deck — pick one

| File | How to present | Good for |
| --- | --- | --- |
| `slides.html` | Open in browser, press `f`, arrow keys | **Recommended** — same window as the demo, nothing to learn |
| `Hearsay-deck.pptx` | Double-click → opens in **Keynote** | If you want to edit slides yourself |
| `Hearsay-deck.pdf` | Open in Preview, ⌘⇧F | Zero-risk fallback |

### If you use Keynote (first time)

1. Double-click `Hearsay-deck.pptx` — Keynote opens and converts it automatically.
   A warning about fonts or a "some changes were made" notice is normal; click through it.
2. Slides are listed down the left. Click one to edit it on the canvas.
3. To edit text, double-click the text and type. To move something, drag it.
4. **To present: ⌥⌘P** (or the ▶ Play button, top right). Arrow keys advance. **Esc** exits.
5. Speaker notes (I wrote some) are under **View ▸ Show Presenter Notes**.

One caveat when recording Keynote: presenting takes over the whole screen, so you'll be
recording the full screen rather than just a window — and switching to the browser for the
demo will briefly show your desktop. The HTML deck avoids that, which is why it's the
recommendation.

---

## Recording: **⌘⇧5**

Press ⌘⇧5 and a small toolbar appears.

1. Choose **Record Selected Portion** and drag a box around just the browser window
   (or **Record Entire Screen** if that's easier)
2. **Options ▸ Microphone ▸ MacBook Air Microphone** — this is how you get voiceover
3. **Options ▸ Save to ▸ Desktop**
4. Click **Record**
5. Stop with the ⏹ button in the menu bar, or ⌘⌃Esc

The file lands on your Desktop as a `.mov`.

### Record in three separate takes, not one

Far easier than getting five minutes right in a single pass:

| Take | Contents | Roughly |
| --- | --- | --- |
| **A** | Slides 1–3 (the problem, the name) | 0:00–1:00 |
| **B** | The live demo in the browser | 1:00–3:05 |
| **C** | Slides 4–6 (architecture, impact, close) | 3:05–4:30 |

If you fluff a line, just re-record that take. You stitch them together at the end.

---

## Editing

### The one edit that matters

Take B contains two waits of roughly a minute each while the pipeline runs.
**Speed those up 8×.** Keep the first three or four seconds at normal speed so the
viewer sees the stages lighting up, then accelerate through the rest.

Untouched, those two waits eat two of your five minutes and the video dies.

### Option 1 — iMovie (click-based)

1. Open iMovie → **Create New ▸ Movie**
2. Drag takes A, B, C into the timeline in order
3. To speed up a wait: click the clip, press **⌘B** to split at the start of the wait,
   **⌘B** again at the end, select the middle piece, then click the **speedometer icon**
   above the viewer → **Fast ▸ 8x**
4. **File ▸ Share ▸ File** → 1080p → Export

### Option 2 — ffmpeg (paste-based, faster)

```bash
brew install ffmpeg     # once

# Speed a section up 8×  (here: from 0:42 to 1:40 of take B)
ffmpeg -i takeB.mov -filter_complex \
  "[0:v]trim=0:42,setpts=PTS-STARTPTS[a];
   [0:v]trim=42:100,setpts=(PTS-STARTPTS)/8[b];
   [0:v]trim=100,setpts=PTS-STARTPTS[c];
   [a][b][c]concat=n=3:v=1[outv]" -map "[outv]" -an takeB_fast.mov

# Join the three takes
printf "file 'takeA.mov'\nfile 'takeB_fast.mov'\nfile 'takeC.mov'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy hearsay-demo.mov
```

---

## Before uploading

- [ ] Watch it once, start to finish, with a timer. **Under 5:00** — aim for 4:30
- [ ] If it's long, cut from the architecture section. **Never cut the demo**
- [ ] Check the audio is audible the whole way through
- [ ] Upload to YouTube, visibility **Public** (the rules require public)
- [ ] Paste the link into the Devpost submission

---

## If something goes wrong on the day

- **A demo run fails while recording** — stop, fix it, re-record only take B
- **A run is unusually slow** — fine, you're speeding it up anyway
- **You stumble over a line** — pause, breathe, say the line again. Cut the bad one later;
  it takes ten seconds in iMovie
