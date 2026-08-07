---
name: quality-gate
description: The quality scoring framework — how carousel template libraries are measured, scored across six dimensions, and gated before release. Use when auditing, scoring, refining, or comparing template libraries, or when deciding whether generated design work is good enough to ship.
---

# The Quality Gate

How a library gets from "looks fine" to "measured, scored, and provably good."

**The gate is self-contained.** Every threshold below — coverage floors, gap ceilings, scale
conformance — is a fixed constant in `scripts/score.py`, calibrated once during development and
locked in. None of it is fetched from a comparison file at run time. A library built with zero other
libraries present in the working tree is held to exactly the same bar as one built alongside a dozen
of them. **No reference library is required to use this system, and none is required to produce
reference-quality output from it.**

`/design-system-carousel-creator:bench` (optional) exists for a different situation: you have a *specific* library in mind —
something you built before, competing work, an earlier draft — and want a candidate measured against
it explicitly. That's an extra comparison layered on top of the gate, never a prerequisite for it.
See `/design-system-carousel-creator:ship` §2b.

---

## The split

Six dimensions, 100 points. **Eighty are deterministic** — computed by `scripts/dscc.py`, identical
on every run, diffable across versions, arguable with evidence. **Twenty are judged** by the
`design-critic` agent from rendered PNGs against an anchored rubric.

Of the eighty, seventy are *portable*: computable on any library, with or without this plugin's metadata.
That subset is what makes benchmarking against foreign libraries possible at all.

| Dimension | Pts | Method |
|---|---|---|
| Integrity | 20 | deterministic |
| Discipline | 15 | deterministic |
| Density | 20 | deterministic |
| Distinction | 15 | deterministic |
| Veracity | 10 | deterministic |
| Craft | 20 | judged |

### Constraints are not a seventh dimension

A constraint the user declared — "each card must stand alone", "do not mention the source" — is not
worth points. It is worth being **true**. So `CROSS_REFERENCE`, `SOURCE_LEAK` and `MISSING_REQUIRED`
carry no weight of their own; they enter the defect list, they fail the gate outright, and the
scorecard reports which constraints were checked and whether they came back clean.

That reporting matters as much as the checking. Without it "gate: PASS" means only that the geometry
is sound. With it, a pass says something specific about the thing the user actually asked for.

### An unscored dimension must be said out loud

If `critic.json` is absent, Craft's 20 points are not scored, the total is out of 80, and the
scorecard carries a `NO_CRITIC` defect that says so in those words. **Repeat it in the report.**

Presenting an 80-point total as though it were a 100-point one is the same dishonesty the benchmark
caveats exist to prevent, and it is easier to commit because nothing about the number 99.6 looks
incomplete.

The split exists to stop the judged half doing the deterministic half's job. A model looking at a
screenshot will confidently say "spacing looks consistent" while three cards differ by 60px. It
cannot see 4px of overflow. It cannot count tuple collisions across fifty cards. Give those to the
machine and reserve judgement for what actually needs taste.

---

## Ship gate

```
total ≥ 80/100          AND
min per-card ≥ 70/100   AND
zero P0 defects         AND
Density ≥ 15/20         AND
Distinction ≥ 11/15
```

The per-card floor matters more than the total. A library averaging 84 with one card at 48 is not an
84 library — a reader hits that card and the whole set loses credibility. Averages hide exactly the
thing that damages perception most.

The two dimension-specific floors are there because Density and Distinction are the ones that can be
traded away invisibly to raise a total.

---

## What each dimension measures

### Integrity — 20

| Check | Points | Defect |
|---|---|---|
| No content past artboard bounds | 6 | `OVERFLOW` (P0) |
| No colliding text boxes | 5 | `COLLISION` (P0) |
| Balanced markup per card | 4 | `UNBALANCED` (P0) |
| Every `var()` declared | 3 | `UNDECLARED_VAR` (P0) |
| Media slots present and sized | 2 | `EMPTY_SLOT` (P1) |

Decorative elements (`.motif`, `.dot-grid`, `.bleed`, `.scrim` and descendants) are excluded from
bounds checks — bleeding decoration is intent.

### Discipline — 15

| Check | Points | Defect |
|---|---|---|
| Zero raw px in card markup | 4 | `RAW_PX` |
| Zero raw hex in card markup | 3 | `RAW_HEX` |
| Zero inline `font-size` | 3 | `INLINE_TYPE` |
| Computed sizes on the locked ramps | 3 | `OFF_SCALE` |
| Gaps/margins on the spacing scale | 2 | `OFF_SCALE_SPACE` |

`OFF_SCALE` is the one that catches slow drift — it reads *computed* values from the browser, so it
finds sizes introduced through a class the linter never saw.

### Density — 20

| Check | Points | Defect |
|---|---|---|
| Ink coverage ≥40% | 7 | `SPARSE` |
| Max row gap ≤1.5× rhythm | 6 | `UNDERWRITTEN` |
| Bottom slack licensed | 4 | `UNLICENSED_SLACK` / `FALSE_LICENSE` |
| Library gap CV ≤0.35 | 2 | `GAP_VARIANCE` |
| Coverage ≤78% | 1 | `OVERPACKED` |

