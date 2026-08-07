---
description: Optionally compare a library against any comparison libraries you supply, using the identical auditor.
argument-hint: <candidate.html> <comparison.html...>
allowed-tools: Read, Bash, Glob, Skill
---

# /design-system-carousel-creator:bench

`$ARGUMENTS`

**This step is entirely optional and requires nothing from anyone else's work.** The quality gate
(`/design-system-carousel-creator:audit`) is self-contained and produces the same bar with zero comparison files present. Use
this command only when the user has specific libraries in hand — theirs or anyone else's — that they
want a candidate measured against.

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py bench CANDIDATE.html COMPARISON1.html COMPARISON2.html ...
```

This is what turns "better" into a number. The same deterministic auditor runs over every library;
nothing about the candidate gets special handling.

## Always report the caveats with the numbers

The script prints them, and you must not drop them when summarising:

1. **Veracity is unscoreable for foreign libraries** — they have no content brief. The comparison is
   made on the 70 deterministic points all libraries share.
2. **Foreign libraries run in degraded mode** — no manifest, so the artboard is auto-detected and
   intent licensing cannot be read. Unlicensed slack is scored *in their favour*. The candidate is
   held to the stricter standard.
3. **Distinction is capped at 60%** for libraries without `data-mechanic` markup, because tuple
   collisions cannot be checked on them at all.

A benchmark that hides its caveats is worthless. If the candidate only wins because the rules
differ, say that — the point is to know whether the work is better, not to produce a favourable
table.

## Use it to calibrate, not just to celebrate

Every threshold in `schema/calibration.json` is derived from a benchmark run. When a reference
library scores impossibly well or badly on a metric, that is usually a bug in the harness, not a
discovery about the reference. Two such bugs have been found exactly this way — a 100% ink-coverage
reading that turned out to be the card's background surface counted as content, and a universal
"crowded" verdict that turned out to be measuring to the footer element instead of the footer rule.

If you change a threshold, update `calibration.json` with the measurement that justifies it. A
threshold nobody can trace back to a measurement is a preference wearing a number's clothes.
