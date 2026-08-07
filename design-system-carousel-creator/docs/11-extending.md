# 11 · Extending

The plugin is a set of files. Everything below is editing one of them.

---

## Layout

```
design-system-carousel-creator/
├── commands/         12 slash commands — the pipeline stages
├── agents/           5 subagents
├── docs/             this guide
├── skills/
│   ├── carousel-craft/            the design knowledge
│   │   ├── SKILL.md
│   │   ├── references/            mechanics · density-law · theming · anti-patterns · dc-format
│   │   └── assets/kernel.css      the primitive layer
│   ├── design-system-distillation/
│   └── quality-gate/
├── scripts/          the deterministic half — no Claude dependency
├── assets/
│   ├── runtime/      vendored support.js + image-slot.js
│   ├── canvas/       the canvas host + its embedded font
│   └── builder/      build.py template
└── schema/           JSON Schemas + the judged rubric + defaults
```

---

## A different artboard size

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py new "Square Set" --width 1080 --height 1080
```

The manifest carries it and every stage reads from there. To change the *default*, edit
`artboard` in [`schema/defaults.json`](../schema/defaults.json).

Check the type floors in `TYPE_FLOORS` in `scripts/dscc.py` if you go much smaller — they are
set by thumbnail legibility at 3.6× reduction on a 1080px board.

---

## A new layout mechanic

Mechanics are the six-axis vocabulary in [Concepts](02-concepts.md#3--uniqueness-is-defined-so-it-is-checkable).

1. Add the value to the relevant axis in
   [`schema/layout-plan.schema.json`](../schema/layout-plan.schema.json)
2. Describe it in
   [`references/mechanics.md`](../skills/carousel-craft/references/mechanics.md) — what it is
   *for* and how it fails, not just what it looks like
3. Add the primitive to `kernel.css` if it needs one

`uniq.py` reads the tuple generically, so distance and collision checking pick it up with no
code change.

**Adding a value widens the space; it does not raise the bar.** The distance threshold is what
prevents fifty near-identical cards, and that is a constant in `score.py`.

---

## A new deterministic check

Static (source-readable) checks go in `lint.py`; geometric ones in `measure.py`.

```python
# lint.py
def check_my_thing(html: str, card_html: str) -> list[dict]:
    """One paragraph on why this is checkable and what the legal fix is."""
    return [{"code": "MY_CODE", "severity": "P1", "detail": "…", "card": 3}]
```

Then wire it into `lint()`, and register it in `score.py`:

```python
LEGAL_FIX["MY_CODE"] = "the one correct fix -- not the cosmetic one"
DEFECT_DIM["MY_CODE"] = "discipline"
```

If it should cost per-card points, add it to the deduction list in `score()`.

Two rules worth keeping:

**Name the cause, not the symptom.** `UNDERWRITTEN`, not `SPACING`. The name determines which
fix people reach for.

**State the illegal fix.** Every check has a cosmetic workaround that clears it in a minute and
makes the work worse. Write it down in the `legal_fix` string.

---

## Tuning the gate

All thresholds are constants at the top of [`scripts/score.py`](../scripts/score.py):

```python
WEIGHTS = {"integrity": 20, "discipline": 15, "density": 20,
           "distinction": 15, "veracity": 10, "craft": 20}
GATE = {"total": 80, "min_card": 70, "density": 15, "distinction": 11}
COVERAGE_FLOOR = 0.40
COVERAGE_CEIL = 0.88
SLACK_FREE = 160
LEGAL_LICENSES = {"cover", "close", "single-figure", "media-led", "few-rows", "section-break"}
```

They are deliberately constants and not configuration. A gate you can lower from a config file
is a gate that gets lowered at 2am. If your house standard genuinely differs, change them here
and say so in your fork's documentation — the point is that the change is visible and applies
to every library, not tuned per run.

Calibration notes are in [`schema/calibration.json`](../schema/calibration.json).

---

## Constraint phrase lists

`CROSS_REF_PHRASES` and `ATTRIBUTION_PATTERNS` in [`scripts/lint.py`](../scripts/lint.py) are
plain lists of regexes. Add domain-specific ones there, or per-project via
`constraints.forbidden_patterns` in `project.json` — which needs no code change and travels
with the project.

Prefer the manifest for anything project-specific. Prefer the code for shapes that are wrong
everywhere.

---

## The canvas

Edit [`assets/canvas/canvas.html`](../assets/canvas/canvas.html), then re-install:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py canvas dist/
```

Bundle copies are regenerated on every scaffold, so edit the plugin's copy, never the bundle's.

Placeholders substituted at install: `__FONT_FACE__`, `__DOC_SRC__`, `__DOC_TITLE__`,
`__CARD_W__`, `__CARD_H__`, `__DEFAULT_DARK__`.

### A different UI font

Replace `assets/canvas/JetBrainsMono-latin.woff2.base64` with your own base64-encoded woff2 and
update `_font_face()` in `scaffold.py` plus `--ui-font` in the canvas CSS. Keep it embedded —
the reason is in [The canvas](06-canvas.md#typography). Update
[`FONT-LICENSE.md`](../assets/canvas/FONT-LICENSE.md) to match what you ship.

---

## The builder template

[`assets/builder/build.py.tmpl`](../assets/builder/build.py.tmpl) is what every project's
`build/build.py` starts as. Add house-specific helpers there and every future project inherits
them.

`emit_builder()` never overwrites an existing `build.py` — the emitted file gets filled in with
real composition, and clobbering that on a re-scaffold would be a far worse bug than the one it
prevents.

---

## The kernel

[`skills/carousel-craft/assets/kernel.css`](../skills/carousel-craft/assets/kernel.css) is
brand-agnostic and copied verbatim into every library.

If you edit it, keep the `dscc:kernel-begin` / `dscc:kernel-end` sentinels — the `OFF_SCALE`
check skips between them, because flagging a file you instruct people to copy verbatim is the
tool contradicting itself.

Brand-specific CSS belongs in `BRAND_CSS` in the project's builder, never here.

---

## The judged rubric

[`schema/rubric.json`](../schema/rubric.json) holds the anchors for the five Craft
sub-criteria — what a 5 vs a 3 vs a 1 looks like, with worked examples.

The critic must cite a card index and a visible reason for every deduction. Unanchored
deductions are discarded on merge, in `score()`. Keep that if you extend the rubric: a critic
that can deduct without evidence is a critic whose score means nothing.

---

## Zero-prompt defaults

[`schema/defaults.json`](../schema/defaults.json) is the answer to every question the pipeline
refuses to ask: artboard, card count, theme handling, surface distribution, media ratio,
grammar devices, type registers, taxonomy naming, structural formats.

Each entry carries a `rationale`. Keep that convention — a default without a stated reason is
indistinguishable from an arbitrary choice, and the next person will change it for equally
arbitrary reasons.

---

## Using the scripts standalone

Nothing under `scripts/` imports Claude anything. In CI:

```yaml
- run: pip install playwright && playwright install chromium
- run: python scripts/dscc.py audit --strict
```

Exit `0` on PASS. That independence is the point: a quality claim only the thing making the
claim can verify is not a quality claim.

---

## Renaming the plugin

The plugin name determines the command namespace (`/<plugin-name>:build`). To rename:

1. `.claude-plugin/plugin.json` → `name`, `displayName`
2. the directory itself
3. the marketplace entry's `name` and `source`
4. every `/<old-name>:` reference in `commands/` and `docs/`

`${CLAUDE_PLUGIN_ROOT}` handles script paths, so those need no change.
