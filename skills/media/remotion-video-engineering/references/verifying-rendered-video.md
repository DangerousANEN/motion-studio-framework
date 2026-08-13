# Verifying a rendered video is actually correct

Companion to Rule 1b (a successful render is not a correct render), Rule 1f
(match the instrument to the defect) and Rule 1i (sample the delivered artifact).

Every technique here is written from a measured case, with the numbers that
exposed the problem.

---

## 1. Verify the delivered artifact, not a fresh render

`npx remotion still` re-renders from source. It proves the *code* can produce a
frame; it does not prove the mp4 you are about to hand over contains it. Encoding,
audio muxing and the transition timeline are all downstream of `still`.

Extract frames out of the encoded file instead:

```bash
ffmpeg -y -v error -i out.mp4 -vf "select=eq(n\,140)" -vsync 0 -frames:v 1 f140.png
```

`-vsync 0` matters. Without it ffmpeg re-times the single output frame and you can
get frame 0 back regardless of the `select` expression.

Then hash sampled frames to prove motion exists *in the encoded file*:

```bash
sha1sum f030.png f090.png f140.png | awk '{print substr($1,1,12), $2}'
```

Three distinct hashes from one orbiting scene is the cheapest possible proof that
the camera moved through the encode. Identical hashes caught a frozen 360° orbit
that `tsc`, exit code, luminance and a content probe all passed.

**Windows/MSYS: give `ffprobe` a native path.** In git-bash, `ls` and `ffmpeg`
both accept `/c/Users/...`, but `ffprobe` returned
`No such file or directory` for a file `ls` had just listed at 4,075,784 bytes —
which reads exactly like a missing or corrupt render. Quote the native form
instead:

```bash
ffprobe -v error -show_entries format=duration,size \
        -show_entries stream=width,height,r_frame_rate,codec_name \
        -of default=noprint_wrappers=1 'C:\Users\me\out\video.mp4'
```

Before concluding an artifact is missing or broken, confirm the path style the
specific tool wants — the file existing under one form and not another is a path
translation issue, not a render failure.

---

## 2. Compute scene spans BEFORE choosing sample frames

`TransitionSeries` **overlaps** neighbours: a transition of N frames makes the
outgoing scene's last N frames shared with the incoming one. Scene starts are
therefore not cumulative durations.

```python
d = [150, 120, 120]      # scene durations
t = [18, 18]             # transition before scene 2, before scene 3

start, spans = 0, []
for i, dur in enumerate(d):
    if i > 0:
        start -= t[i - 1]          # overlap pulls the next scene earlier
    spans.append((i + 1, start, start + dur))
    start += dur

total = sum(d) - sum(t)            # must equal ffprobe nb_frames
```

Yields `scene 1: 0..150`, `scene 2: 132..252`, `scene 3: 234..354`, total 354.

**Frame 140 belongs to scenes 1 AND 2.** Sampling it as "the end of scene 1"
produced a scary reading — centre-band ink fell to 18.1 % against 68–80 % on
earlier orbit frames, and vision reported two scenes stacked: a helmet with
another scene's heading and donut arcs drawn over it. Nothing was broken. That is
what a crossfade looks like 8 frames in.

Rules that follow:

- Never assert per-scene content from a frame inside a transition window. Pick
  samples from `[start + N, end - N]`.
- An anomalous ink/colour reading inside an overlap is the blend, not a defect.
  Adjudicate with the span arithmetic before you start "fixing" anything.
- `total = sum(durations) - sum(transitions)` is a free oracle. Compare it to
  `ffprobe nb_frames` on every render; a mismatch means the timeline planner and
  the composition disagree.

---

## 3. Three instruments, in order

Each answers a question the others cannot. Running them in the wrong order wastes
a render cycle or invents a bug.

| Instrument | Answers | Blind to |
|---|---|---|
| Container facts (`ffprobe`) | right size/fps/frame count | anything about pixels |
| Pixel probe (ink %, distinct colours) | is a subject present, did frames change | *what* the subject is |
| Vision | what is actually on screen, legibility, overflow | blending, opacity, exact geometry |
| Semantic pass vs the spec (§10) | is the *right* thing on screen | nothing — but it needs a human-readable read of every scene |

