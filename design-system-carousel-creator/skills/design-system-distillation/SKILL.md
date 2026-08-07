---
name: design-system-distillation
description: Converts a brand design system given as prose, markdown, a style guide, CSS variables, or a Tailwind theme into a closed, machine-checkable token contract for template generation. Use when a user pastes a brand style reference and wants templates built from it, or when design values need locking into scales before layout work begins.
---

# Design System Distillation

Turn a brand document into a **closed set of legal values**. Everything downstream validates against
it, so drift becomes impossible rather than merely discouraged.

The input is whatever the user has: a markdown style reference, a paste of CSS custom properties, a
Tailwind `@theme` block, a PDF brand book, three screenshots and a paragraph. The output is always
the same shape: `design-system.json` conforming to `schema/design-system.schema.json`.

---

## Why "closed" is the whole point

An open system says "headings are large, around 48–64px." A closed system says "headings are 62px,
and 46px, and nothing else." The second one can be checked by a program.

That single property is what makes everything else in this plugin work:

- "is the library consistent?" becomes a grep, not a squint
- re-typing fifty cards becomes editing nine numbers
- a new card cannot introduce a new size, because there is nowhere to put one
- an audit can report *drift* as a defect with a line number

Brand documents almost never arrive closed. Closing them is the work.

---

## The seven extractions

### 1 · Colour → roles, not names

Brand palettes come named for what they are (`eggshell`, `warm-taupe`, `stone`, `graphite`). Layout
needs them named for what they *do*. Map every brand colour onto exactly one role:

| Role | What it is |
|---|---|
| `--surface` | the card background |
| `--surface-2` | panels, tiles, tags — one step off the background |
| `--surface-3` | the deepest neutral fill, marks, bar tracks |
| `--ink` | primary text and the strongest graphic element |
| `--muted` | secondary text — body copy, kickers |
| `--faint` | tertiary text — captions, annotations, inactive states |
| `--on-ink` | text sitting on `--ink` |
| `--rule` | hairlines and borders |
| `--accent` / `--accent-2` | brand colour, used per the legality rules below |

Then produce the **inverse plate** set (`--plate-bg`, `--plate-fg`, `--plate-mute`, `--plate-rule`,
`--plate-well`). Most brand documents don't specify one. Derive it: the plate background is the
brand's darkest neutral (light mode) or a lifted near-black (dark mode), and the plate roles mirror
the primary roles at inverted contrast.

**Both themes, always.** Light and dark are two complete role maps, not one map with a filter.
Deriving dark mode by inverting lightness produces muddy, over-saturated results. Pick real values.

**Background purity.** If the brand says "never pure white or pure black," honour it — near-white
and near-black are a large part of why premium brand systems look premium. If the brand doesn't say,
default to near rather than pure anyway.

### 2 · Type → nine steps, exactly

Three families (`display`, `body`, `mono` — collapse to fewer if the brand has fewer) and nine size
steps:

```
kicker · display · heading · heading-sm · body-xl · body-lg · body-sm · caption · mono
```

Brand documents give web scales. **Social artboards need roughly 2.2–2.6× web sizes.** A 24px web
h1 is a 148px display on a 1080px artboard. Getting this wrong is the single most common reason
generated slides read as reports: the type is technically on-brand and visually far too small.

Minimums for a 1080×1350 artboard, non-negotiable:

| Step | Floor | Why |
|---|---|---|
| display | 120px | it's the scroll-stopper |
| heading | 52px | must survive thumbnail scale |
| body-xl | 34px | the "one idea" line |
| body-sm | 23px | the practical legibility floor |
| caption | 19px | anything smaller is decoration |

Also fix the five-step **figure ramp** (`hero · lg · md · sm · xs`). Numbers are graphics and want
their own ramp: larger, tighter tracking, lighter weight than headings at the same optical size.

**Font substitution.** Proprietary brand faces usually aren't available. Substitute by *skeleton*,
not by vibe — match x-height, contrast and terminal style. Record the substitution explicitly in
`typography[].note` so nobody later mistakes it for the real specification.

### 3 · Spacing → seven values

`4 · 8 · 16 · 20 · 24 · 32 · 40`. A 4px half-step on an 8px base. Seven steps is enough for any
card; an eighth is a symptom that a layout is fighting the system.

Also fix `--rhythm` — the reference unit for the density auditor's gap ceiling. 64px suits a
1080×1350 artboard.

### 4 · Radii → three roles

`pill` (9999px, for tags and chips), `card` (panels), `tile` (smaller fills), `icon` (squircle-ish
icon tiles). If the brand specifies a minimum radius, respect it as a floor everywhere.

### 5 · The motif

**Every library needs one recurring non-typographic graphic.** This is what makes fifty different
compositions read as one family — more than colour does, and much more than font does.

Find it in the brand material: a gradient sphere, a notch, a logo lockup, a specific rule treatment,
a mark. If the brand has no obvious motif, derive one from the accent colour and the brand's stated
character, and say plainly in the output that it was derived.

Record: what it is, the exact CSS that draws it, roughly what fraction of cards should carry it
(⅓ is a good default), and where it must never appear.

**Always add grain.** A flat CSS gradient reads as a default; the same gradient under an
`feTurbulence` noise overlay reads as designed.

### 6 · Legality rules

The part of a brand document that's written as prose and needs to become enforcement. Typical:

- accent colours appear only in the motif and product visuals — never on borders, rules, or text
- backgrounds are never pure white or pure black
- tags and chips are always fully pilled
- the wordmark never appears at less than N px, never rotated, never re-coloured

Each becomes a `rules[]` entry with a `check` field naming the lint rule that enforces it, where one
exists.

### 7 · Anti-instructions

Extract the brand's don'ts verbatim and add the social-medium ones (see `carousel-craft` law 1).
These go straight into the compositor's prompt as hard constraints.

---

## Handling thin input

Users often paste half a system. Fill gaps by derivation, never by silence, and **mark every derived
value** with `"derived": true` plus a one-line rationale.

| Missing | Derivation |
|---|---|
| dark theme | build a real inverse role map; don't filter the light one |
| plate colours | darkest neutral as `--plate-bg`; mirror roles at inverted contrast |
| figure ramp | display × [1.35, 0.84, 0.53, 0.43, 0.35], rounded to whole px |
| mono family | a geometric mono matching the body face's x-height |
| motif | derive from accent + stated character; say so |
| spacing scale | the standard seven; almost always right |

The output must report a `coverage` figure — what proportion of the contract came from the source
versus derivation — so the user knows how much of the result is their brand and how much is the Creator's
judgement. A system at 40% coverage still produces a good library; the user just deserves to know.

---

## Output

Write `design-system.json`. Then emit the `:root` blocks that precede `kernel.css` in the built
library — the JSON is the contract, the CSS is its compiled form, and they must be generated
together so they cannot disagree.

Validate before finishing:

```
python scripts/dscc.py doctor --system design-system.json
```

This checks that every key `kernel.css` requires is present, that the type floors are met, and that
no two roles resolve to the same colour (which silently destroys contrast in one theme while looking
fine in the other).
