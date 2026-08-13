---
name: msf-gate
description: Gate logic for MSF video generation — routes agents to the dumb or smart pipeline.
---
# MSF Gate

Decides which MSF pipeline an agent may use. The gate is enforced **inside the graph**,
not by a separate classifier module.

> There is no `msf.skills_bridge.gate_classifier`. Earlier versions of this skill
> referenced it; importing it raises `ModuleNotFoundError`. The real gate is
> `node_gate_check` in `msf/graph/video_graph.py`, driven by the `agent_level` you pass in.

## What the gate does and does NOT restrict

The gate exists to stop weak agents **writing untested React into the render path**.
It does **not** restrict which finished scenes they may use. Every registered preset
is available at every level.

| Level | Skill | May use presets | May write React |
|---|---|---|---|
| 1–2 | `msf-dumb-animate` | **all registered** (26) | no — never edit `remotion/src/` |
| 3–5 | `msf-smart-animate` | all + custom | yes, in `remotion/src/presets/custom/` |

## How the gate actually works

`node_gate_check` reads `agent_level` from the graph state:

- `agent_level <= 2` → **preset-only**. A name that is not a registered preset is
  rejected: the top-level `preset` falls back to `HeroKinetic`, and an unknown
  per-scene `preset` inside a `storyboard` is **dropped** so rotation picks a real
  varied preset instead of repeating one title card. The reason lands in `state["error"]`.
- `agent_level >= 3` → untouched. Custom presets in `remotion/src/presets/custom/` permitted.

`ALLOWED_PRESETS` is **derived from the registry at import time**, not hand-written:
`_read_registry_presets()` parses the modules that `remotion/src/registry/presets.ts`
imports. A new pack becomes available to level-1 agents the moment it is registered.

### Two bugs this replaced — do not reintroduce them

1. **A hand-written list of 11 names.** The library grew to 26 and the list was never
   updated, so 15 valid presets — `TgChat`, `DonutFill`, `PhoneMockup`, every media
   scene — were silently rewritten to `HeroKinetic` for level ≤ 2. The agents that
   depend on presets most were locked out of over half the library. If you ever
   hardcode this set again, it will rot the same way.
2. **The gate only checked the top-level `preset`.** Scenes inside a `storyboard`
   were never inspected, so a level-1 agent could name anything at all — including a
   nonexistent preset — and the gate reported success. Since storyboards are the
   recommended way to drive data presets, the hole covered the *common* path.

Verify both with:
```bash
cd /c/Users/ANEN/motion-studio-framework && python -c "
import sys; sys.path.insert(0,'.')
from msf.graph.video_graph import node_gate_check, ALLOWED_PRESETS
print(len(ALLOWED_PRESETS), 'presets allowed')
print('effects leaked?', any(n in ALLOWED_PRESETS for n in ('Bloom','FadeIn','CrossFade')))
print(node_gate_check({'agent_level':1,'preset':'TgChat'})['preset'])   # -> TgChat
print(node_gate_check({'agent_level':1,'preset':'Nope'})['preset'])     # -> HeroKinetic
"
```
Expected: `26 presets allowed`, `effects leaked? False`. The count must equal the
registry — check with `npx tsx -e "import {PRESET_NAMES} from './src/registry/presets'; console.log(PRESET_NAMES.length)"`
from `remotion/`. If Python and TypeScript disagree, the parser broke.

Note the parser reads **only** the modules `presets.ts` imports. Globbing the whole
registry directory also matches `effects_*.ts` and `transitions.ts`, which share the
entry shape, yielding 134 bogus "presets" (`Bloom`, `CrossFade`) — an agent naming one
of those as a scene gets an error card.

## Self-classification signals
| Signal | Level |
|---|---|
| "just want a video", "I don't code" | 1 |
| "make me a promo video" | 2 |
| "I know React, let me write components" | 3 |
| "use Remotion, I'll build the animation" | 4 |
| "I have a vision, give me full control" | 5 |

Report your real level. Inflating it to unlock custom code produces untested React in the
render path with no reviewer. **Deflating it costs you nothing** — all 26 presets work at
level 1, so pick level 1–2 unless you are genuinely going to author and verify a component.

## Usage
```python
import sys
sys.path.insert(0, r"C:\Users\ANEN\motion-studio-framework")
from msf.graph.video_graph import build_msf_graph

result = build_msf_graph().invoke({
    "text": "...",
    "preset": "HeroKinetic",
    "agent_level": 1,          # <- the gate input
    "output_path": r"C:\Users\ANEN\motion-studio-framework\output\out.mp4",
})
```

`create_video()` in `msf/orchestrators/remotion_runner.py` still exists as a thin
one-call wrapper, but it bypasses the gate and QA — prefer the graph.