The fourth row is the one that gets skipped, and it is the only one that catches
wrong words, duplicate colours and invented units. See §10.

The productive sequence when a number looks wrong:

1. Pixel probe **flags** the anomaly (18.1 % where 70 % was expected).
2. Vision **explains** what occupies the frame (two scenes composited).
3. Timeline arithmetic **adjudicates** whether that is legal (frame 140 ∈ overlap → legal).

Skipping step 3 is how a correct render gets "fixed" into a broken one.

---

## 4. Probe hygiene: validate the probe before trusting the result

A probe that lies is worse than no probe. Two failure modes observed:

**Output rows exceeding sampled frames.** A sampler using
`select=not(mod(n\,60))` on a 354-frame video returns 6 frames, but the reading
loop printed **359 rows** labelled `t=0s … t=358s`. The labels were fabricated by
enumerating a byte buffer, not frames. If row count ≠ expected sample count, the
probe is decoding something other than what you think — discard the run.

**Decorative layers satisfying the assertion.** An early "OBJECT PRESENT" verdict
on a 3D scene was entirely a `gridHelper` floor; the model was absent. Turn
decoration off before asserting a subject exists, and prefer distinct-colour
count over coverage — a shaded PBR mesh yields hundreds of colours, flat UI a
handful.

Cheap self-checks worth wiring into any probe: expected-vs-actual sample count,
a known-good and known-bad frame as fixtures, and an explicit background sample
so "ink" is measured against the real backdrop rather than an assumed black.

---

## 5. Treat delegated verification as an unverified claim

Four subagents refactoring presets each reported success on the strength of a
`YMAX` reading. `YMAX` only proves a frame is not black — it says nothing about
the safe-area compliance the refactor existed to achieve. A pixel bounds probe
was needed to actually confirm it (5/5 inside the safe box, 6 px tolerance).

When delegating render work, specify the *measurement* that constitutes proof,
not just the goal, and re-run it yourself on the returned artifact.

---

## 6. Keep generated binaries out of git

A model cache (`assets/models/`, `remotion/public/models/`) and scratch debug
frames land in commits easily — 7.5 MB of GLB in one case, plus a stray PNG. The
provider re-downloads and revalidates on demand, so ignore both paths and confirm
the preset still renders **after** untracking, proving the fetch path works rather
than silently depending on a committed blob.

---

## 7. Audio cue times must come from the transition planner too

§3 of `transitions-and-motion-layer.md` covers the composition *duration*. The
same overlap bites a second consumer that is easy to forget: the **SFX / music
cue generator**. A generator that walks the scene list accumulating
`durationInFrames` places every cue after the first transition too late, and
produces a track longer than the picture.

Measured on an 8-scene demo with 7 transitions totalling 154 overlap frames:

| | before | after |
|---|---|---|
| audio track | 22.50 s | 19.93 s |
| video (`ffprobe`) | 19.99 s | 19.99 s |
| last hit offset | **+2.57 s late** | on the cut |

Fix is to import the same `getTransitionPlan` the composition uses and subtract
the overlap when advancing the cursor — never re-derive scene starts in the audio
layer.

Two free oracles, both one command:

- `ffprobe` the **audio** file and the **video** file and compare durations.
  A gap larger than a frame means the two layers disagree about the timeline.
- Assert every cue frame lands inside its scene's span *outside* the overlap
  windows (§2). A cue sitting inside a crossfade fires against the wrong picture
  even when the totals happen to match.

After the fix, re-measure the mix rather than assuming the edit was neutral:
`−14.00 LUFS`, peak `−0.69 dBFS`, no clipping.

---

## 8. Safe-area compliance must be re-checked on *effect-applied* frames

A preset that passes a safe-area probe in isolation can fail in the timeline,
because camera effects move content after layout. A `DollyIn` push scaled a hero
subtitle from inside the readable band up into the reserved top strip:
`3833 px` of solid ink at `x 481..599, y 231..273` against a 280 px top limit.
Nothing in the preset changed; the effect did it.

So: run the bounds probe on frames sampled from the **assembled** render (§1),
not on stills of bare presets, and include frames from inside camera-effect
windows.

### Localise a spill by enumerating the region, never by re-measuring globally

