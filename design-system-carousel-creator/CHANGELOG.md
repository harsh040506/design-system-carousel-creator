# Changelog

The version lives in one place, [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json), and the
marketplace entry mirrors it. Every scorecard and every `audit/history.jsonl` row records it as
`scorer_version`: totals produced by different scoring rules are not comparable, and the record says
which rules produced each one. `python scripts/dscc.py --version` prints it.

## 1.1.0

### Scoring changes — totals are not comparable with 1.0.0

- **`RAW_PX` now catches 10, 20, 100, 200 and 1000px.** The allow-list check stripped trailing
  `0`s, so those values read as `1` or `2` and passed. Libraries may show `RAW_PX` that was
  previously hidden.
- **`FLAT_SURFACES` costs 5 Distinction points** (enough to fail the Distinction ≥ 11 gate on its
  own); **`GROUND_CLUSTER` costs 1 per pair, capped at 2.** Both were previously listed but free.
- **`SLACK_REVIEW` (P2):** licensed bottom slack over 520px needs the critic's sign-off
  (`slack_signoff` in `critic.json`).
- **Veracity** reads a claim's `figure` field as brief text, and checks reuse per claim
  (`CLAIM_REUSE`).
- **`OFF_SCALE`** stylesheet values now reach the scorecard as one P2 entry, so they fail
  `--strict` as documented.
- The scorecard carries `raw_points` and `scorer_version`; an unscored Craft is described as
  scaled to 100, not as a 100-point total.
- **`INVENTED_FIGURE`** no longer fires on sentence punctuation: "In 2024, …" is the number 2024.
- **`UNDECLARED_VAR`** ignores `var(--x, fallback)` and counts `setProperty('--x')` as a
  declaration. The kernel gives `--on-photo-*`, `--motif-fill` and `--motif-radius` fallbacks, and
  the scaffold declares `--label-vis`, so builder-generated libraries no longer carry P0s they
  could not fix.
- **`WEB_CHROME`** now costs the card it is on (−8), as documented; `WEB_CHROME_COPY` reaches the
  scorecard.
- **Craft** is averaged over attributable critic rows; rows without an integer `index` are ignored
  instead of collapsing together.
- **`flush`** (full-bleed media) no longer counts as one of the five grounds.
- An audit whose selector matches nothing is reported as degraded instead of scoring the gallery
  as one clean card.

### Fixes

- Built libraries render **offline**: React 18.3.1 is bundled in `assets/runtime/vendor/` and
  mapped through `window.__resources`; `scaffold verify` checks for it. `--fonts none` drops the
  only remaining network request.
- The `©` attribution check matches `© 2024 Acme` and `(c) 2021`.
- Project names containing `"`, `#`, `:`, `?` and similar no longer crash `project new` or emit an
  unparseable `build.py`; folder and library filenames are sanitised, the display name is kept.
- The canvas escapes the project name for each context it is written into.
- The builder resolves the plugin at run time (`DSCC_PLUGIN_ROOT`, then `CLAUDE_PLUGIN_ROOT`),
  derives `data-mechanic` from the plan's axes, emits `g-<chrome>` ground classes, writes light
  tokens into `:root`, and emits the project's real artboard size.
- Kernel default artboard is 1080 × 1440, matching the project default; `img-slot` typo fixed.
- Preview server: no wildcard CORS; foreign `Host`/`Origin` on `/__dscc/` gets 403; no double
  reload after a rebuild.
- Five commands had invalid YAML in `argument-hint`, which silently dropped their metadata. All
  twelve are quoted.
- Commands write `design-system.json`, `content-brief.json` and `layout-plan.json` to `build/`,
  where the manifest, the builder and `dscc audit` look for them.
- `--fonts none` survives rebuilds: the emitted builder re-scaffolds with the same fonts choice.
- Theme values containing quotes (`"'Fraunces', serif"`) no longer break `applyTheme`.
- The builder maps legacy ground names (`plate`, `tinted`, `standard`) and `flush` to real
  classes, and `build.py --verify` exits non-zero when verification fails.
- `score.py` exits 1 on a gate FAIL and 2 when an input is missing.
- `adopt` without `--into` creates `<name> (project)` beside the folder instead of writing into
  it; `new --source DIR` freezes a whole folder instead of crashing.
- `slots fill --overwrite` puts each image in the slot it reports.
- `dscc audit --out` / `--rhythm` given explicitly win over the manifest; `preview` honours the
  manifest's `serve.open` and `serve.watch`.
- `scaffold init --system` with a missing file stops with an error instead of using placeholder
  tokens; a standalone builder lives in `build/` so it writes the library where it found it.
- Stale `card-*.png` are cleared before new shots; the report counts only renders it embedded.
- Smaller crash fixes: `info` with a null history total, `doctor` with a non-object `themes`,
  a non-object slot sidecar, `../` slot paths, bench references with the same name, and the
  canvas when browser storage is blocked.
- Agent and skill docs use the six named grounds throughout; display and headline floors match
  `doctor` (120px / 52px).

### Added

- `.claude-plugin/plugin.json` and a repository marketplace, so the plugin installs with
  `/plugin marketplace add`.
- `tests/test_regressions.py` (stdlib only).
- `dscc.py --version`.

## 1.0.0

Initial release.
