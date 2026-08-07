# 3 · The pipeline

```
                       :new  ──►  <Project>/  + project.json
                          │        inputs frozen, constraints declared
   design system          │            source documents
   (md · css · pdf)       │            (md · txt · pdf · docx)
          │               │                   │
      :distill            │               :brief
          │               │                   │
 build/design-system.json │      build/content-brief.json
   · locked scales        │        · atomic claims
   · role-mapped palette  │        · provenance spans
   · motif definition     │        · narrative arc
          └───────────────┼───────────────────┘
                          ▼
                       :plan
                          │
               build/layout-plan.json
                · 50 mechanic tuples, collision-checked
                · claim → slide assignment
                · fill/breathe intent, licensed
                          ▼
                      :build
                          │
            build/build.py  ──►  dist/<Name>.dc.html
                                  + runtime · canvas · slot state
                          ▼
              ┌────────  :audit  ────────┐
              │                          │
        deterministic              design-critic
   (lint · measure · uniq)        (rendered PNGs)
              └──────── score ───────────┘
                          │
              audit/scorecard.json → history.jsonl
                          │
               ≥80? ──no──►  :refine  ──┐
                  │        (reads history)│
                 yes                      └── max 4 passes
                  ▼
               :ship  ──►  :preview
```

Commands are shown short (`:distill`) for readability. The full form is
`/design-system-carousel-creator:distill`.

`:run` executes all of it. The stages are separately invocable because in practice you re-run
`plan → build → audit` a dozen times and `distill` once.

---

## 0 · `:new` — create the project

**Run this first, always.** Nothing else should write a file before it exists.

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py new "Acme Templates" \
  --system DESIGN.md --source whitepaper.pdf --source notes.md \
  --width 1080 --height 1440 --cards 50 --cols 5 \
  --independent --no-source
```

The last two flags are the important half. Any constraint stated in prose is captured here or
it is not enforced at all — see [Constraints](07-constraints.md).

**Writes:** the project tree, `project.json`, a generated `README.md`, and the bundle skeleton
(`support.js`, `image-slot.js`, `canvas.html`, `.image-slots.state.json`).

---

## 1 · `:distill` — brand document → token contract

Reads whatever shape the brand is in — a markdown style guide, a `.css` file of custom
properties, a Tailwind `@theme` block, a PDF brand book, pasted prose — and extracts the same
seven categories regardless: colour roles, type scale, spacing, radii, motif, legality rules,
anti-instructions.

**Writes:** `build/design-system.json`

**Validate:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py doctor --system build/design-system.json
```

This checks that every required token exists, that no two roles collapsed to the same value,
and that the type ramp clears the floors for a 1080px artboard (`--t-display` ≥ 120px is the
one people trip on — a display size that works on a website is too small on an artboard viewed
as a thumbnail).

It also reports **coverage**: what fraction came from your source versus derivation. Tell the
user that number. They deserve to know how much of the result is actually their brand.

**Re-run when:** the brand changes. Roughly once per project.

---

## 2 · `:brief` — sources → atomic claims

Reads every source document **in full** and extracts atomic claims with provenance spans.

**Over-extract deliberately: aim for 3× the card count.** The surplus is what resolves
under-written cards later without inventing anything. A brief with exactly fifty claims for
fifty cards leaves the refiner with no legal move when a card comes up sparse.

**Writes:** `build/content-brief.json`

```json
{
  "claims": [
    { "id": "c001", "type": "fact", "text": "…", "source": "s1", "span": [1204, 1288] },
    { "id": "c002", "type": "figure", "text": "…", "figure": "7,500", "source": "s1" }
  ],
  "arc": { "opening": [1, 5], "problem": [6, 14] },
  "unused_pool": ["c101", "c102"]
}
```

`.docx` is routed through `scripts/extract_text.py` first (stdlib zip/XML, no dependency),
which preserves heading levels and pulls table cells in reading order. Legacy binary `.doc` is
not parseable — re-save as `.docx` or paste the text.

**Re-run when:** sources change, or the claim pool runs dry during refinement.

---

## 3 · `:plan` — all fifty layouts, as a set

The stage that prevents the failure modes. Assigns each card a mechanic tuple, its claims, and
its fill/breathe intent — **before any card is built.**

