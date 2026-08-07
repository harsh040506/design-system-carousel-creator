---
description: Plan all layouts as a set, with collision checking, before building any card.
argument-hint: [--cards 50] [--brief content-brief.json] [--out layout-plan.json]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# /design-system-carousel-creator:plan

`$ARGUMENTS`

Load `carousel-craft` and read `references/mechanics.md`.

This stage exists because of one specific failure: building cards one at a time produces fifty
individually reasonable choices and a repetitive library. Each card looks fine. The set has three
Q&A slides that differ only in wording and four interchangeable 2×2 grids. You never see the set
while building it — you see it in a table.

So make the table first.

## Assign

For each card: a mechanic tuple, a narrative section, its claim ids, its planned row count, and its
fill/breathe intent.

Assign by **narrative position**, not by walking the mechanics catalogue in order — the latter
produces a library whose first ten cards are all monoliths.

## Declare intent honestly

`intent: "fill"` is the default and right for roughly 40 of 50. `intent: "breathe"` requires a
license from the list, and `few-rows` requires an actual row count ≤4 — the schema enforces that,
because a license that can be claimed freely stops meaning anything.

## Check the set

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/uniq.py layout-plan.json --out uniq.json
```

Resolve every collision **in the plan**. Cheapest first: enumerator → chrome → emphasis → partition.
Changing the words is not a resolution; the auditor compares tuples and so does the reader's eye.

Also clear `MIX_OFF` here. Hitting the media/plate/tinted targets after the cards exist means
rebuilding them.

Report the distribution table and the mean pairwise distance before moving on.
