---
name: carousel-craft
description: Design principles, layout mechanics and density rules for building fixed-artboard social carousel template libraries (Instagram 4:5, LinkedIn). Use when composing, reviewing, or fixing carousel slides, template libraries, or social post designs — especially when a slide feels sparse, repetitive, off-brand, or "like a website or a report instead of a post".
---

# Carousel Craft

The distilled reasoning behind template libraries that hold up at fifty slides. Not a style — a set
of constraints that make good composition the path of least resistance and bad composition
mechanically detectable.

## Operating with no brief

**"Here's a design system and some content — make me a library" is a complete instruction.** Do not
stop to ask about card count, artboard size, taxonomy, tone, or theme handling. Every one of those
has a defensible default in [`schema/defaults.json`](../../schema/defaults.json), and asking about
them buys nothing the user wants.

Read that file first when the instruction is thin. It covers artboard (1080×1440), card count (50),
theme handling (one file, one enum prop), the surface set, media ratio, grammar devices, type
registers, taxonomy naming, and the structural formats. Take every decision from it, then **state
the choices in the final report** so the user can redirect anything they disagree with.

Only three situations genuinely warrant a question: the sources contradict each other on a fact
that would appear on a card, the brand supplies no colour information at all, or the content is
plainly for a medium other than social carousels. Everything else — decide.

The bar to hit without being told is in
[`references/house-standard.md`](references/house-standard.md). Read it before planning: it names
the eight properties that separate an authored library from a generated one, and the three that
generated output almost always misses.

## The four laws

**1. A slide is a poster, not a page.**
No buttons, nav bars, pricing tables, menus, sign-up forms, breadcrumbs, or any other web interface
chrome. A reader cannot click. The moment a slide contains a thing that looks clickable, it stops
reading as a post and starts reading as a screenshot of a product — which is the single most common
way a good design system produces bad social content.

**2. One idea per slide, stated at poster scale.**
If you cannot name the slide's single claim in six words, the slide is two slides. Body copy under
~24px on a 1080-wide artboard is a report; the headline should be legible at thumbnail size, which
in practice means ≥52px (the `--t-heading` floor) for anything carrying the idea.

**3. Sparse means under-written, never over-spaced.**
See `references/density-law.md`. This is the law that gets violated most and costs most.

**4. Fifty compositions, one identity.**
Every card shares the same artboard, the same masthead position, the same footer, the same type
ramp, the same seven spacing values. Everything *between* the masthead and the footer should be
different on every card. Libraries fail in both directions: fifty identical cards (boring) or fifty
unrelated cards (not a library).

## Working sequence

Follow this order. Each stage is cheap to redo and expensive to skip.

### 1 · Lock the system before drawing anything

Convert the brand input into a **closed set** of legal values — see the
`design-system-distillation` skill. Nine type steps, five figure steps, seven spacing values, four
radii, one motif. Not "roughly these"; exactly these. Then never write a raw pixel or hex value in
card markup again.

The payoff is not tidiness. It is that re-typing an entire fifty-card library becomes editing nine
numbers, and that "is this consistent?" becomes a grep instead of a squint.

### 2 · Build a claim inventory before writing copy

Slides written from memory of the source material drift into generic SaaS filler within about eight
cards. Extract atomic claims first — each a single assertion with its source span and a type
(`stat`, `definition`, `contrast`, `quote`, `process`, `milestone`, `objection`, `consequence`,
`example`, `principle`).
Then compose slides *from the inventory*.

Two things fall out for free: you can prove no number was invented, and when a card turns out
under-written you have a shelf of unused real rows to pull from instead of reaching for padding.

### 3 · Plan all fifty layouts before building any

Assign each card a **mechanic tuple** — `(partition, flow, enumerator, emphasis, media, chrome)` —
and check for collisions across the whole set *on paper*. Two cards with the same tuple are the same
card wearing different words, and you will not notice while building them one at a time. You will
notice immediately in a table.

Target distribution over fifty cards, which is what keeps a library from feeling monotonous:

| Property | Target |
|---|---|
| cards carrying a large image slot | 14–20 (≈30–40%) |
| named grounds used | ≥5 of paper · panel · ink · accent-1 · accent-2 · grey |
| ground mix (per 50 cards) | paper 20–26 · panel 6–9 · ink 6–9 · accent-1 4–6 · accent-2 2–4 · grey 3–5 |
| full-bleed photo cards (`flush`) | 2–4 — not a ground; does not count toward the five |
| cards whose emphasis is a figure | 8–12 |
| distinct partitions used | ≥8 of 10 |
| most-used partition | ≤9 cards |
| mean pairwise tuple distance | ≥2.6 of 6 |

