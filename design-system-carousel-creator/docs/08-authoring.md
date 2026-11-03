# 8 · Authoring cards

The rules that keep fifty cards looking like one library.

---

## Write the generator, not the HTML

`build/build.py` is the source. `dist/*.dc.html` is its output.

Composing fifty cards by hand into a 120 KB HTML file produces something nobody can re-type,
re-theme or re-order. The generator makes the type ramp nine numbers in one place, a ground a
dictionary, and a fix to a shared row shape reach all fifty cards rather than the eleven you
remembered to edit.

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py build
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview --watch   # rebuild + reload on save
```

---

## Two invariants you must not undo

Both are in the emitted builder with comments explaining them. Both fail silently.

### 1 · Always re-scaffold from scratch

```python
def main():
    subprocess.run([sys.executable, SCAFFOLD, "init", *ARGS], check=True)
    doc = DOC.read_text(encoding="utf-8")
    # … then inject
```

The tempting alternative is idempotence via a marker:

```python
if "BRAND LAYER" not in doc:      # looks careful, is a trap
    doc = insert_css(doc)
```

After the first successful build that condition is never true again, so **every later edit to
the CSS silently does not reach the output.** The symptom is indistinguishable from the edit not
working, which sends you searching the CSS instead of the build script.

Regeneration is cheap and cannot go stale.

### 2 · Tokens into `:root` *before* the CSS layer

```python
doc = inject_tokens(doc, TOKENS_LIGHT)  # first — :root carries the light defaults
doc = insert_css(doc)                   # second
```

Reverse them and guard the injection with `if "--gp-bg" not in doc`, and the CSS layer's own
`var(--gp-bg)` uses satisfy the guard — the tokens are never written and the document fills with
`UNDECLARED_VAR` P0s pointing at a file that, read alone, looks correct.

Declare before you reference. If you must guard, guard on a declaration-shaped sentinel
(`"    --gp-bg: "`), never a bare token name, which appears on both sides.

---

## Card shape

```html
<div style="display:flex;flex-direction:column;gap:18px">
  <div class="gallery-label" style="display:var(--label-vis)">07 · Comparison · capability matrix</div>
  <div class="frame g-panel" data-card="07"
       data-layout="capability-matrix"
       data-mechanic="ledger:vertical:rule:panel:none:panel"
       data-intent="fill"
       data-claim="c012 c019 c044">
    …
  </div>
</div>
```

The `data-*` attributes are not decoration — they are how the auditor checks the build against
the plan:

| Attribute | Makes checkable |
|---|---|
| `data-mechanic` | layout collisions |
| `data-intent` / `data-license` | bottom slack |
| `data-claim` | veracity — provenance is a lookup, not a memory |
| `data-card` | which card a defect belongs to |

The label above each card is **part of the deliverable**. Name the format so the name is a
*specification*: "Comparison · capability matrix", not "Content slide 7". If two names could be
swapped without anyone noticing, they are one format.

---

## Hard rules

### Never write a raw px, raw hex, or inline `font-size`

Everything resolves through a token. This is what makes a fifty-card library re-typable by
editing nine numbers, and it is why a card naming a *role* survives all twelve
ground × theme states while a card carrying a hex survives one.

Codes: `RAW_PX`, `RAW_HEX`, `INLINE_TYPE`.

### `min-width: 0` on every flex child holding text

Omitting it is what drives text through the frame edge — and it only manifests once the copy is
long enough, so a layout passes for twenty cards and breaks on the twenty-first.

### One idea per card, named in ≤ 9 words

If the name needs a subordinate clause, it is two cards.

### No web chrome

Buttons, nav, pricing tiers, forms, tabs, breadcrumbs. A reader cannot click. The moment a
slide contains something that looks clickable it stops reading as a post and starts reading as
a screenshot of a product.

Translate instead: a CTA becomes a tag or a bold closing line; a pricing card becomes a ledger;
a feature grid becomes an icon matrix.

### Concluding lines use `.note`

A summary floating between two rows reads as another row. `.note` pins it to the bottom rule.

### Image slots get an explicit height and ratio

A slot sized only by its content collapses.

### Write literal characters, never numeric entities

`&#9671;` survives tag-stripping in the auditor's text extractor as the digits `9671`, which the
veracity check reads as a figure absent from the brief. One decorative lozenge in a shared
footer produces one `INVENTED_FIGURE` (P0) *per card* — enough to fail the gate on its own.

The document is UTF-8. Write `◇`. The emitted builder asserts this; keep the assertion.

