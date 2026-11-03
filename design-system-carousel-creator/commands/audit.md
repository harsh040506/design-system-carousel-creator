---
description: Measure, score and gate a template library against the quality rubric.
argument-hint: "[library.html] [--critic] [--strict] [--note \"…\"]"
allowed-tools: Read, Write, Bash, Glob, Skill, Agent
---

# /design-system-carousel-creator:audit

`$ARGUMENTS`

Load `quality-gate`.

## Deterministic pass

Inside a project this takes **no arguments**:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py audit
```

It reads `project.json` for the library, system, brief, plan, shots, rhythm and output directory, and
prints what it wired so you can see it was right. Passing five paths by hand on every invocation is
five chances to audit a library against the wrong brief. Explicit flags still win when you need them.

This produces `audit/lint.json`, `measure.json`, `uniq.json` and `scorecard.json`, plus per-card
PNGs, and appends one line to `audit/history.jsonl`. It covers the 80 deterministic points (70 if the project has no content brief, since Veracity
needs one).

`--strict` promotes every accepted-but-unresolved P2 into a gate failure. Use it when you intend to
actually close `GAP_VARIANCE` rather than note it for a third run. An unscored Craft (no `critic.json`) also fails the gate under `--strict`.

## Constraints

If the project declares any, they are checked here and reported as `constraints … -> clean` or
`BREACHED`:

| code | severity | means |
|---|---|---|
| `CROSS_REFERENCE` | P1 | a card depends on having read another |
| `SOURCE_LEAK` | P0 | a forbidden term or an attribution shape, in a card **or** in the chrome |
| `MISSING_REQUIRED` | P1 | a required term appears nowhere in the library |

A breach fails the gate regardless of the total. These are not quality gradients — the user said no
card may depend on another, and either that is true of the library or it is not.

`CROSS_REFERENCE` is resolved by **restating the referenced fact on the card**, never by deleting the
sentence. A card that points elsewhere is a card missing content, which is the density law wearing a
different hat.

## Judged pass

Run the `design-critic` agent over `shots/` with `${CLAUDE_PLUGIN_ROOT}/schema/rubric.json`, write
`audit/critic.json`, then re-score:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --lint audit/lint.json \
  --measure audit/measure.json --uniq audit/uniq.json \
  --critic audit/critic.json --brief build/content-brief.json --out audit/scorecard.json
```

Without it the total is scaled up from the deterministic points that could be scored (80 with a content brief, 70 without), Craft reads `--`, and the
scorecard carries a `NO_CRITIC` defect saying so. **Repeat that in your report.** Presenting a
scaled score as a full 100-point one is the specific dishonesty this pipeline's whole benchmark
section exists to prevent.

## Reading the result

In this order: **gate → P0 defects → weakest card → library statistics.**

The per-card floor matters more than the total. A library averaging 84 with one card at 48 is not an
84 library — a reader hits that card and the set loses credibility. Averages hide precisely the
thing that damages perception most.

The library statistics come last but are where systemic problems live. No P0s, a decent average, and
a gap CV of 0.55 means a rhythm problem that no single card would reveal.

## When a measurement contradicts your eye

Suspect the measurement first, then say so. This harness has been wrong before in exactly that way —
it once flagged every card as crowded because it measured to the footer element rather than the
footer rule, and reported 100% ink coverage on reference libraries because it counted the card's
background surface as content. Both produced confident, precise, wrong numbers.

Verify against three cards you have actually looked at before trusting it on fifty you haven't. If
the harness is wrong, fix the harness — do not quietly work around it, and do not "fix" the library
to satisfy a broken check.

The same applies to a check that fires on known-good work. `CROSS_REFERENCE` originally matched a
bare "back to", so "Where surplus goes / Back to members" — an answer, not a reference — failed the
gate. A verifier that cries wolf gets ignored, which is worse than not having one. Tighten the check;
do not edit the card.

## Then look at it

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

Press `A` for the audit overlay: every card carries its score and defect codes, and failing cards get
a red edge. Some defects are invisible in the numbers and obvious the moment you look — a motif eating
the type on one ground, a rule running past its content, a closing note reading as another row. The
deterministic score and your eyes are checking different things; run both before calling a card done.
