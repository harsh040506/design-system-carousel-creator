# The House Standard

What separates a template library that looks generated from one that looks *authored*. These are the
properties observed across professionally-built libraries in this category — the things that are
true of all of them regardless of brand, and that are almost never true of a first draft.

Treat this as the bar. A library that has all of these is good. A library missing three of them
reads as competent-but-generated no matter how clean its tokens are.

---

## 1 · The library has a grammar, not just a palette

Excellent libraries are recognisable at a glance across every card because they commit to **two or
three specific devices** and use them relentlessly:

- a swash/ornamental capital opening display words, at ~1.4× the surrounding cap height
- a corner micro-label in bracketed mono at the artboard edge
- a bracket convention — `[ Like This ]` — used for asides, categories, captions
- a rule weight that never varies
- a single geometric intervention repeated at different scales — a notch, a bleed, a cut corner

**A brand's colours and fonts are not a grammar.** Two libraries can share a palette entirely and one
still feels authored because it made three arbitrary-but-consistent choices and never wavered.

When distilling a brand that has no obvious device, *invent one* and apply it everywhere. An invented
device applied fifty times reads as intent. No device reads as a template.

---

## 2 · Surface variants are a first-class axis

Weak libraries have light cards and dark cards. Strong ones have a **named surface set** — five or
six distinct card grounds, each carrying its own complete text-colour treatment:

```
paper   the default ground
panel   one step off paper, for grouped content
ink     full inversion, the loudest punctuation
accent-1  a deep saturated ground (a teal, a brown, an oxblood)
accent-2  a second, used sparingly enough to stay surprising
grey     a neutral mid-ground for quotes and testimonials
```

Cards then get labelled by ground — *"Teal · workflow breakdown"*, *"Ink cover · abstract statement"*,
*"Grey · testimonial grid"*. The ground becomes part of the format's identity.

This single move does more for perceived range than any amount of layout variation, because it
changes the card's whole optical weight rather than rearranging boxes within a constant one.

**Distribution across ~50 cards:** paper 20–26 · panel 6–9 · ink 6–9 · accent-1 4–6 · accent-2 2–4 ·
grey 3–5. Never two of the same loud ground adjacent.

---

## 3 · Density is editorial, not decorative

The strongest cards carry a *lot* of real content and still feel calm. What makes that possible:

- **Three registers per card, maximum.** A display line, a body register, a micro register. Not five.
- **The micro register does the heavy lifting.** Corner labels, index numbers, category tags, credits,
  bracketed asides — all at 13–19px, all in the same letterspaced treatment. This is where a card
  gets its density without getting loud.
- **Real content in every slot.** Spec tables have real specs. Index rows have real page references.
  Nothing says "lorem" and nothing says "Category".

A card with a headline, six index rows, three micro-labels and a bleeding image is dense *and* calm.
A card with a headline and two paragraphs is sparse *and* busy.

---

## 4 · Image slots are filled, not empty

A library demoed with forty grey rectangles reads as unfinished, whatever the layout quality. Every
slot should ship **prefilled** from an openly-licensed source, and the placeholder text should
describe the intended subject — `"Grayscale hero"`, `"Office snapshot"`, `"Plate"` — never `"Image"`.

Grayscale or duotone treatment on all photography is the cheapest way to make heterogeneous stock
imagery look like one commissioned shoot.

---

## 5 · The format count is high and the taxonomy is flat

Reference libraries run **40 to 120 formats**, not 20. And the taxonomy is *flat* — a numbered list
of named formats, each a specific compositional idea:

> `12 · Stat rows` · `19 · Checklist · readiness assessment` · `36 · Definition · glossary term`
> `47 · Location callout · map pin` · `54 · Transcript` · `61 · Red flags`

Not `Category A / Variant 3`. Each name describes what the card *does*, is unique, and could be
requested by name. If two format names could be swapped without anyone noticing, they are one format.

**A good format name is a specification.** "Comparison · capability matrix" tells you the mechanic,
the content type, and roughly what it looks like. "Content slide 4" tells you nothing and usually
labels a card that has nothing to say.

---

## 6 · Structural formats are treated as seriously as content formats

Weak libraries have fifty content slides. Strong ones spend real design effort on the connective
tissue, because in a real carousel these appear as often as anything else:

- table of contents / index with page references
- section dividers
- agenda, numbered two-column
- recap / summary index
- credits and colophon
- end card

These are usually the most typographically confident cards in the whole set — they have the least
content, so composition has nowhere to hide.

---

## 7 · Every card is legible at thumbnail scale

A carousel is consumed at ~300px wide in a feed. The rule that follows: **the single idea of each
card must survive a 3.6× reduction.** Display type at 62–104px on a 1080 artboard, never below 46px
for anything carrying the point. Supporting text may become texture at that scale — that is fine and
expected — but the headline may not.

---

## 8 · The system is configurable at the top, not per card

One prop block drives the whole library. Changing the accent recolours 120 cards. Nothing is
hardcoded per card that could have been a token.

This is the property most often missing from otherwise-good output, and it is the one that decides
whether a library is a *system* or fifty pictures. It is also the one this pipeline enforces
mechanically — see the Discipline dimension in `quality-gate`.

---

## The honest gap

Most generated libraries fail on **1, 2, and 5** — no grammar, binary light/dark instead of a named
surface set, and twenty formats where there should be fifty with real names.

Those three are where to spend effort when a library scores well and still feels flat.