When a bounds probe reports spill, the instinct to re-measure the whole frame is
a trap. A global bbox says only *where the outermost ink is*; soft glow from
`Bokeh` / `Vignette` / a zoom push sits at the very edges and dominates that
answer, so the global read comes back "content is comfortably inside, it must
just be decoration" — and a real defect gets dismissed. This produced two
consecutive wrong conclusions in one session before the region read settled it.

Measure **inside the offending strip only**, and print coordinates plus
intensity:

```python
d = np.abs(im - bg).sum(axis=2)           # bg sampled from a corner
solid = d > 320                            # panels/text >320; glow measured ~105
region = solid[:top_limit - tolerance]     # the strip that was flagged
ys, xs = np.nonzero(region)
print(region.sum(), f"y {ys.min()}..{ys.max()} x {xs.min()}..{xs.max()}",
      int(np.median(d[:top_limit - tolerance][region])))
```

Intensity separates the two causes cleanly: decoration measured `105` max at the
frame edge, real content `350`–`438`. The coordinates then name the element —
`x 62..73` repeating across two unrelated scenes was one shared 8 px accent bar
drawn at `left: 64` against an 80 px side margin, not two layout bugs.

Worth encoding the `solid` threshold and a comment in the probe itself, so the
next session does not relitigate whether glow counts as spill.

---

## 9. A tool error is not evidence about the artifact

Calling a tool that does not exist returns a refusal. That refusal says nothing
about the repo, the render, or any earlier verified result — but it reads like an
access failure, and the pull to escalate from "this call failed" to "my access is
broken, so my previous report may have been invented" is strong. Acting on that
pull meant retracting a report that was in fact backed by a commit in `git log`
and two artifacts on disk, then re-verifying all of it from scratch.

Before doubting the environment or your own prior findings:

1. Re-read the available tool list and check the **name**. Wrong-name errors look
   identical to permission errors.
2. Re-run the specific check that produced the earlier claim. A commit SHA, an
   `ffprobe` line, or a byte count either reproduces or it does not.
3. Only then report a blocker — and scope it to the one capability that actually
   failed, not to your ability to work.

Verified prior work stays verified until a probe contradicts it. Withdrawing it
on the strength of an unrelated error costs a full re-verification cycle and
makes every future report less credible.

---

## 10. The defect class no numeric probe can see

Companion to Rule 1j. A demo reel passed Zod, `tsc`, the red-frame probe,
safe-area bounds, `intensity=0` byte proofs, span arithmetic and 159 frames of
numeric sampling. The user watched it once and found five defects. All five were
*semantic* — the pixels were present, animated, correctly sized and inside the
safe box, and still said the wrong thing.

| On screen | Cause | Class |
|---|---|---|
| Chat header names the contact "Telegram" | `{title \|\| 'Аня'}` given `title: "Telegram"` | field doing double duty |
| Two donut segments identical in colour | `accentColor` default `BRAND.neon` === `BRAND.accentGreen` | palette alias collision |
| Plain count rendered "108%" | `statSuffix = '%'` default prop, spec sent none | default invents units |
| Subject vibrates | `mulberry32(seed + frame * 7)` reseeds per frame | RNG misuse as motion |
| Segment gaps wider than requested | `gapAngle` per segment **plus** round-cap overhang | compounding geometry |

### Checklist to run against every scene before delivering

Read the spec and the frame side by side and ask:

1. Does each visible string mean what the spec intended, or merely render?
2. Do any two elements that must be distinguishable share a resolved hex?
3. Is any unit/suffix/prefix/currency on screen that the spec never supplied?
4. Does anything vibrate frame-to-frame instead of moving?
5. Do labelled numbers agree with the geometry they annotate?

State plainly when vision tooling is unavailable rather than offering numeric
probes as equivalent coverage. And when a user-reported defect has no proven
cause yet, ask what they saw — one defect in that session ("the card is broken")
was correctly left open instead of pattern-matched to a plausible cause.

### Recipe A — reference-free structural metric

Corner-pixel background sampling (`bg = im[4,4]`) breaks during wipes and
transitions, because the corner itself changes. When a collapse reading might be
an artifact of the reference, re-measure with no reference at all:

