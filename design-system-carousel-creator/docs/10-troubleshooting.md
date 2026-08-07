# 10 · Troubleshooting

Symptoms first, because that is what you actually have.

---

## Things that look broken and are not

### The canvas shows the gallery but nothing pans or zooms

You opened the `.dc.html` directly instead of `canvas.html`.

A `.dc.html` is a canvas *document* — it expects a host application to supply the canvas, the
zoom and the prop editor. On its own it renders and sits still, with no error, which reads as a
script failure.

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

### `.image-slots.state.json` 404s in the console

Expected, and harmless. `image-slot.js` fetches a sidecar it *writes*; it doesn't ship with one
until something is reframed, and the loader handles the miss.

`scaffold init` seeds an empty `{}` so you shouldn't see it at all. If you do, the bundle was
assembled without scaffold — run:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/slots.py state "dist/YourLibrary.dc.html"
```

### The theme toggle does nothing, and the index and overlay are empty

You are on `file://`. The browser gives the iframe an opaque origin, so the theme bridge, the
card index and the audit overlay are all blocked. A banner in the canvas says so.

This is a browser security rule, not a bug. Use `dscc.py preview`.

### `craft -- / 20` and the total is out of 80

Working as designed. Craft is the judged dimension; it needs the `design-critic` agent. Until
you run it the scorecard carries a `NO_CRITIC` defect saying exactly this.

Run the agent over `shots/`, then re-score with `--critic audit/critic.json`.

### A request to `unpkg.com` in the network tab

The vendored `support.js` runtime loads React and Babel from a CDN when the document renders.
That is behaviour of the `.dc.html` runtime this plugin bundles, not of the plugin's own
tooling. Building, auditing and the canvas chrome itself make no external requests.

---

## Setup

### `doctor` says `NOT READY` — chromium

```
chromium  FAILED - run: playwright install chromium
```

Installing the Python package does not download the browser. Run `playwright install chromium`.

### `doctor --system DESIGN.md` complains it is not JSON

`--system` wants the **distilled artifact** (`build/design-system.json`), not your brand
document. Run `:distill` first.

### `UnicodeEncodeError: 'charmap' codec can't encode character`

Windows console encoding. Every script reconfigures stdout on import; if you're wrapping them,
set `PYTHONIOENCODING=utf-8`.

### Paths with `&` or spaces fail

Quote them. `"Acme & Co Templates/dist/Library.dc.html"`. The audit command says so explicitly
when a file isn't found, because this is the usual cause.

---

## Build

### Edits to the CSS don't reach the output

The builder is patching the document in place instead of re-scaffolding. Look for:

```python
if "BRAND LAYER" not in doc:      # the trap
    doc = insert_css(doc)
```

After the first successful build that is never true again. `main()` must re-run
`scaffold.py init` from scratch every time. See
[Authoring](08-authoring.md#1--always-re-scaffold-from-scratch).

### A wave of `UNDECLARED_VAR` P0s on a file that looks correct

Injection ordering. Tokens must go into `:root` **before** the CSS layer is inserted. If the
injection is guarded by `if "--gp-bg" not in doc`, the CSS layer's own `var(--gp-bg)` uses
satisfy the guard and the tokens are never written.

Guard on a declaration-shaped sentinel (`"    --gp-bg: "`), or don't guard at all.

### Artboards measure larger than declared

`box-sizing`. A frame setting width, height *and* padding under content-box adds the padding:
1080 × 1440 renders at 1216 × 1553, silently, and every geometric number is then computed
against an artboard that doesn't exist.

`kernel.css` sets `box-sizing: border-box` on `.frame` and descendants. If you vendored an
older kernel or edited it, restore that line.

### `INVENTED_FIGURE` on every card at once

A numeric HTML entity in shared chrome. `&#9671;` in a footer survives tag-stripping as `9671`
and reads as an unsourced figure — once per card.

Write literal characters; the document is UTF-8. The emitted builder asserts
`not re.search(r"&#\d+;", doc)`. Keep the assertion.

### `scaffold verify` fails on a fresh scaffold with no design system

Expected. The kernel references tokens that `:distill` writes. Run `:distill` before `:build`.

### 25-ish `OFF_SCALE` defects pointing at the kernel

Your kernel copy is missing its sentinels. The scale check skips between
`dscc:kernel-begin` and `dscc:kernel-end`; if you vendored the file before those existed, or
stripped comments, re-copy it from
[`skills/carousel-craft/assets/kernel.css`](../skills/carousel-craft/assets/kernel.css).

---

## Audit

### The gate fails but the total is high

Read the gate reasons. Any of these fail it independently of the total:

- one P0 defect anywhere
- one card below 70
- density below 15, distinction below 11
- **any declared constraint breached**

### `CROSS_REFERENCE` on a card that doesn't reference anything

A false positive. **Tighten the pattern, don't edit the card.** Patterns live in
`CROSS_REF_PHRASES` in [`scripts/lint.py`](../scripts/lint.py).

A verifier that fires on known-good input trains everyone to skim past its output, including
the true positives.

### Scores contradict what you see

Suspect the measurement first, then say so. Verify against three cards you have looked at
closely before trusting it on fifty you haven't. If the harness is wrong, fix the harness —
don't "fix" the library to satisfy a broken check.

### The score is flat across refine passes

Read `audit/history.jsonl`. A defect class surviving two passes with no movement means the
problem is upstream — a thin claim pool or a weak layout plan — not something a third editing
pass reaches. Go back to `:brief` or `:plan`.

### `degraded mode` in the output

No project manifest found, so the artboard was auto-detected and slack licensing can't be read.
Unlicensed slack is scored *in the library's favour* in this mode. Expected when auditing a
foreign library; a problem if you meant to audit your own — check you're inside the project.

---

## Preview

### Port already in use

It isn't — the server walks upward from the requested port. The URL it prints is the one it
bound.

### `--watch` doesn't rebuild

It watches `build/` and `dist/` for `.py`, `.json`, `.css`, `.js`, `.html`, `.md`, and only runs
the builder when a `.py` or `.json` changes. A build failure prints the traceback tail and
deliberately does **not** reload — a canvas showing the last good render beats a blank one.

### The canvas UI font looks wrong

It shouldn't — JetBrains Mono is embedded as a `data:` URI, no network involved. If it fell
back to a system monospace, `assets/canvas/JetBrainsMono-latin.woff2.base64` is missing from the
plugin. Re-install the canvas:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py canvas dist/
```

### Live reload loses my place

It shouldn't — scale, position, theme and focused card are restored. If the document height
changed a lot (labels toggled, cards added), the restored position may point somewhere
different. Press `2` for fit-to-width.

---

## Getting more detail

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py info          # project state and audit trail
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py report        # everything as one HTML page
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py verify "dist/X.dc.html" --json
python ${CLAUDE_PLUGIN_ROOT}/scripts/slots.py audit "dist/X.dc.html"
```

And in the canvas console: `__canvas.state`.
