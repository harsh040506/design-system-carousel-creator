# 4 · Command reference

All twelve slash commands. The full invocation prefix is
`/design-system-carousel-creator:` — abbreviated to `:` in the headings below.

| Command | Does |
|---|---|
| [`:run`](#run) | The whole pipeline, end to end |
| [`:new`](#new) | Create an isolated project |
| [`:distill`](#distill) | Brand document → token contract |
| [`:brief`](#brief) | Source documents → atomic claims |
| [`:plan`](#plan) | All fifty layouts, collision-checked |
| [`:build`](#build) | Plan → HTML, via the generator |
| [`:audit`](#audit) | Measure, score, gate |
| [`:refine`](#refine) | Fix defects by cause until the gate passes |
| [`:preview`](#preview) | Serve the bundle, open the canvas |
| [`:report`](#report) | One self-contained HTML report |
| [`:bench`](#bench) | Compare against libraries you supply |
| [`:ship`](#ship) | Verify, version, write the release record |

---

## `:run`

```
:run <design-system.md> <source-doc...> [--cards 50] [--out DIR]
```

Runs every stage in order and ends with the library open on a canvas.

**Does not ask questions.** Card count, artboard size, taxonomy, tone, theme handling, surface
set and media ratio are all decided in [`schema/defaults.json`](../schema/defaults.json). The
choices are reported at the end so you can redirect any you disagree with.

Stops only when: the sources contradict each other on a fact that would appear on a card, the
brand supplies no colour information at all, or the content is plainly for another medium.

---

## `:new`

```
:new "<Name>" [--system DESIGN.md] [--source doc.pdf] [--independent] [--no-source]
```

| Flag | |
|---|---|
| `--system PATH` | design system to freeze into `inputs/` |
| `--source PATH` | source document, repeatable |
| `--into DIR` | parent directory (default: cwd) |
| `--dirname NAME` | folder name, if different from the project name |
| `--brand NAME` | brand label for the manifest |
| `--width` `--height` | artboard, default 1080 × 1440 |
| `--cards N` | default 50 |
| `--cols N` | gallery grid columns, default 5 |
| `--independent` | no card may depend on another → `CROSS_REFERENCE` (P1) |
| `--no-source` | no attribution anywhere in the artwork → `SOURCE_LEAK` (P0) |
| `--forbid "TEXT"` | forbidden literal, repeatable |
| `--force` | write into a non-empty directory |

**Run this first, always.** The constraint flags are the important half — see
[Constraints](07-constraints.md).

---

## `:distill`

```
:distill <design-system.md|url|paste> [--out design-system.json]
```

Reads a style guide, CSS file, Tailwind `@theme`, PDF brand book or pasted prose and extracts
the same seven categories regardless: colour roles, type, spacing, radii, motif, legality
rules, anti-instructions.

Validate with `dscc.py doctor --system build/design-system.json`. Report the coverage figure —
the fraction that came from the source rather than derivation.

---

## `:brief`

```
:brief <source-doc...> [--cards 50] [--out content-brief.json]
```

Reads every source **in full**. Extracts atomic claims with provenance spans.

**Aim for 3× the card count.** The surplus resolves under-written cards later without
inventing anything.

---

## `:plan`

```
:plan [--cards 50] [--brief content-brief.json] [--out layout-plan.json]
```

One mechanic tuple per card, claims assigned, fill/breathe intent declared. Check with
`uniq.py` and resolve every `DUP_LAYOUT` and `MIX_OFF` **in the plan** — fixing distinction
after the cards exist means rebuilding them.

---

## `:build`

```
:build [--plan layout-plan.json] [--out "Brand Template Library.dc.html"]
```

Scaffold first, then write card composition into `build/build.py`. Never hand-edit the HTML.

Batches of ten, `lint.py` after each, `scaffold.py verify` before auditing.

See [Authoring cards](08-authoring.md).

---

## `:audit`

```
:audit [library.html] [--critic] [--strict] [--note "…"]
```

| Flag | |
|---|---|
| *(no args)* | inside a project, wires everything from the manifest |
| `--strict` | every accepted-but-unresolved P2 becomes a gate failure |
| `--note "…"` | recorded in `audit/history.jsonl` alongside the score |
| `--critic PATH` | merge the judged Craft dimension |
| `--top N` | how many weak cards to table, default 8 |
| `--auto` | auto-detect artboards, for libraries not built by this plugin |

Appends to history on every run.

---

## `:refine`

```
:refine <library.html> [--max-passes 4]
```

Batch by defect class, not by card. Fix the cause the defect names — every defect carries a
`legal_fix` and the names were chosen to name causes rather than symptoms.

Reads `audit/history.jsonl` first. A defect class surviving two passes with a flat total means
the problem is upstream.

**Scope discipline:** a defect reported on cards 32, 33, 40 and 44 is fixed on cards 32, 33, 40
and 44. If a fix seems to want to be global, that is a claim about the whole library — state
it, get it confirmed, then apply it.

---

## `:preview`

```
:preview [--watch] [--port 4173] [--no-open] [--dir DIR]
```

Serves `dist/` on the first free port from 4173 and opens `canvas.html`.

`--watch` re-runs `build/build.py` on change and pushes a reload that preserves your scale,
position, theme and focused card.

See [The canvas](06-canvas.md).

---

## `:report`

```
:report [--no-open]
```

Writes `audit/report.html`. Self-contained, thumbnails inlined, emailable.

---

## `:bench`

```
:bench <candidate.html> <comparison.html...>
```

Identical auditor over every library, one table, caveats printed. Optional — the gate needs no
reference.

---

## `:ship`

```
:ship <library.html> [--version 1.0.0]
```

Rebuild → verify → re-audit → check the gate honestly → write `RELEASE.md`.

If the gate fails, **do not ship and do not soften the report.** Say which condition failed, by
how much, and what it would take.

---

## Subagents

Five specialists the commands dispatch when the work warrants it:

| Agent | Role |
|---|---|
| `system-distiller` | brand document → token contract |
| `content-strategist` | long source sets → claim inventory |
| `layout-architect` | the fifty-tuple plan |
| `slide-compositor` | card markup from a mechanic |
| `design-critic` | the judged Craft dimension, from rendered PNGs only |

`design-critic` is the one you must dispatch deliberately: without it, Craft's twenty points
are unscored.
