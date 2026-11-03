---
description: Extract atomic, sourced claims from documents into a content brief.
argument-hint: "<source-doc...> [--cards 50] [--out build/content-brief.json]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# /design-system-carousel-creator:brief

Sources: `$ARGUMENTS`

## Accepted formats

The user may hand you `.md`, `.txt`, `.pdf`, `.docx`, `.doc`, or pasted text directly in the
conversation — any of these, mixed, in any combination.

| Format | How to read it |
|---|---|
| `.md` / `.txt` | Read tool directly |
| `.pdf` | Read tool directly (use `pages` for anything over 10 pages) |
| `.docx` | Read tool cannot parse this format. Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/extract_text.py FILE.docx --out FILE.txt`, then read the `.txt` output. It preserves heading levels and pulls table cells in reading order. |
| `.doc` (legacy binary) | Not parseable without external tools. Tell the user to re-save as `.docx` or paste the text. |
| pasted text | Already in the conversation — no extraction step needed. |

Do this extraction step **before** anything else. Silently skipping a `.docx` file because it "can't
be read" produces a brief that is missing a whole source with no record of the gap.

Read every source document **completely**. Not skimmed, not sampled — slides written from a partial
reading drift into generic filler by about card eight, and the drift is invisible until you read the
library end to end.

Produce `build/content-brief.json` against `${CLAUDE_PLUGIN_ROOT}/schema/content-brief.schema.json`.

## What a claim is

One assertion, with the source span it came from, typed as one of: `stat`, `definition`, `contrast`,
`quote`, `process`, `milestone`, `objection`, `consequence`, `example`, `principle`.

If a claim needs the word "and" to hold together, it is two claims. Split it. Atomic claims are what
make a card's content a *selection* rather than a paraphrase.

## Over-extract on purpose

Target **3× the card count** — 150 claims for a 50-card library. This is not wasted effort; it is
the mechanism that resolves under-written cards later. When the auditor reports `UNDERWRITTEN` on
card 9, the fix is to pull a real row from the unused pool. Without a surplus, the only available
fix is spacing, which is not a fix.

## Record every number

Any claim carrying a figure sets `figure`. The veracity check compares numbers on the finished
slides against this set, and a number that appears on a slide but not in the brief is a P0 defect. A
beautiful slide containing an unsourceable statistic is worse than an ugly one.

## Then map the arc

Assign claims to the ten narrative sections (hook → ground → tension → method → proof → voice →
depth → objection → application → structure). Weight them 1–5: a weight-5 claim earns a whole card,
a weight-2 claim is a row in someone else's.

Report: claim count by type, coverage of each source, and anything in the sources you judged
unusable and why.
