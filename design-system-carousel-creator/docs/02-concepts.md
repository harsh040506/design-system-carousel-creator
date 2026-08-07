# 2 · Concepts

Seven ideas. Read them once and the rest of the tool explains itself.

---

## 1 · A run is a project

Every artifact for one library lives in one folder under a `project.json` manifest.

```
inputs/   frozen at creation — the design system and every source document
build/    the three planning artifacts + build.py, the library's source
dist/     the deliverable bundle
audit/    every scorecard, plus history.jsonl
shots/    per-card PNGs
```

Two consequences worth understanding:

**Nothing writes into your current directory.** A second library built in the same parent
folder cannot overwrite the first. Tools that scatter artifacts into the cwd fail this way
silently, and you only find out when the work is already gone.

**Every stage reads its wiring from the manifest.** This is why `dscc audit` takes no
arguments — it already knows where the system, brief, plan and shots are. Passing five paths
by hand on every invocation is five chances to audit a library against the wrong brief.

`inputs/` is frozen at `new` time, not copied at ship time. A step you have to remember at the
end is a step that eventually does not happen, and six months later nobody knows which brief
produced which slides.

---

## 2 · Eighty points are arithmetic, twenty are judgement

| Dimension | Pts | Method | What it catches |
|---|---|---|---|
| **Integrity** | 20 | deterministic | overflow past the artboard, colliding text, unbalanced markup, undeclared tokens, empty media slots |
| **Discipline** | 15 | deterministic | raw px/hex in card bodies, inline `font-size`, values off the locked scales, colours that cannot follow the theme |
| **Density** | 20 | deterministic | ink coverage below 40%, unlicensed bottom slack, row gaps over 1.5× rhythm, gap variance |
| **Distinction** | 15 | deterministic | duplicate layouts, low variety, over-used partitions, flat surfaces |
| **Veracity** | 10 | deterministic | text with no claim provenance, numbers absent from the brief |
| **Craft** | 20 | **judged** | weak hierarchy, web chrome, thumbnail illegibility, copy that reads like a report |

The split is the whole design. A model looking at a screenshot will say "spacing looks
consistent" while three cards differ by 60px, and it cannot see 4px of overflow at all. Give
those to arithmetic. Reserve judgement for what actually needs taste.

The thresholds are fixed constants in `scripts/score.py`, calibrated once and locked. **No
reference library is required.** A library built with nothing else on disk is held to exactly
the same bar as one built alongside a dozen comparisons.

### The gate

```
total ≥ 80  AND  min card ≥ 70  AND  zero P0
AND  density ≥ 15  AND  distinction ≥ 11
AND  every declared constraint clean
```

The per-card floor matters more than the total, for the reason in
[Getting started](01-getting-started.md#reading-the-score): averages hide precisely the thing
that damages perception most.

---

## 3 · Uniqueness is defined, so it is checkable

Two slides are the same slide if their **mechanic tuple** matches:

```
(partition, flow, enumerator, emphasis, media, chrome)
```

| Axis | Values |
|---|---|
| **partition** | how the content region divides — `monolith · stack · duo · triad · grid · rail · chain · strip · ledger · overlay` |
| **flow** | reading axis — `vertical · horizontal · z · radial · centred` |
| **enumerator** | what marks the items — `none · number · pip · rule · chip · icon · glyph` |
| **emphasis** | what carries the weight — `display · figure · media · quote · panel · diagram` |
| **media** | `none · inset · sidecar · full-bleed · repeated` |
| **chrome** | `standard · plate · tinted · flush` |

Those cardinalities give far more than fifty combinations, so uniqueness is achievable without
contortion. The collision check is exact.

But exactness alone is not enough: a library where every pair differs on exactly one axis is
technically legal and still feels repetitive. So the auditor also reports **mean pairwise
Hamming distance**, and the gate requires ≥ 2.6. "Fifty unique layouts" stops being an
aspiration and becomes a number.

---

## 4 · The density law

The rule that took longest to learn and is now non-negotiable.

> **A sparse card is under-written, not over-spaced.**

When a card has more room than content there are two moves. One is to distribute the slack
between rows so it looks full. That is the wrong move — it invents 200px gaps that read as
arbitrary, *because they are arbitrary*. The right move is to add a real row from the source
material.

So the auditor never flags "spacing". It flags **`UNDERWRITTEN`**, and the legal fix is to pull
an unused claim from the brief. Spacing adjustment is explicitly disallowed as a fix for that
defect class. This single constraint is the largest reason the pipeline produces different work
than a one-shot generation would.

### The licensed exception: `breathe`

A card may declare `intent: "breathe"` and leave slack at the bottom — legal only for:

`cover` · `close` · `single-figure` · `media-led` · `few-rows` · `section-break`

The manifest records the license; the auditor enforces it. **Unlicensed slack is a defect.
Licensed slack is a design decision.** The difference is that someone declared it in advance.

---

## 5 · Surfaces are a named set, not a light/dark pair

Every card is assigned one of six grounds, each with a complete text-colour treatment:

```
paper · panel · ink · accent-1 · accent-2 · grey
```

Five grounds minimum across a library. This is the highest-leverage move available for
perceived range, and it is the one generated libraries most consistently skip — binary
light/dark is the single most common failure. The auditor emits `FLAT_SURFACES` below five
grounds, and `GROUND_CLUSTER` when two loud grounds land on adjacent cards.

Ground classes remap role tokens on the frame, so one card markup shape renders correctly on
all six:

```css
.frame.g-panel { --surface: var(--panel-bg); --ink: var(--panel-fg); --rule: var(--panel-rule) }
```

---

## 6 · Themes multiply the surfaces

A library is **one document, two themes**. One enum prop, one `applyTheme()` writing custom
properties at runtime. Never separate light and dark files — they drift apart immediately and
double the maintenance surface.

Combined with the surface set, that means **six grounds × two themes = twelve states** every
card-level colour must survive.

The token indirection is what makes that tractable. A card that names a *role* is correct in
all twelve by construction; a card carrying a raw hex is correct in one. That is the real
reason `RAW_HEX` in card markup is a defect rather than a preference.

> **Every colour used in card markup belongs in both theme maps.**

A colour declared once in `:root` and referenced from a card cannot respond to the theme, which
on a two-theme document means it is provably wrong in one of them. The linter emits
`MONO_THEME_TOKEN`. The illegal fix is picking one colour that is *acceptable* in both — it
clears the check in a minute and produces a library where nothing is quite right anywhere.

See [`skills/carousel-craft/references/theming.md`](../skills/carousel-craft/references/theming.md).

---

## 7 · The library has a source

`build/build.py` is the generator. `dist/*.dc.html` is its output.

A 120 KB hand-edited HTML file with no source cannot be re-typed, re-themed or re-ordered. The
same file with a 400-line generator beside it is an asset: the type ramp is nine numbers in one
place, a ground is a dictionary, and a fix to a shared row shape reaches all fifty cards rather
than the eleven you remembered to edit.

Two invariants are baked into the emitted builder with comments telling you not to undo them.
Both are explained in [Authoring cards](08-authoring.md#two-invariants-you-must-not-undo).

---

## Next

- [The pipeline](03-pipeline.md) — the stages, in order
- [Authoring cards](08-authoring.md) — writing the builder