```python
L = 0.2126*im[...,0] + 0.7152*im[...,1] + 0.0722*im[...,2]
edge = (np.abs(np.diff(L, axis=1)).mean() + np.abs(np.diff(L, axis=0)).mean()) / 2
edge_px_pct = (np.abs(np.diff(L, axis=1)) > 6).mean() * 100
```

`edge` and `edge_px_pct` measure *structure*, not deviation from an assumed
backdrop. Agreement between this and the bg-relative read means the anomaly is
real; disagreement means the reference moved.

### Recipe B — quantify jitter with integer-shift search

Distinguishes organic drift from per-frame noise. Grayscale consecutive frames,
find the `(dy,dx)` minimising SAD over a search radius:

```python
def best_shift(a, b, r=14):
    h, w = a.shape
    ac = a[r:h-r, r:w-r]
    best, bv = (0, 0), 1e18
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            v = np.abs(ac - b[r+dy:h-r+dy, r+dx:w-r+dx]).mean()
            if v < bv: bv, best = v, (dy, dx)
    return best
```

The diagnostic is not magnitude but **direction reversals**. Measured on the
jittering scene: mean 0.62 px, max 1.41 px, horizontal sign flipping on 5 of 39
frame pairs with values alternating almost every frame. Smooth camera motion holds
its sign for many consecutive frames; white noise does not. Note this is O(r²) per
pair — 41 frames at r=14 took ~4.5 min, so window it tightly.

### Recipe C — angular run-length sampling of a ring

Proves segment colours and arc extents on a donut/pie without reading the code:

```python
sat  = (px.max(axis=1) - px.min(axis=1)).reshape(h, w)
mask = sat > 60                       # saturated = ink, not backdrop
ys, xs = np.nonzero(mask); cy, cx = int(ys.mean()), int(xs.mean())
# sweep radii, keep the one covering the most degrees, then walk 0..359
```

Collapsing the walk into run-lengths gave `#00F780 220°`, `#00CDF2 80°`,
`#00F780 45°` — two runs of the *same hex* is the duplicate-colour bug stated as
a measurement. The same output verifies gap angles and per-segment share.

### Recipe D — element-vs-element collision inside a container

Safe-area probes check the *frame* edge. They are blind to two elements
overlapping each other inside a card, and blind to text clipped by a container's
`overflow: hidden` — the clip destroys the evidence a bounds check would need.
Both defect classes shipped through the full numeric gate in one session and were
caught by looking at the frame.

Isolate the panel first (any centred container lighter than its page backdrop):

```python
bg   = a[4, 4]
card = a.sum(axis=2) > bg.sum() + 18
rows = card.sum(axis=1)                    # longest run of wide rows == the card
# take the longest run of y where rows[y] > w * 0.35  ->  y0, y1
cols = card[y0:y1 + 1].sum(axis=0)
xs   = np.flatnonzero(cols > (y1 - y0) * 0.5)     # x0, x1
```

Then per declared row: slice its band, threshold ink (`luma > 140`), take the ink
bbox, and assert horizontal clearance:

```python
assert cardRight - inkRight > cardW * 0.05   # 0px margin == silently amputated
```

Measured: a masked card number ended exactly at the card's right edge (0 px
margin) with the last four digits gone; after the fix, 102 px of clearance
(12.9 % of card width). Run this for **every** text row, not just the reported
one — and re-run after each fix, because fixing a collision reflows neighbours
and exposes the next one.

Aspect checks belong here too, and cut both ways: the same vision pass that found
the collisions also claimed the card was "squeezed horizontally". Measured aspect
was 1.612 against ISO 7810 ID-1's 1.586 — a 1.6 % deviation, not a defect.
Reproduce every vision finding as a number before acting on it.

### Frame-accurate extraction

`-ss` before `-i` seeks to the nearest keyframe and will silently hand back a
different frame, which fakes both anomalies and clean results. For exact frames
use a `select` filter with `-vsync 0` (§1), or a range:

```bash
ffmpeg -y -v error -i out.mp4 -vf "select=between(n\,458\,478)" \
       -vsync 0 -frame_pts 1 n%05d.png
```

`-frame_pts 1` names each file by its true frame number, so a mislabelled sample
cannot go unnoticed.

---

## 11. Mid-scene sampling defames progressive-reveal presets

§2 says avoid transition windows. There is a second bad sample point that is
easier to hit, because pipeline QA usually *defaults* to it: the scene
**midpoint**.

