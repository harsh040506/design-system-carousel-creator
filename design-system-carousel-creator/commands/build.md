---
description: Compose the template library HTML from the system, brief and plan.
argument-hint: "[--plan build/layout-plan.json] [--out \"dist/Brand Template Library.dc.html\"]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# /design-system-carousel-creator:build

`$ARGUMENTS`

Load `carousel-craft`. You need `build/design-system.json`, `build/content-brief.json` and `build/layout-plan.json` in
hand — if any is missing, run its stage first rather than improvising it.

## Scaffold first — never hand-write the envelope

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py init "dist/Brand Template Library.dc.html" \
  --system build/design-system.json --title "…" --cols 5
```

This writes the five-part `.dc.html` envelope and installs everything the bundle needs beside it:

- **`support.js` + `image-slot.js`** — mandatory. Without them the library renders as a blank page
  with no console error: an hour to diagnose, two seconds to prevent.
- **`canvas.html`** — the host. A `.dc.html` expects a canvas application to supply the pan, the
  zoom and the prop editor; without one it renders and does nothing, which reads as a script
  failure and was reported as one.
- **`.image-slots.state.json`** — an empty sidecar. `image-slot.js` fetches it and handles the miss
  correctly, so the 404 is harmless — and it is also the first thing anyone sees in the console,
  where it reads as a broken build.
- **`build/build.py`** — the generator. See below.

## Write the cards in `build/build.py`, not in the HTML

The builder is the source; the `.dc.html` is its output. Composing fifty cards by hand into a 121 KB
HTML file produces something nobody can re-type, re-theme or re-order. The generator makes the type
ramp nine numbers in one place and lets a fix to a shared row shape reach all fifty cards rather than
the eleven you remembered.

Two rules are already baked into the emitted file, with the comments explaining why. **Do not undo
either:**

1. **`main()` always re-scaffolds from scratch.** Never patch the document in place. The shape that
   looks sensible —
   ```python
   if "BRAND LAYER" not in doc:      # <- a trap
       doc = insert_css(doc)
   ```
   — is never true after the first successful build, so every later edit to the CSS silently does not
   reach the output. The failure looks exactly like the edit not working, which is why it costs a
   debugging cycle rather than five minutes.
2. **Ground tokens go into `:root` before the CSS layer is inserted.** Reversing the order and
   guarding the injection with `if "--tok" not in doc` matches the CSS layer's own `var(--tok)`
   uses, so the tokens are never written and you get a screen of `UNDECLARED_VAR` P0s pointing at a
   file that looks correct.

Rebuild with `dscc.py build`, or `dscc.py preview --watch` to rebuild and reload on every save.

Read `carousel-craft/references/dc-format.md` for what each envelope part does. The one fact worth
carrying in your head: **light and dark are the same file** — one enum prop, one `applyTheme()`
method writing custom properties at runtime. Never emit separate light and dark documents.

## Card shape

```
<div style="display:flex;flex-direction:column;gap:18px">
  <div style="…;display:var(--label-vis)">07 · Comparison · capability matrix</div>
  <div data-card="07" data-layout="capability-matrix"
       data-mechanic="ledger:vertical:rule:panel:none:panel"
       data-intent="fill" data-claim="c012 c019 c044"
       style="position:relative;width:1080px;height:1440px;background:var(--panel);
              color:var(--ink);overflow:hidden;flex:none;display:flex;
              flex-direction:column;box-sizing:border-box"> … </div>
</div>
```

The `data-*` attributes are not decoration. They are how the auditor checks the build against the
plan: `data-mechanic` makes layout collisions detectable, `data-intent`/`data-license` make bottom
slack adjudicable, `data-claim` makes veracity a lookup instead of a memory.

The label above each card is part of the deliverable. Name the format so the name is a
*specification* — "Comparison · capability matrix", not "Content slide 7".

## Rules while composing

- **Never write a raw px, raw hex, or inline `font-size` in card markup.** Everything resolves
  through a token. This is what makes the library re-typable by editing nine numbers.
- **One idea per card**, named in ≤9 words. If it needs a subordinate clause, it is two cards.
- **No web chrome.** Buttons, nav, pricing tiers, forms — translate them. A CTA becomes a tag or a
  bold closing line; a pricing card becomes a ledger; a feature grid becomes an icon matrix.
- **`min-width:0` on every flex child holding text.** Omitting it is what drives text through the
  frame edge, and it only manifests once the copy is long enough — so a layout passes for twenty
  cards and breaks on the twenty-first.
- **Concluding lines use `.note`.** A summary floating between two rows reads as another row.
- **Image slots get an explicit height and ratio.** A slot sized only by its content collapses.

## Surfaces are a named set, not a light/dark pair

Assign each card one of `paper · panel · ink · accent-1 · accent-2 · grey`, each with a complete
text-colour treatment. Five grounds minimum across the library. This is the highest-leverage move
for perceived range and the one generated libraries most consistently skip — `uniq.py` emits
`FLAT_SURFACES` below five grounds and `GROUND_CLUSTER` when two loud grounds land on adjacent
cards.

## Fill the image slots

A library demoed with forty grey rectangles reads as unfinished no matter how good the layouts are.
Every `<image-slot>` gets an `id`, a `placeholder` describing the *subject* ("Grayscale horizon at
dusk", "Office snapshot") — never the word "Image" — and, wherever possible, a real local `src`.

If the user has photographs, this is one command:

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/slots.py fill LIBRARY.dc.html --from photos/
python ${CLAUDE_PLUGIN_ROOT}/scripts/slots.py audit LIBRARY.dc.html
```

`fill` matches a file named for a slot id first, then fills the rest in order, copies the images into
`dist/images/` and writes the sidecar. **Do not hotlink remote URLs.** A dead URL renders worse than
a described slot and the document has to render offline — that is the format, not a limitation to
route around.

If the slots ship empty, say so in the report with the count. `slots audit` gives you the number.

## Build in batches of ten

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/lint.py LIBRARY.dc.html --out lint.json
```

after each batch. A missing `</div>` found at card 12 costs a minute. Found at card 50, it costs an
hour of bisecting, and you will not find it by reading.

## Every colour used on a card belongs in BOTH theme maps

`applyTheme()` writes one object literal per theme. A colour declared once in `:root` and used in
card markup cannot follow the theme, so on a two-theme document it is provably wrong in one of them.

This is not hypothetical. A motif fill was declared once and was, in dark mode, a dark disc under
dark type on a light ground — and flipping to light mirrored the bug exactly. Both illegible, and
invisible to every check that existed. `lint.py` now emits **`MONO_THEME_TOKEN`** for it.

The legal fix is to put the token in both maps. The illegal one is to compromise on a single colour
that is mediocre in each, which is how you get a library where nothing is quite right anywhere.

## Write literal characters, never numeric entities

`&#9671;` survives tag-stripping in the auditor's text extractor as the digits `9671`, which the
veracity check reads as a figure absent from the brief. One decorative lozenge in a footer produced
**fifty P0 `INVENTED_FIGURE` defects and a failed gate.** The document is UTF-8: write `◇`. The
emitted builder asserts this; keep the assertion.

## Verify the envelope before auditing

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py verify LIBRARY.dc.html
```

Checks all five envelope parts, both runtime files (presence, size, header), every `var(--x)`
resolving to something declared or set in `applyTheme`, and warns when the canvas host or the slot
sidecar is missing. Measuring a library that cannot render produces confident, precise, meaningless
numbers.

When it passes and all fifty cards are in, run `/design-system-carousel-creator:audit`, then `/design-system-carousel-creator:preview` and actually
look at it.
