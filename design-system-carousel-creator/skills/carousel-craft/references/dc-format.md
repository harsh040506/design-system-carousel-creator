# The `.dc.html` Document Format

The container format for a template library. It is a plain HTML file with five required parts and
two sidecar runtime files. Get the envelope wrong and the failure is silent — a blank page, or
cards that render but cannot be re-themed, with no error in the console.

`scripts/scaffold.py init` writes a correct envelope and installs the runtime. Use it rather than
typing this from memory.

---

## Directory structure

A delivered library is a **directory**, not a file. What must be there:

```
<Brand> Post & Carousel Templates/
├── <Brand> Template Library.dc.html   the library — one file, both themes
├── support.js                          runtime (installed by scaffold.py)
├── image-slot.js                       runtime (installed by scaffold.py)
├── fonts/                              ONLY if the library uses local @font-face
│   └── Brand-Regular.otf …
└── logos/                              ONLY if cards reference brand marks
    └── logo1.svg …
```

`fonts/` and `logos/` are conditional. A library on Google Fonts with no local marks needs neither;
one carrying a licensed face needs every weight it declares. Install them with:

```
python scripts/scaffold.py init OUT.dc.html --fonts-dir ./src/fonts --logos-dir ./src/logos
# or afterwards:
python scripts/scaffold.py assets OUTDIR --fonts ./src/fonts --logos ./src/logos
```

### What is *not* part of the deliverable

Working directories accumulate alongside a library and should not be recreated or shipped:

| Path | What it is |
|---|---|
| `uploads/` | source material — PDFs, pasted screenshots, other libraries referenced while designing. **Input, not output.** |
| `.image-slots.state.json` | pan/zoom state written by `image-slot.js` at runtime when a user reframes a photo. Can reach megabytes. Generated, never authored. |
| `.thumbnail` | preview image written by the canvas app |
| `render/`, `scraps/`, `_tmp_*` | scratch artifacts |

Do not generate these. Do not treat their absence as incomplete.

### Broken local references fail silently

A missing `./fonts/Brand-Regular.otf` raises **no error anywhere**. The browser falls back to a
default face and the whole library renders in the wrong typeface — a failure that looks like a
design problem rather than a missing file, and can survive several rounds of review before anyone
works out why the display type looks wrong.

`scaffold.py verify` resolves every `./` reference in the document against the bundle and fails on
any that does not exist. Run it before auditing.

---