### 4 · Compose, then measure, then rewrite copy

Build the card. Render it. Measure ink coverage, row gaps, overflow, collisions. When a measurement
fails, the fix is almost always *editorial* — a row added, a headline shortened — and almost never
spacing. See `references/anti-patterns.md` for the tell-and-fix table.

## The narrative arc

A carousel is sequential. Fifty templates are not fifty independent posters; they are a kit for
building a sequence, and the kit needs a piece for every position:

```
01–05  Hook            the scroll-stopper. Biggest type in the library. One claim.
06–10  Ground          define the problem / the term / the stakes. Where figures earn their keep.
11–15  Tension         what's broken, what it costs. Contrast and negation mechanics.
16–20  Method          how it works. Numbered, sequential, process mechanics.
21–25  Proof           data, comparisons, before/after. Ledger and table mechanics.
26–30  Voice           quotes, testimonials, positions. `ink` and `grey` grounds live here.
31–35  Depth           technical detail, architecture, specifics. Media-heavy.
36–40  Objection       what people get wrong, what this is not. Negation.
41–45  Application     use cases, scenarios, who it's for. Grid mechanics.
46–50  Structure       section breaks, recaps, indexes, the close.
```

The close (50) and the cover (01) are the two cards a reader is guaranteed to see. Spend
disproportionate effort there.

## Composition heuristics that survive contact

**Give the eye one entry point.** Exactly one element per card should be dramatically larger than
everything else. Two competing focal points reads as noise; zero reads as a spreadsheet.

**Anchor the concluding line to the bottom rule.** A sentence that summarises or lands the card
belongs pinned above the footer, not floating in the middle of a list where it looks like another
row. This is what `.note` exists for.

**Let the motif bleed.** A graphic element that runs off the artboard edge implies a world larger
than the frame. One fully-contained circle centred in white space is a logo; the same circle cropped
by the edge is a composition.

**Rules over boxes.** Hairline dividers separate content at a fraction of the visual cost of card
containers. Reserve filled panels for genuine figure/ground changes — when everything is a box,
nothing has weight.

**Numbers are graphics.** Set statistics on the figure ramp, not the heading ramp: bigger, tighter,
lighter. A number at 124px with a 21px label beneath it is a composition. The same number at body
size inside a sentence is a footnote.

**Grain fixes flat gradients.** A pure CSS gradient reads as a default. The same gradient with an
`feTurbulence` noise overlay at ~0.75 opacity in `overlay` blend mode reads as designed. Cheapest
upgrade available.

**Loud grounds are punctuation.** An `ink` or accent card every 4–6 slides resets the eye and marks
section boundaries. The same loud ground twice in a row wastes the effect (`GROUND_CLUSTER`).

## Reference files

- `references/house-standard.md` — **read first.** The eight properties that separate an authored
  library from a generated one, and the three that generated output almost always misses
- `references/mechanics.md` — the forty layout mechanics, with what each is *for* and how it fails
- `references/density-law.md` — fill vs. breathe, in full, including the license list
- `references/anti-patterns.md` — every known failure mode, its tell, its cause, its fix
- `references/theming.md` — one document, two themes, and the law that every card colour lives in
  both maps. Short, and it prevents the most expensive invisible bug in the system
- `references/dc-format.md` — the `.dc.html` envelope, the theming block, `<image-slot>` usage
- `assets/kernel.css` — the brand-agnostic primitive layer; copy verbatim, never edit per brand
- `../../schema/defaults.json` — every decision to take when the user hasn't specified one

## Verification is not optional

A library that has not been through `scripts/dscc.py audit` has not been checked. Eyes miss
overflow of 4px, gap variance across cards seen minutes apart, and a type ramp that grew a twelfth
size. The harness does not. Run it before claiming a card is done — and read
`quality-gate` for what the numbers mean.

## Neither is looking at it

```
python scripts/dscc.py preview
```

The measurements catch what eyes miss. They also cannot see a motif that has gone dark-on-dark in one
theme, a rule that runs past its content, or a closing note that reads as another row — the kind of
compositional defect that is invisible in every number and obvious within thirty seconds of opening
the canvas. Measurement and looking check different things; do both before calling a card done.

Press `D` to flip themes, `A` for the per-card audit overlay, `F` to step through at review size.
Run this before you describe the library to anyone, including yourself.
