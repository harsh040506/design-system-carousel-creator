# 5 · CLI reference

Everything under `scripts/` runs without Claude Code. Put it in CI, put it in a Makefile, point
it at a library someone else built by hand.

That independence is deliberate: **a quality claim only the thing making the claim can verify
is not a quality claim.** The knowledge in `skills/` has no dependency on these scripts, and
the scripts have no dependency on the knowledge. Either half is useful alone.

```bash
DSCC=${CLAUDE_PLUGIN_ROOT}/scripts        # or the plugin's scripts/ directory
```

---

## `dscc.py` — the main entry point

```
python dscc.py <command> [options]
```

| Command | |
|---|---|
| `new` | create an isolated project |
| `list` | every project under a root |
| `info` | this project's wiring, state and audit history |
| `adopt` | pull a flat working directory into a project |
| `set` | set a dotted key in `project.json` |
| `doctor` | check the toolchain, validate a design system |
| `build` | run the project's builder |
| `audit` | lint + measure + uniq + score |
| `preview` | serve the bundle, open the canvas |
| `serve` | alias for `preview --no-open` |
| `report` | render the project as one HTML page |
| `slots` | list / fill / audit image slots |
| `bench` | compare a candidate against libraries you supply |
| `shots` | render per-card PNGs |

### `doctor`

```bash
python dscc.py doctor
python dscc.py doctor --system build/design-system.json
```

Toolchain first (Python, Playwright, Chromium launchable, `kernel.css` present), then — if
given a system — token completeness, type-scale floors, and collapsed colour roles.

`--system` wants the **distilled JSON artifact**, not your brand markdown. Pointing it at
`DESIGN.md` tells you so rather than throwing a parse error.

Exit code `0` = READY.

### `audit`

```bash
python dscc.py audit                          # inside a project: zero arguments
python dscc.py audit LIBRARY.dc.html          # anywhere
```

| Flag | Default | |
|---|---|---|
| `--project DIR` | walk up | which project to read wiring from |
| `--out DIR` | `audit/` | where the four JSON artifacts land |
| `--system` `--brief` `--plan` `--critic` | from manifest | override individually |
| `--shots DIR` | `shots/` | per-card PNG output |
| `--selector` | `.frame` | artboard selector |
| `--auto` | off | auto-detect artboards (degraded mode) |
| `--rhythm N` | from manifest | the density reference unit |
| `--strict` | off | every P2 becomes a gate failure |
| `--note "…"` | — | recorded in `history.jsonl` |
| `--top N` | 8 | weakest cards to table |

Exit code `0` = gate PASS.

### `preview` / `serve`

```bash
python dscc.py preview                        # opens the browser
python dscc.py preview --watch                # rebuild + live reload
python dscc.py serve --port 8080 --quiet      # headless / CI
```

| Flag | |
|---|---|
| `--dir DIR` | serve any bundle instead of the project's `dist/` |
| `--port N` | preferred port; walks upward if taken |
| `--page NAME` | default `canvas.html` |
| `--no-open` | do not launch a browser |
| `--watch` | re-run `build/build.py` on change, push reload |
| `--quiet` | suppress request logging |

Binds `127.0.0.1` only. Dies with the process.

### `bench`

```bash
python dscc.py bench CANDIDATE.html OTHER1.html OTHER2.html --out bench-out
```

Identical auditor over all of them, one table, caveats printed every run.

### `shots`

```bash
python dscc.py shots LIBRARY.dc.html shots/ --clean
```

---

## `project.py` — project management

```bash
python project.py new "Acme Templates" --system DESIGN.md --source doc.pdf \
  --independent --no-source --forbid "Internal Only"
python project.py list [ROOT]
python project.py info [DIR]
python project.py adopt OLD_DIR --name "Acme" --into projects/acme
python project.py set serve.port 5000
python project.py set constraints.forbidden_terms '["Acme Confidential"]'
```

`set` takes a dotted path and infers the type — `true`/`false` → boolean, digits → number,
`[`/`{` → JSON, everything else → string.

---

