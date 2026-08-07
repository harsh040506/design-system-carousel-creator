# Layout Mechanics Catalogue

Forty mechanics, each defined by what it is *for* rather than what it looks like. A mechanic is a
way of organising a content region — not a template. The same mechanic with a different enumerator,
emphasis carrier and chrome variant produces a visibly different card.

**Mechanic tuple:** `(partition, flow, enumerator, emphasis, media, chrome)`

| Axis | Values |
|---|---|
| partition | `monolith · stack · duo · triad · grid · rail · chain · strip · ledger · overlay` |
| flow | `vertical · horizontal · z · radial · centred` |
| enumerator | `none · number · pip · rule · chip · icon · glyph` |
| emphasis | `display · figure · media · quote · panel · diagram` |
| media | `none · inset · sidecar · full-bleed · repeated` |
| chrome | `paper · panel · ink · accent-1 · accent-2 · grey · flush` |

### On the `chrome` axis

This is the **surface ground** the card sits on — a full colour treatment, ground plus every text
role recoloured to match, not a background swap. Weak libraries have two grounds (light and dark).
Strong ones have five or six named ones and label formats by ground: *"Teal · workflow breakdown"*,
*"Ink cover · abstract statement"*, *"Grey · testimonial grid"*.

Changing the ground alters a card's whole optical weight, which does more for perceived range than
rearranging boxes inside a constant one. It is the cheapest distinction move available and the one
generated libraries most consistently skip. Distribution targets are in `house-standard.md` §2.

**Never place two cards with the same loud ground (`ink`, `accent-1`, `accent-2`) adjacent.** They
are punctuation, and punctuation does not cluster.

---

## Monolith — one thing, huge

**01 · Statement.** A single headline at display scale, nothing else but a kicker. For covers and
section breaks. *Fails when* the headline is long enough to wrap four times — at that point it isn't
a statement, it's a paragraph set too large.

**02 · Hero figure.** One number at hero scale with a label beneath. The number must be surprising
on its own; a hero figure of "3" with no context is a wasted slide.

**03 · Question.** A question at display scale, answer withheld for the next slide. Only works in
sequence — a standalone question card is a dead end.

**04 · Term card.** A word, then its definition beneath at body-xl. The most under-used mechanic in
most libraries and the best way to open an educational sequence.

**05 · Quote monolith.** Pull quote at heading scale with attribution pinned to the bottom rule.
Almost always `plate`. Never add quotation-mark graphics — the scale already signals it.

## Stack — ruled rows, the workhorse

**06 · Ruled list.** Rows separated by hairlines, each a label plus a line of body. The default for
"here are five things." *Fails* by being used eight times in one library; vary the enumerator.

**07 · Lead-in list.** Each row leads with an icon tile or numeral chip, then a two-line block.
Heavier than a ruled list; use where each item deserves weight.

**08 · Ledger.** Label left, value right-aligned, hairline between. For specs, prices, metrics,
before/after pairs. Reads as authoritative because it looks like a document — use sparingly for
exactly that reason.

**09 · Consequence chain.** Each row is `cause → effect`, with the effect set in the ink colour and
the cause muted. Excellent for problem slides.

**10 · Negation list.** Rows of "not X — Y." The strikethrough or muted treatment on X carries the
argument. Pairs naturally with `breathe`, since negation lists are usually short.

**11 · Progressive stack.** Rows increase in type size down the card, ending on the conclusion. A
rhetorical build. One per library maximum; it's a trick.

**12 · Annotated stack.** Rows with a small mono annotation hanging in the left margin (dates,
codes, versions). Turns a list into a record.

## Duo / Triad — halves and thirds

**13 · Split compare.** Two full-height halves divided by a rule. Left is the old way, right the
new. The rule must run the full height or the halves stop reading as opposed.

**14 · Asymmetric duo.** 1.6:1 split — a dominant panel and a supporting one. Better than 50/50
whenever the two sides are not genuinely equal, which is most of the time.

**15 · Triad columns.** Three full-height columns, each a heading plus body. The ceiling for
readable columns on a 1080 artboard is three; four is a table.

**16 · Duo with figure.** One half carries a figure at `fig-lg`, the other carries the explanation.
The cleanest way to make a statistic argue for itself.