### Every colour used on a card lives in both theme maps

Otherwise it cannot follow the theme, and on a two-theme document that means it is provably
wrong in one of them. Code: `MONO_THEME_TOKEN`.

The illegal fix is one colour tuned to be *acceptable* on both — it clears the check and gives
you a library where nothing is quite right anywhere.

---

## Filling a card

The density law again, from the authoring side: when a card looks empty, the move is to add a
real row from the claim pool. Never to distribute the slack.

```python
def compose(spec):
    parts = [txt(CLAIMS[c]["text"]) for c in spec["claims"] if c in CLAIMS]
    return "\n".join(parts)
```

If `spec["claims"]` yields two rows on a card sized for five, the fix is in the **plan** — assign
more claims — not in the CSS.

If the pool is genuinely exhausted, that is a signal to re-run `:brief` with a wider net, not a
signal to stretch.

### Or license the emptiness

```html
data-intent="breathe" data-license="cover"
```

Legal licenses: `cover`, `close`, `single-figure`, `media-led`, `few-rows`, `section-break`.

Unlicensed slack is a defect. Licensed slack is a design decision. The difference is that
someone declared it in advance rather than after the auditor complained.

---

## Surfaces

Assign each card one of `paper · panel · ink · accent-1 · accent-2 · grey`. Five grounds minimum
across the library.

Ground classes remap role tokens on the frame, so one markup shape works everywhere:

```css
.frame.g-panel { --surface: var(--panel-bg); --ink: var(--panel-fg); --rule: var(--panel-rule) }
```

Never place two cards with the same loud ground (`ink`, `accent-1`, `accent-2`) adjacent — the
auditor emits `GROUND_CLUSTER`.

Suggested distribution across fifty: paper 20–26 · panel 6–9 · ink 6–9 · accent-1 4–6 ·
accent-2 2–4 · grey 3–5.

---

## Visual grammar

Two or three **arbitrary but relentlessly consistent** devices, applied without exception.
Colours and fonts are not a grammar.

Candidates:

- a bracketed micro-label convention — `[ LIKE THIS ]`
- corner micro-labels pinned to artboard edges
- a single geometric intervention repeated at varying scale (notch, cut corner, bleed)
- a fixed rule weight used as the only divider
- hanging index numbers in the left margin
- an ornamental opening capital at ~1.4× cap height

If the brand supplies none, invent one and apply it everywhere. An invented device used fifty
times reads as intent. Used eleven times it reads as an accident.

---

## Type

Three registers per card, maximum: **display**, **body**, **micro**.

The micro register — corner labels, index numbers, credits, bracketed asides — is where density
comes from without loudness. It is the register most often missing from generated work.

Display floor is 120px (`--t-display`) and anything carrying the point is at least 52px
(`--t-heading`), set by thumbnail legibility at 3.6× reduction. The nine type classes in
`kernel.css` are the whole ramp; a card that sets its own font properties is drift.

---

## Structural formats

At least six, and they are not filler. Connective tissue appears as often as content in a real
carousel and is usually the most typographically confident work in the set, because it has the
least content and composition has nowhere to hide.

Required: table of contents · section divider · recap/summary index · end card.
Optional: agenda · credits/colophon · glossary.

A contents card that lists fourteen named themes with real descriptors is a card. A contents
card that points at other cards is a `CROSS_REFERENCE`.

---

## Working loop

```bash
# terminal 1
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py preview --watch

# terminal 2, after a batch of ten
python ${CLAUDE_PLUGIN_ROOT}/scripts/lint.py "dist/Acme.dc.html" --out /tmp/l.json
```

Then before auditing:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py verify "dist/Acme.dc.html"
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py audit
```

Batches of ten matter. An unbalanced `<div>` found at card 12 costs a minute. Found at card 50
it costs an hour of bisecting, and you will not find it by reading.

---

## Reference

- [`skills/carousel-craft/references/mechanics.md`](../skills/carousel-craft/references/mechanics.md) — forty layout mechanics
- [`skills/carousel-craft/references/density-law.md`](../skills/carousel-craft/references/density-law.md) — fill vs. breathe in full
- [`skills/carousel-craft/references/theming.md`](../skills/carousel-craft/references/theming.md) — the two-map law
- [`skills/carousel-craft/references/anti-patterns.md`](../skills/carousel-craft/references/anti-patterns.md) — every failure mode, its tell, its fix
- [`skills/carousel-craft/assets/kernel.css`](../skills/carousel-craft/assets/kernel.css) — the primitive layer. Copy verbatim; never edit per brand