## `scaffold.py` — envelope, runtime, canvas, builder

```bash
python scaffold.py init "dist/Acme.dc.html" --system build/design-system.json \
  --title "Acme Templates" --cols 5 [--fonts-dir ./fonts] [--logos-dir ./logos]
python scaffold.py verify "dist/Acme.dc.html" [--json]
python scaffold.py runtime dist/                  # refresh support.js + image-slot.js
python scaffold.py canvas dist/ [--document X.dc.html]
python scaffold.py builder "dist/Acme.dc.html"    # emit build/build.py
python scaffold.py assets dist/ --fonts ./fonts --logos ./logos
```

`init` writes the five-part `.dc.html` envelope and installs everything the bundle needs:
both runtime files, the canvas host with its font embedded, the slot sidecar, and the builder.

`verify` checks the envelope, the runtime (presence, size, header), every `var(--x)` resolving
to something declared or set in `applyTheme`, and every `./relative` reference resolving to a
real file. That last one matters most and is easiest to skip — a missing `./fonts/Foo.otf`
raises no error anywhere, the browser silently falls back, and the whole library renders in the
wrong typeface. It looks like a design problem, not a missing file.

`--json` for CI.

---

## `lint.py` — static source analysis

```bash
python lint.py LIBRARY.dc.html --out lint.json \
  [--system build/design-system.json] [--project DIR] [--constraints FILE]
```

Milliseconds, no browser. Tag balance, raw px/hex, inline `font-size`, undeclared custom
properties, web chrome, off-scale values, theme-token coverage, and any declared constraints.

Finds `project.json` by walking up, so constraints are enforced without being passed.

Exit `1` on any P0.

## `measure.py` — the geometry harness

```bash
python measure.py LIBRARY.dc.html --out measure.json [--shots DIR] [--rhythm 64]
```

Playwright + Chromium. Overflow, text collisions, ink coverage (morphological closing), row
gaps, bottom slack, distinct font sizes, distinct gaps. This is the half you cannot fake by
reading source.

## `uniq.py` — layout collision + distance

```bash
python uniq.py build/layout-plan.json --out uniq.json
python uniq.py LIBRARY.dc.html --out uniq.json      # reads data-mechanic
```

Exact tuple collisions, mean pairwise Hamming distance, partition distribution, ground
distribution.

## `score.py` — merge into a scorecard

```bash
python score.py --lint audit/lint.json --measure audit/measure.json \
  --uniq audit/uniq.json --brief build/content-brief.json \
  [--critic audit/critic.json] [--strict] --out audit/scorecard.json
```

## `slots.py` — image slots

```bash
python slots.py list  LIBRARY.dc.html
python slots.py fill  LIBRARY.dc.html --from photos/ [--by auto|id|order] [--overwrite]
python slots.py audit LIBRARY.dc.html [--json]
python slots.py state LIBRARY.dc.html
python slots.py clear LIBRARY.dc.html
```

`fill` matches a file named for a slot id first, then fills the rest in order, copies images
into `dist/images/`, and writes the sidecar. **Remote URLs are refused** — a dead URL renders
worse than a described slot, and the document has to render offline.

## `report.py` — the HTML report

```bash
python report.py [--project DIR] [--no-open]
```

## `extract_text.py` — `.docx` → text

```bash
python extract_text.py document.docx
```

Stdlib zip/XML. Preserves heading levels, pulls table cells in reading order. Refuses PDFs —
those go through the Read tool or `pypdf`.

---

## Exit codes

| Code | |
|---|---|
| `0` | success / gate PASS / READY |
| `1` | gate FAIL, P0 defects present, verification failed, or NOT READY |
| `2` | file not found, or nothing to audit |

Suitable for CI directly:

```yaml
- run: python scripts/dscc.py audit --strict
```

---

## A note on Windows

All scripts call `sys.stdout.reconfigure(encoding="utf-8")` on import. If you wrap them in
your own tooling, set `PYTHONIOENCODING=utf-8` — an arrow in a progress message is not worth a
crashed audit run.