**17 · Stacked duo.** Two full-width bands, upper and lower, divided by a rule. Same logic as split
compare rotated 90° — use when the content is sequential rather than opposed.

## Grid — tiles

**18 · Quad tiles.** 2×2 filled tiles. Comfortable, safe, over-used. Earn it by making the tiles do
something: figures, icons, or media, not four paragraphs.

**19 · Six grid.** 3×2. The upper limit before tiles become chips. Short labels only.

**20 · Mixed grid.** One tile spans two cells; the rest are single. Breaks the monotony of a plain
quad and creates a focal point a uniform grid can't.

**21 · Icon matrix.** Grid of icon tiles with one-line labels. For capability lists and integration
sets. Needs ≥6 items or it looks unfinished.

**22 · Logo/media wall.** Repeated small media slots in a grid. The `repeated` media role. For
customers, integrations, team.

## Rail — the vertical spine

**23 · Timeline.** Vertical rule with pips, each pip a dated event. One pip in the accent colour
marks "now" or "the turning point" — without that, it's just a list with dots.

**24 · Nested rail.** Rail where some items have sub-items indented beneath. For hierarchies and
phased plans.

**25 · Rail with media.** Rail items that include a small inset image. Heavy; only for cards where
the visual evidence matters.

## Chain — horizontal steps

**26 · Step chain.** Three to five steps left to right, divided by rules, each numbered. The default
process mechanic. Do not exceed five — a six-step chain has 140px columns.

**27 · Arrow flow.** Steps connected by glyph arrows rather than rules. Slightly more diagrammatic;
use when the transformation between steps is the point.

**28 · Funnel chain.** Steps that visibly narrow — decreasing tile widths or decreasing figure
sizes. For conversion, filtering, qualification.

## Strip — full-height columns

**29 · Category strip.** Columns divided by vertical rules, each a category with its items listed
beneath. Denser than a triad because items stack.

**30 · Contrast strip.** Two or three columns where one is visually promoted (tinted, or on plate).
For "these three approaches, and the one we take."

## Overlay — media as the ground

**31 · Full-bleed statement.** Photograph fills the artboard, scrim over it, headline on top. Uses
the `on-photo` treatment so every text role re-colours at once. The scrim is mandatory — text
directly on an uncontrolled photo will eventually be illegible.

**32 · Media sidecar.** Image occupies one side at fixed width, text pane beside it. The pane
**must** have `min-width:0` or it will refuse to shrink and drive text through the frame edge.

**33 · Media header.** Image band across the top third, content beneath. The safest media mechanic
and the right default for "this slide needs a picture."

**34 · Inset frame.** Image inset within the artboard with generous margin and a caption beneath.
Reads as editorial rather than promotional.

**35 · Motif overlay.** The brand motif enlarged and bled off two edges, with text over the
remainder. Identity-heavy; use for covers and section breaks.

## Ledger / data

**36 · Comparison table.** Rows with two or three value columns and a bold total rule at the bottom.
The total rule is what makes it a conclusion rather than a table.

**37 · Bar set.** Horizontal bars with labels, one bar in ink and the rest muted. The single ink bar
is the argument; without it the reader has to do the comparing.

**38 · Index.** Two-column list of label/value pairs. For recaps, contents pages, and spec sheets.
The most information-dense mechanic available.

**39 · Delta card.** Before figure, arrow glyph, after figure, all on one line at figure scale, with
supporting rows beneath. The strongest single mechanic for proving change.

**40 · Score/rating block.** A figure with a qualitative label and a short justification. For
testimonial and evaluation sequences.

---

## Using the catalogue

Do **not** assign mechanics by walking the list in order — that produces a library whose first ten
cards are monoliths. Assign by narrative position (see `SKILL.md` § narrative arc), then check the
tuple table for collisions, then rebalance against the target distribution.

When two cards collide, the cheapest resolution in order of preference:

1. change the **enumerator** (number → pip → icon → chip) — costs nothing, reads as different
2. change the **chrome** (standard → plate → tinted) — free punctuation
3. change the **emphasis carrier** (display → figure → media)
4. change the **partition** — the expensive one; do it only when the content actually wants it

Resolving a collision by changing the *words* is not a resolution. The auditor compares tuples, and
so does the reader's eye.