See `carousel-craft/references/density-law.md` for the full treatment. The critical property: these
defects name a **cause**, not a symptom, because the name determines which fix gets reached for.
`UNDERWRITTEN` is resolved by writing. Adjusting spacing to clear it is a rule violation, and the
refiner is told so explicitly.

### Distinction — 15

| Check | Points | Defect |
|---|---|---|
| Zero duplicate mechanic tuples | 6 | `DUP_LAYOUT` |
| Mean pairwise distance ≥2.6 | 4 | `LOW_VARIETY` |
| ≥8 of 10 partitions used | 2 | `NARROW_RANGE` |
| No partition on >9 cards | 2 | `OVERUSED` |
| Media/plate/tinted mix on target | 1 | `MIX_OFF` |

Uniqueness is defined as tuple equality, so it is exact rather than impressionistic. Mean distance
catches the subtler failure: a set where every pair differs on exactly one axis is technically
collision-free and still monotonous.

### Veracity — 10

| Check | Points | Defect |
|---|---|---|
| Every text node traces to a claim | 5 | `UNSOURCED` |
| Every number appears in the brief | 4 | `INVENTED_FIGURE` |
| No claim used more than twice | 1 | `CLAIM_REUSE` |

Requires a `content-brief.json`. Libraries without one score `null` on this dimension and are graded
out of 90 — which is also why benchmark comparisons against foreign libraries are made on the 60
shared deterministic points.

`INVENTED_FIGURE` is the highest-consequence defect in the whole system. A beautiful slide
containing a number nobody can source is worse than an ugly one.

### Craft — 20, judged

Five sub-criteria at 4 points each, scored 1–5 from rendered PNGs and scaled:

1. **Hierarchy** — one clear entry point; the eye knows where to start
2. **Social-nativeness** — reads as a post, not a webpage or a report
3. **Thumbnail legibility** — the idea survives at 1/3.6 scale
4. **Copy quality** — one claim, poster-length, no subordinate clauses
5. **Compositional interest** — the card is worth looking at, not merely correct

Anchors for every point on every scale are in `schema/rubric.json`.

**Every deduction must cite a card index and a visible reason.** Unanchored deductions ("feels
generic") are discarded when the critic's JSON is merged. This is the only defence against a judged
score that drifts to a comfortable 3-out-of-5 on everything.

---

## The refine loop

```
audit → defects sorted by (severity, dimension weight, card index)
      → fix in batches by defect class, not card by card
      → re-audit
      → repeat, max 4 passes
```

**Batch by defect class.** Fixing card-by-card re-introduces drift, because each card gets its own
local judgement. Fixing every `UNDERWRITTEN` in one pass means one decision applied consistently.

**Fix causes.** Each defect class has a legal fix list and an illegal fix list
(`density-law.md` § enforcement). The illegal fixes are the ones that clear the check without
improving the work — they exist in the table specifically because they are tempting.

**Stop conditions.** Gate passed; or four passes with score improving <1.5 points per pass, at which
point the remaining defects are structural and need a human decision about scope, not another pass.

**Scope discipline.** A defect reported on cards 32, 33, 40 and 44 is fixed on cards 32, 33, 40 and
44. If a fix seems to want to be global, that is a claim about the whole library — state it, get it
confirmed, then apply it. Silently generalising a scoped instruction is its own defect class and has
cost more rework than any layout bug.

---

## Benchmarking

`dscc.py bench` runs the identical deterministic auditor over reference libraries and the
candidate, and prints one table.

Two caveats, always printed with the results because a benchmark that hides them is worthless:

1. **Veracity is unscoreable for foreign libraries** — no brief, so the comparison is made on the 60
   deterministic points all libraries share.
2. **Foreign libraries are audited in degraded mode** — no manifest, so the artboard is auto-detected
   and intent licensing can't be read. Unlicensed slack is scored *in their favour*. The candidate is
   held to the stricter standard.

If the candidate only wins because the rules differ, the table says so. That is the difference
between measuring quality and manufacturing a favourable number.

---

## Reading a scorecard

`scorecard.json`:

```jsonc
{
  "total": 84.5,
  "gate": "PASS",
  "dimensions": { "integrity": 20, "discipline": 14, ... },
  "cards": [ { "index": 1, "score": 88, "defects": [...] } ],
  "defects": [
    { "code":"UNDERWRITTEN", "severity":"P1", "card":9,
      "detail":"max row gap 112px > 96px ceiling",
      "legal_fix":"add a row from the claim inventory" }
  ],
  "library": { "gap_cv": 0.28, "mean_tuple_distance": 3.1, "coverage_mean": 0.52 }
}
```

Read in this order: **gate → P0 defects → weakest card → library-level stats.** The library stats
are last but are where systemic problems live; a library with no P0s, a decent average and a gap CV
of 0.5 has a rhythm problem that no single card would reveal.