A word-by-word reveal preset (`TypewriterSub`) is designed so unspoken words sit
in a dim pending colour and brighten as the voiceover reaches them. At the
midpoint that is exactly half-lit — which is correct, and which vision reports as
a defect. Measured on an 8-scene short whose graph QA sampled `scene_NN_mid.png`:

| | mid-scene frames | frames ~0.3–0.5 s before scene end |
|---|---|---|
| vision verdict | "opacity dropped to 10–15 %, words merge into the background" on 2/8 scenes | "весь текст яркий", 0 dim words |
| suggested action | recolour the text to white | none needed |

The mid-frame verdict was confident and specific — it even proposed a cause
("lost alpha channel / slipped opacity") and a fix. Acting on it would have
deleted the reveal animation.

Recipe — re-sample near the end of the suspect scenes before believing the
verdict. Compute the scene's end time from the spec, back off a few tenths, and
extract by timestamp:

```bash
for t in 9.20 22.30 34.90; do
  ffmpeg -hide_banner -loglevel error -ss $t -i out.mp4 \
         -frames:v 1 -update 1 "end_${t}.png" -y
done
```

(`-ss` before `-i` is keyframe-snapping per §10; acceptable here because the
question is "is the text bright by now", not "which exact frame is this". When
the exact frame matters, use the `select` + `-vsync 0` form instead.)

Then contact-strip them into one image so a single vision call covers all the
suspects:

```bash
ffmpeg -hide_banner -loglevel error -y -i a.png -i b.png -i c.png \
  -filter_complex "[0:v]scale=340:-1[a];[1:v]scale=340:-1[b];\
[2:v]scale=340:-1[c];[a][b][c]hstack=inputs=3" \
  -frames:v 1 -update 1 strip.png
```

**`-frames:v 1 -update 1` is mandatory when writing a single PNG.** Without it
ffmpeg treats the output as an image sequence, warns `Use a pattern such as %03d`,
and writes nothing — the subsequent `ls` fails and it reads like a filter error.

Generalised rule: **match the sample point to what the preset does.**

| Preset behaviour | Sample at | Why |
|---|---|---|
| progressive reveal (typewriter, counters, wipes) | near scene end | mid-animation is *meant* to be incomplete |
| entrance / exit effect | inside the active window | end state is the bare preset, proves nothing |
| **beat-divided (countdown, quiz reveal, karaoke, steps)** | **once per beat, esp. the last** | each beat holds *different content*; one sample misses the payoff entirely |
| steady card / hero | anywhere outside overlaps (§2) | no time dependence |

Ask "what should this look like at this instant" before ruling on a frame. A
verdict of "element missing / text too dim" on a timed reveal needs a second
sample near the scene end before it counts as a defect.

### 11a. Beat-divided presets: one sample per scene is structurally blind

The reveal case above yields a *wrong verdict* from a mid sample. The beat case is
worse — it yields **no verdict at all**, because the content you need to check was
never rendered into any sampled frame.

`CountdownHero(from: 3)` splits 102 frames into 4 equal beats: `3`, `2`, `1`, then
the hero word. The house habit of sampling 72 % into each scene lands on frame 73 —
inside beat 2, showing the digit `1`. The final word occupies the last 25 % of the
scene and was never sampled. A truncated hook (`ОГНАЛ` instead of `ДОГНАЛИ`, the
word overflowing the 1080 px frame) therefore passed a 15-frame still sweep **and**
a vision review of every scene, surfacing only after all three scripts were
rendered to mp4 and frames near the cuts were extracted.

Derive frames from the preset's own time-division field rather than the scene:

```python
total_beats = int(scene.get("from", 3)) + 1
beat = scene["durationInFrames"] / total_beats
frames = [int(beat * (i + 0.72)) for i in range(total_beats)]
```

Fields that imply beats: `from`, `revealAtProgress`, `sendAtProgress`, per-line
`startAt`, `steps[]`. When you don't want to model the preset, sample **three**
frames per scene at 30 / 72 / 92 % — the 92 % sample catches final-beat and
end-state content for one extra `still` per scene.

Full case, plus the text-overflow defect it was hiding, in
`references/text-fitting-and-beat-sampling.md`.

