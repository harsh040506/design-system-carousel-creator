---
description: Render the whole project as one self-contained HTML report.
argument-hint: [--no-open]
allowed-tools: Bash, Read
---

# /design-system-carousel-creator:report

`$ARGUMENTS`

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py report
```

Writes `audit/report.html` — scorecard, dimension bars, the score trail across every audit the
project has ever had, the per-card table with defects and their legal fixes, the constraints that
were checked, thumbnails of all fifty renders, and the exact commands to reproduce it.

Self-contained: thumbnails are inlined as data URIs and nothing in the page phones anywhere, so it
can be emailed or dropped in a folder.

## What it is for

"99.6/100, gate PASS" is a sentence. The interesting part of a scorecard is always the ten lines
under it: which dimension is carrying the total, which card is weakest, what was accepted rather
than fixed, and what was never scored at all. Those live in JSON that nobody outside this session is
going to read.

The report prints the unflattering parts at the same size as the flattering ones — the unscored
dimensions in the header, the P2s that were accepted, the missing artifacts in the reproduce table.
A report listing only successes is marketing.

## Read it before shipping

If the trail is flat across four refine passes, the refinements are not working and the problem is
upstream — a thin claim pool or a weak layout plan — not something another editing pass will fix.
Say that rather than running a fifth.
