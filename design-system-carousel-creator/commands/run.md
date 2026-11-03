---
description: Run the whole pipeline — design system + sources in, scored template library out.
argument-hint: "<design-system.md> <source-doc...> [--cards 50] [--out DIR]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill, Agent
---

# /design-system-carousel-creator:run — end to end

Arguments: `$ARGUMENTS`

Run every stage in order. Each writes a file; each is separately re-runnable. Do **not** skip ahead
to building — the three planning artifacts are what prevent the failure modes, and building without
them means rediscovering all of them.

## Run this without asking questions

**"Here is a design system and some content — build me a library" is a complete instruction.** Card
count, artboard size, taxonomy, tone, theme handling, surface set, media ratio: all of it is decided
in [`schema/defaults.json`](../schema/defaults.json). Read that file, take the decisions, build.
Report the choices at the end so the user can redirect anything they disagree with — do not front-load
questions whose answers are nearly always the same.

Three situations genuinely warrant stopping: the sources contradict each other on a fact that would
appear on a card; the brand supplies no colour information at all; the content is plainly for a
different medium. Everything else — decide and proceed.

Before planning, read `carousel-craft/references/house-standard.md`. It is the quality bar this
command exists to hit, and it names the three properties generated libraries almost always miss:
no consistent visual grammar, a light/dark pair instead of a named surface set, and too few formats
with names too vague to be specifications.

## 0 · Preflight

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py doctor
```

Stop if it reports NOT READY. Load the `carousel-craft` skill now; you will need it throughout.

## 0b · Create the project — do this before anything writes a file

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/project.py new "Brand Templates" \
  --system DESIGN.md --source book.pdf [--independent] [--no-source]
```

Every artifact from here lands inside that folder. Nothing goes in the cwd. See
[`/design-system-carousel-creator:new`](new.md) — the important half of that command is the last two flags: **any constraint
the user stated in prose is captured here or it is not enforced at all.** "Each card must stand
alone" and "don't mention the source" are `--independent` and `--no-source`, and they become
deterministic defect codes on every audit rather than something you remember to check.

Then work from inside the project directory. Every command below finds `project.json` by walking up.

## 1 · Distill

Load `design-system-distillation`. Read the brand input. Produce `build/design-system.json` and validate:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py doctor --system build/design-system.json
```

Report the coverage figure to the user — what proportion came from their source versus derivation.
They deserve to know how much of the result is their brand.

## 2 · Brief

Read every source document **in full**. Extract atomic claims with provenance into
`build/content-brief.json`. Over-extract: aim for 3× the card count. The surplus is what resolves
under-written cards later without inventing anything.

If the sources are long, dispatch `content-strategist` — but only if the user asked for subagents or
the volume genuinely warrants it. Otherwise read them yourself.

## 3 · Plan

Produce `build/layout-plan.json`: one mechanic tuple per card, claims assigned, intent declared. Check it
before building anything:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/uniq.py build/layout-plan.json --out uniq.json
```

Resolve every `DUP_LAYOUT` and `MIX_OFF` **in the plan**. Fixing distinction after the cards exist
means rebuilding them.

## 4 · Build

Scaffold once — this writes the `.dc.html` envelope, installs the runtime **and the canvas host**,
seeds the slot sidecar, and emits `build/build.py`:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py init "dist/Brand Template Library.dc.html" \
  --system build/design-system.json --title "…" --cols 5
```

Then **write the card composition into `build/build.py`, not into the HTML.** The generator is the
source; the `.dc.html` is its output. A 121 KB hand-edited HTML file with no source is a liability;
the same file with a generator beside it is an asset — the type ramp is nine numbers in one place and
a fix to a shared row shape reaches all fifty cards instead of the eleven you remembered to edit.

The emitted builder already carries the two structural lessons and its comments explain both. Do not
undo either:

- **It re-scaffolds from scratch every run.** Never patch the document in place. The natural shape,
  `if "BRAND LAYER" not in doc: doc = insert_css(doc)`, is never true after the first successful
  build, so every later CSS edit silently does not reach the output — a failure that looks exactly
  like the edit not working.
- **Ground tokens go into `:root` before the CSS layer is inserted.** Inserting CSS first and then
  guarding the token injection with `if "--tok" not in doc` matches the CSS layer's own `var(--tok)`
  uses, so the tokens are never written and you get a screen of `UNDECLARED_VAR` P0s.

Every card carries `data-card`, `data-layout`, `data-mechanic`, `data-intent`, `data-license` and
`data-claim` so the auditor can check the build against the plan.

Build in batches of ten, running `lint.py` after each batch. An unbalanced `<div>` found at card 12
costs a minute; found at card 50 it costs an hour.

When all cards are in:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py verify "dist/Brand Template Library.dc.html"
```

Non-zero exit means the envelope or the runtime is broken. Fix before auditing — measuring a library
that cannot render produces confident, precise, meaningless numbers.

## 5 · Audit

Inside a project this takes no arguments. The manifest knows where the system, brief, plan and shots
are, and wiring them by hand is five chances to audit against the wrong brief:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py audit
```

Every run appends to `audit/history.jsonl`, so the refine trail is a file rather than a memory.

Then run the `design-critic` agent over `shots/` for the Craft dimension, and re-score with
`--critic audit/critic.json`. **Do not skip this and then report a total as if it were out of 100.**
Without the critic, Craft's 20 points are unscored and the scorecard says so in its own defect list;
repeat that in your report rather than rounding it away.

## 6 · Refine

While the gate fails and passes < 4: fix defects **batched by class**, re-audit. Obey the legal-fix
lists — `UNDERWRITTEN` and `SPARSE` are resolved by adding real content from the unused claim pool,
never by adjusting spacing. That constraint is the entire reason this pipeline produces different
work than a one-shot generation would.

## 7 · Optional: benchmark against a comparison library

The gate in step 6 is self-contained — nothing in it depends on any file besides the library being
built, so a fresh run produces the same quality bar whether or not any comparison material exists.
This step only applies if the user has supplied one or more libraries they want the candidate
measured against:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py bench LIBRARY.html COMPARISON1.html COMPARISON2.html
```

Compare on the shared 70 points. A candidate that clears 80/100 but loses to a comparison library on
Density or Distinction has cleared the floor without matching the specific bar the user cares about
— say so, and consider another `/design-system-carousel-creator:refine` pass or a return to `/design-system-carousel-creator:plan` if the gap is
structural (thin claim pool, weak layout variety) rather than fixable by editing existing cards.

## 8 · Preview — the run is not finished until it is on screen

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

Serves `dist/` and opens the canvas: pan, zoom, theme toggle, card index, audit overlay. Look at the
library before you describe it. Some defects — a motif eating the type on one ground, a rule running
past its content, a closing note reading as another row — are invisible in every deterministic number
and obvious the moment you actually see the card.

## 9 · Report

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py report
```

Then give the user, in prose: the scorecard, what changed across refine passes (read
`audit/history.jsonl`, do not reconstruct it), the constraints that were checked and whether they
came back clean, the benchmark table if one was run with its caveats, and an honest list of anything
still failing and why.

State plainly which dimensions were **not** scored and what the total is therefore out of. If
something was left undone, say so rather than rounding it up to complete.
