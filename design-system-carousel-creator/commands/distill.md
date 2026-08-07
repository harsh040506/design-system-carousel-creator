---
description: Turn a brand design system into a locked, machine-checkable token contract.
argument-hint: <design-system.md|url|paste> [--out design-system.json]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# /design-system-carousel-creator:distill

Input: `$ARGUMENTS`

## Accepted formats

The brand input arrives as whatever the user has on hand:

| Format | How to read it |
|---|---|
| `.md` / `.txt` (style guide, brand book prose) | Read tool directly |
| `.css` (custom properties, a `:root` block) | Read tool directly — parse the declarations as the token source |
| Tailwind config / `@theme` block (`.js`, `.ts`, `.css`) | Read tool directly — map the theme keys onto the seven extractions |
| `.docx` | Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/extract_text.py FILE.docx --out FILE.txt` first, then read the output |
| `.pdf` (brand book export) | Read tool directly |
| pasted markdown / prose / CSS | Already in the conversation |
| a URL | Only if the user provided it directly — never fetch a design system from a guessed URL |

Whatever the shape, the extraction target is always the same seven categories (see below) — a CSS
file just means colour and type roles are read from declarations instead of prose.

Load the `design-system-distillation` skill and follow it. The seven extractions are colour roles,
nine type steps, seven spacing values, three radii, the motif, the legality rules, and the
anti-instructions.

Three things that go wrong most often, so check them explicitly:

1. **Type scaled for the web.** Brand documents give web sizes. A 1080px artboard needs roughly
   2.2–2.6× those. Getting this wrong is the single most common reason generated slides read as
   reports — the type is technically on-brand and visually far too small. The floors in the skill
   are hard floors.

2. **Dark mode derived by filtering.** Light and dark are two complete role maps. Inverting lightness
   produces muddy, over-saturated results that look fine in isolation and wrong beside the light
   version.

3. **No motif.** If the brand has one, find it. If it doesn't, derive one and *say* that you derived
   it. A library without a recurring graphic reads as fifty unrelated cards no matter how consistent
   the tokens are.

Write `design-system.json` against `${CLAUDE_PLUGIN_ROOT}/schema/design-system.schema.json`, emit
the matching `:root` CSS blocks in the same pass so the two cannot disagree, then validate:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py doctor --system design-system.json
```

Report the `coverage` figure and list every derived value with its rationale. A system at 40%
coverage still produces a good library — the user just deserves to know which half is theirs.
