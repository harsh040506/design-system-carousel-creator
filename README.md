# Design System Carousel Creator

A Claude Code plugin that turns a brand design system and a pile of source documents into a
50-slide social carousel template library — **proves** the result is good before it ships, and
opens it on a real canvas so you can see it.

The point is not generation. Generation is the easy half. This exists because the expensive half
is everything that happens *after* the first draft: noticing that six cards were padding
themselves with 200px of invented air, that three Q&A slides were the same slide, that a `.pane`
without `min-width:0` was pushing text through the frame, that the type ramp had quietly grown
twelve one-off sizes. The plugin encodes that work as a machine.

```
pip install playwright && playwright install chromium

/design-system-carousel-creator:run DESIGN.md whitepaper.pdf
```

One command, whole pipeline, ends with the library open in your browser.

📖 **[Full documentation](design-system-carousel-creator/docs/)** — getting started, concepts, every command, the canvas,
defect reference, troubleshooting.

---

## The core bet

> Anything you had to *notice* by eye, twice, should have been a check.

Quality splits into two halves, and the judged half is never allowed to do the deterministic
half's job:

- **80 points are machine-verified.** Overflow, collisions, ink coverage, gap regularity, token
  conformance, layout uniqueness, claim provenance. Reproducible, arguable, diffable across runs.
  (70 of those 80 are *portable* — computable on any library, which is what makes benchmarking
  possible at all. The remaining 10, Veracity, needs a content brief.)
- **20 points are judged** by a critic agent working from an anchored rubric with worked
  examples, scoring rendered PNGs — never source code.

A library ships at **≥80 total, ≥70 per card, zero P0 defects, and every declared constraint
clean.** Below that, `:refine` loops.

The thresholds are fixed constants in `scripts/score.py`, calibrated once and locked. **No
reference library is required.** Every gate check, scale floor and density ceiling works
identically whether you have a dozen comparison files or none.

If you *do* have a library you consider best-in-class, `:bench` runs the identical auditor over
both and prints the comparison. Optional extra, never a dependency.

---

## What you get

```
Acme Templates/
├── project.json     identity, wiring, constraints, pipeline state
├── README.md        generated — how to rebuild, how to preview
├── inputs/          FROZEN copies of the design system and every source document
├── build/           design-system.json · content-brief.json · layout-plan.json · build.py
├── dist/            THE DELIVERABLE — self-contained, servable, zippable
├── audit/           scorecard · lint · measure · uniq · report.html · history.jsonl
├── shots/           per-card PNGs
└── RELEASE.md
```

`dist/` reaches outside itself for nothing. `inputs/` is frozen at creation rather than copied
at ship time — a step you have to remember is a step that eventually doesn't happen, and six
months later nobody knows which brief produced which slides.

---

## Highlights

| | |
|---|---|
| **Projects** | One self-contained folder per library. Nothing writes into your working directory, so a second run can never overwrite the first |
| **A canvas that opens** | `dscc preview` serves the bundle and opens it: pan, zoom, dark mode, filterable card index, per-card audit overlay, minimap, presenter mode, live reload |
| **Constraints as code** | "each card must stand alone" and "don't mention the source" become flags, then `CROSS_REFERENCE` (P1) and `SOURCE_LEAK` (P0) checked on every audit |
| **Regenerable libraries** | `build/build.py` ships beside every library. The `.dc.html` is an output, not a hand-edited artifact |
| **Zero-argument audit** | Inside a project it reads its own wiring. Five manual paths is five chances to audit against the wrong brief |
| **Theme safety** | A colour used on a card but absent from both theme maps is provably wrong in one theme — a static check, not a judgement call |
| **Audit history** | `audit/history.jsonl`, append-only. The refine trail is a file, not a memory |
| **Nothing phones out** | Building, auditing and previewing all work offline. The canvas embeds its own UI font rather than fetching one |

---

## The pipeline

```
                       :new  ──►  <Project>/  + project.json
                          │        inputs frozen, constraints declared
   design system          │            source documents
          │               │                   │
      :distill            │               :brief
          │               │                   │
 build/design-system.json │      build/content-brief.json
          └───────────────┼───────────────────┘
                          ▼
                       :plan  ──►  build/layout-plan.json
                          │        50 mechanic tuples, collision-checked
                          ▼
                      :build  ──►  dist/<Name>.dc.html
                          │         + runtime · canvas · slot state
                          ▼
              ┌────────  :audit  ────────┐
        deterministic              design-critic
   (lint · measure · uniq)        (rendered PNGs)
              └──────── score ───────────┘
                          │
               ≥80? ──no──►  :refine  (max 4 passes)
                  │
                 yes
                  ▼
               :ship  ──►  :preview
```

`:run` executes all of it. The stages are separately invocable because in practice you re-run
`plan → build → audit` a dozen times and `distill` once.

---

## Inputs

**Content** — any mix of `.md`, `.txt`, `.pdf`, `.docx`, or text pasted into the conversation.
`.docx` is routed through `scripts/extract_text.py` (stdlib zip/XML, no dependency), which
preserves heading levels and pulls table cells in reading order. Legacy binary `.doc` isn't
parseable — re-save or paste.

**Design system** — a markdown style guide, a `.css` file of custom properties, a Tailwind
`@theme` block, a PDF brand book, or pasted prose. `:distill` extracts the same seven categories
regardless of shape: colour roles, type, spacing, radii, motif, legality rules,
anti-instructions.