**Writes:** `build/layout-plan.json`

**Check it before building anything:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/uniq.py build/layout-plan.json --out uniq.json
```

Resolve every `DUP_LAYOUT` and `MIX_OFF` **in the plan**. Fixing distinction after the cards
exist means rebuilding them, which is why this check runs on a JSON file rather than on HTML.

**Re-run when:** distinction scores poorly, or the claim assignment needs rebalancing.

---

## 4 · `:build` — plan → HTML

Scaffold once, then write the card composition into `build/build.py`.

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py init "dist/Acme Templates.dc.html" \
  --system build/design-system.json --title "Acme Templates" --cols 5
```

**Writes:** the `.dc.html` envelope, both runtime files, `canvas.html`, the slot sidecar, and
`build/build.py`.

Then compose cards in the builder — never by hand-editing the HTML. See
[Authoring cards](08-authoring.md).

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py build          # re-run the generator
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py verify "dist/Acme Templates.dc.html"
```

`verify` checks all five envelope parts, both runtime files, and every `var(--x)` resolving to
something declared or set in `applyTheme`. **Non-zero exit means fix before auditing** —
measuring a library that cannot render produces confident, precise, meaningless numbers.

Build in batches of ten, running `lint.py` after each. An unbalanced `<div>` found at card 12
costs a minute; found at card 50 it costs an hour of bisecting.

---

## 5 · `:audit` — measure, score, gate

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py audit
```

Zero arguments inside a project. Runs lint → measure → uniq → score, prints the scorecard, and
appends one line to `audit/history.jsonl`.

**Writes:** `audit/{lint,measure,uniq,scorecard}.json`, `shots/*.png`, `audit/history.jsonl`

For the judged twenty points, run the `design-critic` agent over `shots/` and re-score with
`--critic audit/critic.json`. Without it Craft is unscored, the total is out of 80, and the
scorecard carries a `NO_CRITIC` defect saying so.

`--strict` promotes every accepted-but-unresolved P2 into a gate failure.

---

## 6 · `:refine` — fix by cause, batched

While the gate fails and passes < 4: fix defects **batched by class**, then re-audit.

Walking card by card gives each card its own local judgement, which is how drift gets into a
library. Fixing every `UNDERWRITTEN` in one pass means one decision applied consistently.

Order: all P0 first, then P1 by dimension weight, then P2.

**Read `audit/history.jsonl` before deciding what to try.** If a defect class has survived two
passes with the total flat, the fix you are reaching for is not working and the problem is
upstream — a thin claim pool or a weak layout plan — not something a third editing pass
reaches.

Stop after 4 passes, or when improvement drops below 1.5 points per pass.

---

## 7 · `:bench` — optional comparison

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py bench LIBRARY.html OTHER1.html OTHER2.html
```

Runs the identical auditor over a candidate and any comparison libraries you supply, then
prints one table. **Entirely optional** — the gate is self-contained and needs no reference.

The point of the table is that it can report a loss. Two caveats print with every run:
Veracity is unscoreable without a brief, and a library with no project manifest is audited in
degraded mode with unlicensed slack scored *in its favour* — so your candidate is held to the
stricter standard, not the other way round.

---

## 8 · `:ship` — verify, record, hand over

Rebuild, re-audit, check the gate honestly, write `RELEASE.md`.

The known-limitations section is what makes that document worth anything. A release record
listing only successes is marketing. Include: every accepted defect with its reason, how many
image slots ship filled, and what the total is out of.

---

## 9 · `:preview` — look at it

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

The run is not finished until the library is on screen. See [The canvas](06-canvas.md).

---

## 10 · `:report` — one page for people who won't read JSON

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py report
```

**Writes:** `audit/report.html` — scorecard, dimension bars, the score trail across every audit
the project has had, per-card defects with legal fixes, inlined thumbnails, reproduce table.
Self-contained; email it.

---

## Adopting existing work

If a library was built into a flat folder before you had a project:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py adopt OLD_DIR \
  --name "Acme Templates" --into projects/acme --independent --no-source
```

Moves artifacts into the layout, repoints the builder's paths, seeds audit history from any
existing scorecard, installs the canvas. It **copies** — the original is untouched so you can
verify before deleting it.