## Anatomy

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="./support.js"></script>          <!-- 1. FIRST. defines DCLogic -->
</head>
<body>
<x-dc>                                         <!-- 2. component root -->
<helmet>                                       <!-- 3. injected into <head> -->
  <meta name="design_doc_mode" content="canvas">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
  <link href="https://fonts.googleapis.com/css2?family=…" rel="stylesheet">
  <script src="./image-slot.js"></script>
  <style>
    :root { --paper:#FFF; --ink:#111; … ; letter-spacing: normal; }
    body { margin:0; background: var(--canvas); }
    image-slot { display:block; width:100%; height:100%; min-width:0; }
  </style>
</helmet>

<section style="display:flex;flex-direction:column;gap:72px;padding:96px">
  <header>…library title, count, dimensions…</header>
  <div style="display:grid;grid-template-columns:repeat(8,1080px);gap:96px 72px;
              justify-content:start;align-items:start">
     …one wrapper per card…                    <!-- 4. the gallery -->
  </div>
</section>
</x-dc>

<script type="text/x-dc" data-dc-script data-props="{…escaped JSON…}">
class Component extends DCLogic {               <!-- 5. the logic block -->
  applyTheme() { … }
  componentDidMount()  { this.applyTheme(); }
  componentDidUpdate() { this.applyTheme(); }
  renderVals() { return {}; }
}
</script>
</body>
</html>
```

**Order matters.** `support.js` must load before anything references `DCLogic`. `image-slot.js`
belongs inside `<helmet>`, not `<head>`.

---

## The single most important architectural fact

**Light and dark are the same file.** Not two files, not two `:root` blocks toggled by an attribute
— one document with an enum prop, and a `applyTheme()` method that writes custom properties onto
`document.documentElement.style` at runtime.

This is worth internalising because the wrong instinct — export a light library and a dark library —
doubles the maintenance surface and guarantees they drift apart. One file, one prop, both themes.

The `:root` block in `<helmet>` holds the **light** values as static defaults so the document looks
right before JavaScript runs. `applyTheme()` then overwrites them on mount.

---

## The logic block

The compact form, preferred — one object per theme, then a loop:

```js
class Component extends DCLogic {
  applyTheme() {
    const dark = (this.props.theme ?? 'White') === 'Black';
    const r = document.documentElement.style;
    const v = dark
      ? { paper:'#0F0E0C', ink:'#FAFAF5', panel:'#1D1C1A', rule:'rgba(250,250,245,0.20)',
          canvas:'#000000', 'logo-filter':'invert(1)' }
      : { paper:'#FAFAF5', ink:'#0F0E0C', panel:'#F0F0EB', rule:'rgba(15,14,12,0.16)',
          canvas:'#C9C6C0', 'logo-filter':'none' };
    for (const k in v) r.setProperty('--' + k, v[k]);
  }
  componentDidMount()  { this.applyTheme(); }
  componentDidUpdate() { this.applyTheme(); }
  renderVals() { return {}; }
}
```

Keys are written **without** the leading `--`; the loop adds it. Both lifecycle hooks are required:
`componentDidMount` for first paint, `componentDidUpdate` so the prop editor actually does something.

### `data-props` — the editor schema

JSON, HTML-escaped (`"` → `&quot;`). Each key becomes a control in the prop editor.

```json
{"theme":{"editor":"enum","default":"White","options":["White","Black"],
          "tsType":"string","section":"Theme"},
 "showLabels":{"editor":"boolean","default":true,"tsType":"boolean","section":"Theme"}}
```

Editors seen in practice: `enum` (with `options`), `boolean`, `color` (with `options` as swatch
presets). A `color` prop with four presets gives the user a palette picker rather than a binary
toggle — worth using when the brand genuinely has multiple accent treatments rather than a
light/dark pair.

`showLabels` driving `--label-vis` is a good pattern: the per-card caption above each artboard is
useful while working and noise when exporting.

---

## Card wrappers

Each card is a label plus a fixed-pixel artboard:

```html
<div style="display:flex;flex-direction:column;gap:18px">
  <div style="font-size:13px;letter-spacing:0.18em;color:var(--lbl);display:var(--label-vis)">
    01 · Statement + bleeding image
  </div>
  <div style="position:relative;width:1080px;height:1440px;background:var(--paper);
              color:var(--ink);overflow:hidden;flex:none;display:flex;
              flex-direction:column;box-sizing:border-box">
    …
  </div>
</div>
```

`flex:none` and `box-sizing:border-box` are load-bearing. `overflow:hidden` clips intentional bleed;
it is not a licence to let content escape — the auditor still flags overflow.

**Artboard size: 1080×1440** (3:4) is what these libraries use. 1080×1350 (4:5) is the tighter
Instagram portrait crop. Pick one per library and never mix.

---

## `<image-slot>`

```html
<div style="background:var(--plate);min-width:0;overflow:hidden">
  <image-slot id="ed-01a" placeholder="Grayscale hero"
              src="./media/ed-01a.jpg"></image-slot>
</div>
```

- Needs a **sized parent**. It fills its container and collapses to nothing without one.
- `min-width:0` on that parent, always — same flex-shrink trap as everywhere else.
- Unique `id` per slot; state is keyed on it.
- `placeholder` is the empty-state label. Write a real description ("Grayscale hero", "Plate"),
  never "Image".
- `src` prefills. A library that ships with every slot filled demos far better than one showing
  forty grey rectangles. Use **local files** copied into the bundle (`dscc slots fill`), from openly
  licensed sources. A remote URL is flagged `REMOTE_SLOT` (P1): a dead link renders worse than a
  described slot, and the document must render offline.

---

## Fonts

Three routes, all seen in the wild:

1. **Google Fonts** — one `<link>` with every family combined into a single request. This is the
   scaffold's default and the one request a built library can make; if it is blocked the text falls
   back to a system face rather than failing.
2. **Local `@font-face`** in the `<helmet>` `<style>` for licensed faces, pointing at `./fonts/*.otf`.
   If you do this, the font files become part of the bundle and must ship with it. Combine with
   `scaffold.py init --fonts none` for a bundle that makes no outside request at all.
3. **Icon webfonts** via CDN when a system needs a large icon set (this reintroduces a network
   dependency; prefer inline SVG).

Always `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">` first — it measurably
cuts first-paint time on a document this large.

---

## Verify, don't hope

```
python scripts/scaffold.py verify LIBRARY.dc.html
```

Checks all five envelope parts, both runtime files (presence, size, header), every `var(--x)`
resolving to something declared or set in `applyTheme`, and that image slots exist at all. Non-zero
exit on any failure, so it drops straight into a build loop.
