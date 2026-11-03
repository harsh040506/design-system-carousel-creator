---
description: Iteratively fix audit defects by cause until the quality gate passes.
argument-hint: "<library.html> [--max-passes 4]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

# /design-system-carousel-creator:refine

`$ARGUMENTS`

Load `quality-gate` and `carousel-craft`. Read `audit/scorecard.json` **and `audit/history.jsonl`**.

The history is append-only, one line per audit for the life of the project: total, per-dimension,
defect counts, gate, note. Read it before deciding what to try. If a defect class has survived two
passes with the total flat, the fix you are reaching for is not working and the problem is upstream —
a thin claim pool or a weak layout plan — not something a third editing pass will reach.

## Batch by defect class, not by card

Walking card by card gives each card its own local judgement, which is how drift got into the
library in the first place. Fixing every `UNDERWRITTEN` in one pass means one decision applied
consistently to all of them.

Order: all P0 first, then P1 by dimension weight, then P2.

## Fix the cause the defect names

Every defect carries a `legal_fix`. The names were chosen to name causes, not symptoms, because the
name is what determines which fix gets reached for.

| Defect | Fix | **Not** |
|---|---|---|
| `UNDERWRITTEN` | add a real row from the unused claim pool | adjust spacing, shrink type, add padding |
| `SPARSE` | add content, enlarge media, promote a figure | stretch existing rows apart |
| `UNLICENSED_SLACK` | declare a license, or fill the card | leave it and hope |
| `FALSE_LICENSE` | drop the license and fill | widen what the license means |
| `OVERPACKED` | split into two cards | shrink the type |
| `OVERFLOW` | `min-width:0` on the flex child; shorten the headline | `overflow:hidden` |
| `DUP_LAYOUT` | change enumerator → chrome → emphasis → partition | rewrite the copy |
| `CROSS_REFERENCE` | **restate** the referenced fact on this card | delete the sentence |
| `SOURCE_LEAK` | remove the attribution, including from labels and chrome | reword it to be subtler |
| `MONO_THEME_TOKEN` | put the token in **both** theme maps | pick one colour that survives both |

The "not" column exists because each of those clears the check in under a minute and makes the
library worse. That is why they are written down.

`CROSS_REFERENCE` deserves the same note `UNDERWRITTEN` gets: deleting the referring sentence leaves
the card thinner than it was. A card that points at another card is a card missing content — the
density law again, wearing a different hat.

`MONO_THEME_TOKEN`'s "not" column is the subtler trap. A colour tuned to be acceptable on both
grounds is acceptable on neither, and the compromise is invisible until you put the two themes side
by side — which is what `/design-system-carousel-creator:preview` and `D` are for.

## Rebuild, do not hand-edit

The library has a source: `build/build.py`. Fix the generator and re-run it. Editing the built HTML
means the next rebuild silently discards the fix, and there **will** be a next rebuild.

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview --watch
```

runs the builder on every save and reloads the canvas with your scale, position and focused card
intact. Refining against a live view rather than a JSON file is the largest single speedup available
here.

## Scope discipline

A defect reported on cards 32, 33, 40 and 44 is fixed on cards 32, 33, 40 and 44.

If a fix seems to want to be global, that is a claim about the whole library. State it, get it
confirmed, then apply it. Silently generalising a scoped instruction has cost more rework than any
layout bug in this system's history — it turns a four-card note into a fifty-card regression, and
the regression looks like progress until someone opens the file.

## Loop

Re-audit after each pass. Stop when the gate passes, or after 4 passes with improvement under 1.5
points per pass — at that point the remaining defects are structural and need a decision about
scope, not another pass.

Pass `--note "what this pass changed"` to `dscc.py audit` so the history line records the intent
alongside the number. In four passes' time that note is the difference between a trail you can read
and a column of totals.

Report each pass as a diff: score before → after, defects cleared, defects introduced. If a pass made
something worse, say so.
