# 1 · Getting started

About ten minutes from a cold install to a scored library open on screen.

---

## Requirements

| | |
|---|---|
| **Python** | 3.10 or newer |
| **Playwright + Chromium** | `pip install playwright && playwright install chromium` |
| **Claude Code** | for the slash commands. The Python CLI works without it |
| **Node** | not required |
| **Network** | not required after install |

Chromium is the only heavy dependency and it earns its place: the density, overflow and
collision checks are real geometry read out of a real layout engine. There is no way to
compute ink coverage from source text.

## Install

Point Claude Code at the folder containing this plugin:

```
/plugin marketplace add /path/to/the/folder
/plugin install design-system-carousel-creator
```

The plugin is self-contained — commands, agents, skills, schemas, scripts, the CSS kernel,
the browser runtime and the canvas host all travel together. Nothing is fetched at runtime.

## Check the toolchain

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py doctor
```

```
toolchain
  python            3.12.1
  playwright        installed
  chromium          launchable
  kernel.css        found

READY
```

If it says `NOT READY`, fix what it names before going further. The most common miss is
`playwright install chromium` — installing the Python package does not download the browser.

---

## Your first library

### The one-command version

```
/design-system-carousel-creator:run DESIGN.md whitepaper.pdf
```

This runs every stage in order and finishes by opening the library on a canvas. It does
**not** stop to ask you about card count, artboard size, tone, taxonomy or theme handling —
every one of those has a defensible default in [`schema/defaults.json`](../schema/defaults.json),
and the choices are reported at the end so you can redirect anything you disagree with.

Three situations genuinely stop it: your sources contradict each other on a fact that would
appear on a card, the brand supplies no colour information at all, or the content is plainly
for a different medium.

### The stage-by-stage version

Better the first time, because you see what each stage produces.

```bash
# 1 · Create the project. Do this before anything else writes a file.
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py new "Acme Templates" \
  --system DESIGN.md --source whitepaper.pdf
cd "Acme Templates"
```

Then, in Claude Code:

```
/design-system-carousel-creator:distill    → build/design-system.json
/design-system-carousel-creator:brief      → build/content-brief.json
/design-system-carousel-creator:plan       → build/layout-plan.json
/design-system-carousel-creator:build      → dist/Acme Templates.dc.html
/design-system-carousel-creator:audit      → audit/scorecard.json
/design-system-carousel-creator:preview    → opens the canvas
```

At any point:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py info
```

prints what is done, what is next, and the audit history.

---

## What you get

```
Acme Templates/
├── project.json     identity, wiring, constraints, pipeline state
├── README.md        generated — how to rebuild, how to preview
├── inputs/          FROZEN copies of DESIGN.md and whitepaper.pdf
├── build/           design-system.json · content-brief.json · layout-plan.json · build.py
├── dist/            THE DELIVERABLE — self-contained, servable, zippable
│   ├── Acme Templates.dc.html
│   ├── support.js · image-slot.js
│   ├── canvas.html
│   └── .image-slots.state.json
├── audit/           scorecard · lint · measure · uniq · report.html · history.jsonl
├── shots/           per-card PNGs
└── RELEASE.md       written at ship time
```

**`dist/` is the whole deliverable.** Nothing in it reaches outside itself. Zip that folder
and hand it over.

---

## Reading the score

```
SCORE  94.2/100   gate: PASS

  integrity     19.4 / 20  #######################
  discipline    14.1 / 15  ######################
  density       17.9 / 20  #####################
  distinction   15.0 / 15  ########################
  veracity       9.6 / 10  #######################
  craft          -- / 20

  unscored: craft (scored out of 80)
```

Read it in this order:

1. **The gate** — PASS or FAIL, and why.
2. **P0 defects** — these fail the gate outright regardless of the total.
3. **The weakest card** — more important than the average. A library averaging 84 with one
   card at 48 is not an 84 library; a reader hits that card and the set loses credibility.
4. **Library statistics** — where systemic problems live. No P0s, a decent average and a gap
   CV of 0.55 means a rhythm problem no single card would reveal.

That `craft -- / 20` is not a rounding detail. Craft is the judged dimension and it needs the
critic agent; until you run it, the total is out of 80 and the scorecard says so in its own
defect list. See [`09-defects.md`](09-defects.md#no_critic).

---

## Look at it

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

Serves `dist/` and opens the canvas. Drag to pan, ⌘/Ctrl+scroll to zoom, `D` for dark mode,
`I` for the card index, `A` for the audit overlay, `?` for the full key map.

**Do this before you describe the library to anyone.** Some defects are invisible in every
deterministic number and obvious the moment you see the card — a motif eating the type on one
ground, a rule running past its content, a closing note reading as another row.

---

## Next

- [Concepts](02-concepts.md) — what a mechanic tuple is, why sparse cards are a content
  problem rather than a spacing problem, and why surfaces are a named set
- [The pipeline](03-pipeline.md) — what each stage writes and when to re-run it
