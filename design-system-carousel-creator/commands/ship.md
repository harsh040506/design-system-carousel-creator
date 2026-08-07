---
description: Verify the gate, version the library, and write the release record.
argument-hint: <library.html> [--version 1.0.0]
allowed-tools: Read, Write, Edit, Bash, Glob
---

# /design-system-carousel-creator:ship

`$ARGUMENTS`

## 1 · Rebuild, then re-audit — do not trust the last run

Refine passes edit the builder; the document and the scorecard on disk may both describe an earlier
state.

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py build
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py verify "dist/<Name>.dc.html"
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py audit --note "ship candidate"
```

## 2 · Check the gate honestly

```
total >= 80  AND  min card >= 70  AND  zero P0  AND  density >= 15  AND  distinction >= 11
AND  every declared constraint clean
```

The constraint clause is not a formality. If the project declares `independent_cards` or
`no_source_attribution`, a single `CROSS_REFERENCE` or `SOURCE_LEAK` fails the gate whatever the
total says — the user asked for something binary and it is either true of the library or it is not.

If it fails, **do not ship and do not soften the report**. Say which condition failed, by how much,
and what it would take. Reporting a failing library as shipped is a worse outcome than shipping
late — and if Craft was never scored, the total is out of 80 and must be described that way.

## 2b · Optional: compare against a library you consider best-in-class

The gate in step 2 is self-contained — its thresholds are fixed constants calibrated once during
development, not fetched from any file at run time, so a library can pass it with zero comparison
material present. This step is for when *you* have a specific bar in mind and want the candidate
held to it explicitly.

If you have one or more comparison libraries on hand, run it before shipping:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py bench LIBRARY.html COMPARISON1.html COMPARISON2.html
```

On the **shared 70 deterministic points**, look for where the candidate is ahead and where it is
behind. Discipline (token conformance, one locked type ramp) is usually where a creator-built library
pulls ahead concretely — most hand-built libraries don't lock a type ramp, so a candidate carrying
40+ distinct computed font sizes hasn't delivered the standardization this pipeline exists to
enforce, even if its total clears 80.

If the candidate loses to a comparison library on a shared dimension, **that is not a caveat to
mention in passing — it is the finding.** Report it as plainly as a passing gate: which dimension, by
how much, against which file, and whether `/design-system-carousel-creator:refine` can close it or whether it's a
planning-stage gap (weak claim inventory, thin layout plan) that needs another pass upstream of the
audit.

Craft (the judged 20 points) is where the deterministic auditor can't see at all — run
`design-critic` before calling a library truly best-in-class, not just before calling it
gate-passing.

## 3 · Write the release record

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py report      # audit/report.html
```

Then `RELEASE.md` at the project root:

- version, date, source design system and its coverage figure, source documents
- final scorecard: total, all six dimensions, weakest card, **and what the total is out of**
- the constraints declared and their verdict
- benchmark table against any comparison libraries used, caveats included (omit if none — it is optional)
- refine history read from `audit/history.jsonl` — score per pass, defects cleared, defects introduced
- **known limitations** — every defect consciously accepted, with the reason
- image slots: how many ship filled, how many described (`slots.py audit` gives the number)
- how to reproduce: the exact commands, in order

The known-limitations section is the part that makes this document worth anything. A release record
listing only successes is marketing.

Do not reconstruct the refine history from memory. It is a file.

## 4 · The inputs are already frozen

`:new` copied the design system and every source document into `inputs/` at creation, and
`build/` holds the three artifacts. Confirm they are all present — `dscc.py info` prints the wiring
— rather than copying them now. In six months nobody will remember which brief produced which slides,
which is why this happens at the start rather than at the end.

## 5 · Hand over the bundle

`dist/` is the deliverable, whole: the `.dc.html`, both runtime files, `canvas.html`, the slot
sidecar, and any fonts or logos. Nothing in it reaches outside itself. Zip that directory.

Tell the recipient it needs a server, and give them the one line that starts it:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

Over `file://` the browser gives the iframe an opaque origin and the theme bridge is blocked. That
is a browser rule, not a bug in the bundle, and the canvas says so in a banner if it happens.

## 6 · Tell the user what they have

Total, gate status, what the total is out of and which dimensions were not scored, what is genuinely
strong, what is accepted-but-imperfect, and what would need doing to move it further. Plainly — no
hedging on the good parts, no rounding up the bad ones.