---

## Install

```
/plugin marketplace add <this-directory>
/plugin install design-system-carousel-creator
```

Or point Claude Code at the folder directly — the plugin is self-contained.

**Runtime dependencies** (checked by `dscc.py doctor`):

```
pip install playwright && playwright install chromium
```

Python ≥ 3.10. No Node. No network at runtime.

---

## Two ideas worth knowing before you start

### The density law

> **A sparse card is under-written, not over-spaced.**

When a card has more room than content there are two moves. Distributing the slack between rows
invents 200px gaps that read as arbitrary, *because they are*. Adding a real row from the source
material does not.

So the auditor never flags "spacing" — it flags `UNDERWRITTEN`, and spacing adjustment is
explicitly disallowed as a fix. This single constraint is the largest reason the pipeline
produces different work than a one-shot generation would.

The licensed exception: a card may declare `intent: "breathe"` — legal for covers, closers,
single-figure statements, media-led cards and cards with ≤4 rows. Unlicensed slack is a defect;
licensed slack is a design decision.

### Uniqueness, defined

Two slides are the same slide if their **mechanic tuple** matches:

```
(partition, flow, enumerator, emphasis, media, chrome)
```

The collision check is exact, and `uniq.py` also reports mean pairwise Hamming distance — a
library where every pair differs on one axis is technically legal and still feels repetitive.
The gate requires ≥ 2.6. "Fifty unique layouts" stops being an aspiration.

---

## Scoring

| Dimension | Pts | Method | Catches |
|---|---|---|---|
| **Integrity** | 20 | deterministic | overflow, colliding text, unbalanced markup, undeclared tokens, empty slots |
| **Discipline** | 15 | deterministic | raw px/hex, inline `font-size`, off-scale values, colours that can't follow the theme |
| **Density** | 20 | deterministic | ink coverage <40%, unlicensed slack, gaps >1.5× rhythm, gap variance |
| **Distinction** | 15 | deterministic | duplicate layouts, low variety, over-used partitions, flat surfaces |
| **Veracity** | 10 | deterministic | text with no provenance, numbers absent from the brief |
| **Craft** | 20 | judged | weak hierarchy, web chrome, thumbnail illegibility, copy that reads like a report |

Full anchors live in [`schema/rubric.json`](design-system-carousel-creator/schema/rubric.json). The critic must cite a card
index and a visible reason for every deduction; unanchored deductions are discarded on merge.

**If Craft is unscored the total is out of 80, and the scorecard says so in its own defect list.**
Presenting an 80-point total as a 100-point one is the exact dishonesty the benchmark caveats
exist to prevent.

---

## Layout

```
design-system-carousel-creator/
├── commands/         12 slash commands — the pipeline stages
├── agents/           5 subagents — distiller, strategist, architect, compositor, critic
├── docs/             the full guide
├── skills/
│   ├── carousel-craft/            the design knowledge
│   │   ├── references/mechanics.md      40 layout mechanics, described not copied
│   │   ├── references/density-law.md    fill vs. breathe, in full
│   │   ├── references/theming.md        one document, two themes, and the law
│   │   ├── references/anti-patterns.md  every failure mode, its tell, its fix
│   │   └── assets/kernel.css            brand-agnostic primitive layer
│   ├── design-system-distillation/
│   └── quality-gate/
├── scripts/
│   ├── dscc.py       CLI: new · list · info · doctor · build · audit · preview · report · bench
│   ├── project.py    project isolation: new · adopt · info · history
│   ├── scaffold.py   .dc.html envelope + runtime + canvas + emitted builder
│   ├── serve.py      preview server: free port, SSE live reload
│   ├── report.py     the project as one self-contained HTML page
│   ├── slots.py      image slots: list · fill · state · audit
│   ├── lint.py       static analysis + declared-constraint enforcement
│   ├── measure.py    Playwright geometry harness
│   ├── uniq.py       mechanic-tuple collision + distance
│   └── score.py      merge → scorecard
├── assets/           vendored runtime · canvas host · builder template
└── schema/           JSON Schemas for every artifact + the judged rubric
```

`scripts/` has no dependency on Claude — run it in CI, on a library you built by hand, on
someone else's. `skills/` has no dependency on the scripts. Either half is useful without the
other, which is the main reason the split exists.

---

## Deliberate non-goals

- **No stored reference templates.** The plugin ships zero copied markup. What it ships is the
  mechanics catalogue, the density law, the anti-pattern list and the primitive layer — the
  *reasons* good libraries work. Copying layouts would cap output at imitation.
- **No raster export.** PNG/PDF rasterization belongs downstream. `shots` renders PNGs for the
  critic's eyes and the report's thumbnails, and that is its whole job.
- **No hosted anything.** Every artifact is a file in a folder. `serve` binds localhost and dies
  with the process.
- **No remote images.** `slots fill` copies local files in. A dead URL renders worse than a
  described slot, and the document must render offline.
- **No auto-fixing of judged defects.** The critic reports; a human or the model decides. A tool
  that silently "improves" a composition is a tool whose scorecard you cannot trust.

---

## Licence

MIT. The bundled JetBrains Mono subset is SIL OFL 1.1 — see
[`assets/canvas/FONT-LICENSE.md`](design-system-carousel-creator/assets/canvas/FONT-LICENSE.md).
