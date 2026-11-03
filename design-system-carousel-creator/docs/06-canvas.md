# 6 · The canvas

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview
```

Serves `dist/` on the first free port from 4173 and opens `canvas.html`.

---

## Why a canvas host exists at all

A `.dc.html` is a canvas **document**. It carries

```html
<meta name="design_doc_mode" content="canvas">
```

and expects a host application to supply the canvas surface, the zoom, and the prop editor.
Served from a plain static server it renders and then does nothing — no error, no console
message, just a page that sits still. That silence reads as "the JavaScript isn't loading",
which is a reasonable diagnosis of the wrong problem: the scripts are fine, there is simply no
host to talk to.

`canvas.html` is that host. It does not mock the protocol — it speaks the one `support.js`
already implements:

```
parent → doc    postMessage {type:'__dc_theme', theme:'dark'|'light'}
                window.__dcSetProps(rootName, {theme:'Black'|'White', showLabels})
doc → parent    postMessage {type:'__dc_booted', rootName, propsMeta}
```

So the theme toggle drives the library's **real theme prop** through the runtime — the same
path a production host uses — rather than repainting CSS from outside.

**It is part of the bundle, not the export.** It never touches the `.dc.html`, so `verify`,
`lint` and `measure` still describe real 1080×1440 artboards rather than a transformed canvas.

---

## Controls

| Gesture | |
|---|---|
| drag | pan |
| scroll | pan |
| shift + scroll | pan horizontally |
| ⌘/Ctrl + scroll, trackpad pinch | zoom at the cursor, 3–400% |
| double-click a card | focus it |

| Key | |
|---|---|
| `+` `−` | zoom in / out |
| `0` | actual size (100%) |
| `1` | fit the whole gallery |
| `2` | fit to width — the opening view |
| `F` | focus one artboard at review size |
| `[` `]` | previous / next card |
| `I` | card index |
| `A` | audit overlay |
| `M` | minimap |
| `L` | format labels |
| `D` | dark / light |
| `P` | presenter mode |
| `S` | copy the shot command for the focused card |
| `R` | reload the document |
| `?` | key map |
| `Esc` | close whatever is open |

The key map shows once on first run, then never again. `?` brings it back.

---

## The panels

### Card index (`I`)

Every format by number and name, filterable. Click to fly to it. A coloured dot per card shows
its audit grade once a scorecard exists. Fifty artboards on an infinite canvas is a haystack;
this is the way through it.

Opening the rail slides the canvas rather than covering the first column with it.

### Audit overlay (`A`)

Reads the live scorecard and draws each card's score and defect codes on the card itself.
Failing cards get a red edge, warning cards amber. Click a badge to fly to that card.

This is the difference between a scorecard you cross-reference by hand and one you can see.

### Minimap (`M`)

A schematic of the whole gallery with a viewport rectangle. Click anywhere to travel there.
Failing cards show red in the map, so a cluster of problems is visible at a glance.

### Presenter mode (`P`)

One card, full bleed, no chrome, arrow keys to step. For showing a client.

---

## Why it opens at fit-to-width

Fitting a fifty-card gallery to the window lands near 5%, which is not a view of anything. Fit
to width puts a full row on screen at roughly the size a carousel is actually consumed at in a
feed — which is the size at which thumbnail legibility problems become visible.

Your scale, position, theme, and open panels are remembered per document in `localStorage`.
Reopening puts you back where you were.

---

## The iframe is not interactive

`#doc` is `pointer-events: none`, deliberately.

A wheel event over a cross-document iframe never reaches the parent window. If the document
accepted pointer events, the canvas could not implement zoom at all. So the canvas owns every
gesture and the frame is visual only. That is the one thing a local host cannot have both ways.

---

## Live reload

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview --watch
```

Watches `build/` and `dist/`. On change it re-runs `build/build.py`, then pushes a `reload`
event over Server-Sent Events. The canvas restores your scale, position, theme and focused card
across the reload, so rebuild-and-look is about a second instead of six seconds of re-finding
your place.

A build failure prints the tail of the traceback and does **not** reload — a canvas showing the
last good render is more useful than a blank one.

The status dot bottom-left: grey = no connection, green = watching, red flash = reloading.

---

## Two routes a plain static server does not have

| Route | |
|---|---|
| `/__dscc/state` | `project.json` plus the latest scorecard, so the audit overlay can read outside `dist/` |
| `/__dscc/events` | the reload stream |

Both are read-only and exist only while the preview server runs. On any other static server
they 404 and the canvas degrades cleanly to pan / zoom / theme. **The bundle stays
self-contained.**

---

## Typography

The canvas UI is JetBrains Mono, embedded as a `data:` URI at install time. There is no `<link>`
to a font CDN anywhere in the file and no request leaves the page.

This is not decoration. The canvas is the one part of the toolchain a designer looks at, so its
typography must not be a function of network conditions. Behind a proxy that blocks
`fonts.gstatic.com` — or on a plane — a linked webfont silently falls back to whatever monospace
the OS supplies, the labels reflow, and the tool looks broken at the exact moment you are
judging whether the work looks good. 40 KB, once, removes the question.

Licence and provenance: [`assets/canvas/FONT-LICENSE.md`](../assets/canvas/FONT-LICENSE.md).

---

## Over `file://`

The browser gives the iframe an opaque origin, so the theme bridge, the card index and the
audit overlay are all blocked. Pan and zoom still work, and a banner explains why the rest
doesn't. This is a browser security rule, not a bug in the bundle.

Use `dscc.py preview`, which starts the right server.

---

## Scripting hook

`window.__canvas` is exposed for the console:

```js
__canvas.state              // scale, position, theme, card count, whether bridged
__canvas.cards              // every card with its geometry and format name
__canvas.goTo(6, true)      // fly to card 7 (0-indexed)
__canvas.theme('light')
__canvas.audit(true)
__canvas.index(true)
__canvas.fit() / .fitWidth() / .actualSize()
__canvas.reloadDoc()
```

Useful for driving a review, and for checking the host from a test without reading the file.

---

## Customising it

The canvas is regenerated on every scaffold, so edits to a bundle's copy are lost. Change
[`assets/canvas/canvas.html`](../assets/canvas/canvas.html) in the plugin and re-run:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py canvas dist/
```

Placeholders substituted at install time: `__FONT_FACE__`, `__DOC_SRC__`, `__DOC_SRC_JS__`, `__DOC_TITLE__`,
`__CARD_W__`, `__CARD_H__`, `__DEFAULT_DARK__`.
