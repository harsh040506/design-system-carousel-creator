---
description: Create an isolated project — one folder holding every artifact for one library.
argument-hint: "<Name>" [--system DESIGN.md] [--source doc.pdf] [--independent] [--no-source]
allowed-tools: Read, Write, Bash, Glob
---

# /design-system-carousel-creator:new

`$ARGUMENTS`

**Run this first, always.** A run is a project, not a directory.

Writing `design-system.json`, `content-brief.json`, `layout-plan.json` and `shots/` into whatever
directory you happen to be standing in means a second library built in the same folder silently eats
the first. For a tool meant to be run many times that is the most serious defect there is, and
nothing about running it warns you.

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/project.py new "Brand Templates" \
  --system DESIGN.md --source book.pdf --source notes.md \
  --width 1080 --height 1440 --cards 50 --cols 5
```

Creates:

```
Brand Templates/
├── project.json     the manifest — identity, wiring, constraints, pipeline state
├── README.md        how to rebuild and how to preview, generated
├── inputs/          FROZEN copies of the design system and every source document
├── build/           design-system.json · content-brief.json · layout-plan.json · build.py
├── dist/            the bundle: .dc.html, runtime, canvas.html, slot state
├── audit/           scorecard · lint · measure · uniq · history.jsonl
├── shots/           per-card PNGs
└── RELEASE.md       written by /design-system-carousel-creator:ship
```

`inputs/` is frozen at creation, before anything can drift — not copied later as a ship-time
reminder. A step you have to remember at the end is a step that eventually does not happen.

Every later stage reads its wiring from `project.json`, which is why `/design-system-carousel-creator:audit` takes no
arguments. Wiring five paths by hand on every invocation is five chances to audit a library against
the wrong brief.

## Capture the user's constraints here, not in your head

This is the step where prose becomes enforceable. If the user said anything of the shape "each card
must stand alone" or "don't mention where this came from", set it now:

| They said | Pass | What it becomes |
|---|---|---|
| "each page individual, no page depends on another" | `--independent` | `CROSS_REFERENCE` (P1) on every audit |
| "it should not mention the source" | `--no-source` | `SOURCE_LEAK` (P0), plus attribution patterns |
| "never say <X>" | `--forbid "X"` (repeatable) | literal, case-insensitive, checked in cards **and** chrome |

`--no-source` also seeds the forbidden list from the source filenames, because a title removed from
every card walks straight back in through a footer or the gallery header.

A constraint that only a careful human enforces is not a constraint — someone eventually reviews a
library at 2am, skips the manual check, and ships the leak. Set it here and it is checked every time.

## Then, in order

```
/design-system-carousel-creator:distill   → build/design-system.json
/design-system-carousel-creator:brief     → build/content-brief.json
/design-system-carousel-creator:plan      → build/layout-plan.json
/design-system-carousel-creator:build     → dist/<Name>.dc.html  (via build/build.py)
/design-system-carousel-creator:audit     → audit/scorecard.json  (zero arguments)
/design-system-carousel-creator:preview   → serves dist/, opens the canvas
```

`dscc.py info` at any point prints what is done, what is next, and the audit trail.

## An existing working directory

If a library was built by hand into a flat folder before this project layout existed, don't rebuild
it — adopt it:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/project.py adopt OLD_DIR \
  --name "Brand Templates" --into projects/brand-templates --independent --no-source
```

`adopt` moves the artifacts into the layout, repoints the builder's paths, seeds the audit history
from any existing scorecard, and installs the canvas. It **copies** — the original is left untouched
so you can verify before deleting it.
