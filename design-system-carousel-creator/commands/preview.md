---
description: Serve the bundle and open the canvas — pan, zoom, theme, card index, audit overlay.
argument-hint: [--watch] [--port 4173] [--no-open]
allowed-tools: Bash, Read
---

# /design-system-carousel-creator:preview

`$ARGUMENTS`

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

Serves `dist/` on the first free port from 4173 and opens `canvas.html`. **A pipeline that ends
without opening the thing it built is not finished.**

## Why this exists

A `.dc.html` is a canvas *document*: it carries `<meta name="design_doc_mode" content="canvas">` and
expects a host application to supply the canvas, the zoom and the prop editor. Served from a plain
static server it renders and does nothing — no error, no console message, just a page that sits
still. That silence reads as "the JavaScript isn't loading," which is a reasonable diagnosis of the
wrong problem: the scripts are fine, there is simply no host to talk to.

`canvas.html` is that host. It does not mock the protocol; it speaks the one `support.js` already
implements:

```
parent → doc   postMessage {type:'__dc_theme', theme:'dark'|'light'}
               window.__dcSetProps(rootName, {theme:'Black'|'White', showLabels})
doc → parent   postMessage {type:'__dc_booted', rootName, propsMeta}
```

The host is part of the **bundle**, not the **export**. It never touches the `.dc.html`, so
`scaffold verify`, `lint` and `measure` still describe real artboards rather than a transformed
canvas.

## Controls

| | |
|---|---|
| drag / scroll | pan |
| ⌘/Ctrl + scroll, pinch | zoom at the cursor, 3–400% |
| `1` `2` `0` | fit all · fit width (the opening view) · actual size |
| `F`, `[` `]` | focus one artboard at review size, step through |
| `I` | card index — every format by name, filterable, click to fly |
| `A` | audit overlay — per-card score and defect codes drawn on the cards |
| `M` | minimap |
| `L` | format labels (drives the library's own `showLabels` prop) |
| `D` | dark / light — canvas ground **and** library theme together |
| `P` | presenter mode — one card, no chrome |
| `R` | reload · `S` copy the shot command · `?` key map |

It opens at fit-to-width, not fit-all: fitting a fifty-card gallery lands near 5%, which is not a
view of anything. Fit-width puts a full row on screen at roughly the size a carousel is consumed at
in a feed.

## Live rebuild

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview --watch
```

Watches `build/` and `dist/`, re-runs `build/build.py` on change, pushes `reload` over SSE. The
canvas restores scale, position, theme and focused card across the reload, so rebuild-and-look is one
second rather than six of re-finding your place. Build failures print the tail of the traceback and
do **not** reload — a canvas showing the last good render is more useful than a blank one.

## Two routes the plain static server does not have

- `/__dscc/state` — `project.json` plus the latest scorecard, so the audit overlay can read outside
  `dist/`. Deliberately, read-only, and only while this server runs.
- `/__dscc/events` — the reload stream.

On any other static server both 404 and the canvas degrades to pan / zoom / theme. The bundle stays
self-contained.

## If it does not work

Over `file://` the browser gives the iframe an opaque origin: the theme bridge, the card index and
the audit overlay are all blocked and a banner says so. Pan and zoom still work. Use this command
rather than opening the file.

`.image-slots.state.json` no longer 404s — `scaffold init` seeds it. It is generated-never-authored;
do not commit it and do not hand-write its contents.
