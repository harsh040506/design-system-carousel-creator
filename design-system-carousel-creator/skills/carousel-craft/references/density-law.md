# The Density Law

> **A sparse card is under-written, not over-spaced.**

This document exists because this is the rule that gets broken most, breaks most subtly, and is
hardest to un-learn once a library has been built the wrong way.

---

## The failure it prevents

A card has five rows of content and room for seven. There are two moves:

**Move A — distribute.** `justify-content: space-between`. The five rows spread out, the card looks
full, nothing is empty. This is the instinct, and it is wrong.

**Move B — write.** Go back to the claim inventory, find two more real rows, add them.

Move A produces gaps of 180px, 210px, 224px between rows. Nobody chose those numbers — they are
whatever was left over divided by four. A reader cannot articulate what's wrong, but the card feels
*loose*, and worse, the gaps are different on every card in the library, so the set loses its
rhythm. The design system is intact on paper and visibly broken on screen.

Move B produces a card that says more.

The auditor therefore emits **`UNDERWRITTEN`**, never "spacing issue," and the refiner is explicitly
forbidden from resolving it by changing spacing. That constraint is the whole point: if the fix
were allowed to be cosmetic, it always would be.

---

## The default: fill

Content regions **fill** by default. `flex:1` on the region, `justify-content:space-between` or
`align-content:space-between` on the rows, `grid-template-rows:repeat(n,minmax(0,1fr))` on grids.

This is correct when the leftover space is small — the rows then land on a regular rhythm and read
as a deliberate table rather than an accident. Filling is right for roughly 40 of 50 cards.

**Legal gap ceiling: 1.5 × `--rhythm`** (96px at the default 64px rhythm). Above that, filling has
stopped distributing and started inventing. That card is under-written; go to Move B.

---

## The opt-out: breathe

Some cards genuinely carry few rows, and distributing four rows across 900px produces exactly the
loose gaps described above no matter how well written they are. Those cards use the `-top`
modifier: rows keep a fixed rhythm from the top, and **all the leftover space collects at the bottom
as one clean block.**

One 400px block of quiet under the content is a compositional decision. Four 100px gaps between rows
are an accident. Same slack, opposite readings.

### The license list

`intent: "breathe"` is legal **only** for:

| License | Why |
|---|---|
| `cover` | The hook slide wants air under a huge headline. Filling a cover makes it a contents page. |
| `close` | The final slide is a landing, not a table. Content sits centred or high; the bottom is quiet. |
| `single-figure` | One giant number plus a label. Distributing two elements is meaningless. |
| `media-led` | An image occupies the upper region; text sits beneath it and stops. |
| `few-rows` | ≤4 content rows, verified. Not "it looked better" — counted. |
| `section-break` | Structural dividers are deliberately minimal. |

Anything else is unlicensed slack, which is a defect.

### The license is recorded, not remembered

The manifest carries `intent` and `license` per card. The auditor cross-checks: a card using `-top`
without a declared license fails `UNLICENSED_SLACK`; a card declaring `few-rows` with six rows fails
`FALSE_LICENSE`. This prevents the license from decaying into "I'll mark them all breathe."

---

## Ink coverage

**≥40% of every artboard must be occupied by meaningful content** — text, media, figures, panels,
diagrams, icons. Chrome (masthead, footer) does not count. Decorative motifs count at half weight.

Measured by rasterising the artboard into a 40×50 cell grid and marking every cell intersected by a
content box. This is an approximation of true union area and deliberately so — it is stable across
runs, cheap, and errs slightly generous, which keeps it from becoming a nuisance metric.

Coverage below 40% is `SPARSE` and, again, is resolved by writing.

The upper bound matters too. Above ~78% a card has no breathing room at all and reads as a wall;
that emits `OVERPACKED`, resolved by splitting the card in two — which is usually the right answer,
since it means the card was carrying more than one idea.

---

## Gap variance

Beyond the per-card ceiling, the auditor measures **gap variance across the library**. A set where
one card's rows sit 64px apart and the next card's sit 130px apart has no rhythm even if every
individual card passes. Coefficient of variation over all inter-row gaps should be ≤0.35.

This is the check that catches slow drift — the kind that accumulates over fifty cards built across
several sessions and is invisible when looking at any two of them side by side.

---

## Bottom slack, precisely

`bottom_slack` = distance from the lowest content box's bottom edge to the top of the footer rule.

| Slack | Verdict |
|---|---|
| < 24px | `CROWDED` — content is jammed into the footer, add breathing room |
| 24–160px | normal, no comment |
| 160–520px | requires a declared license |
| > 520px | requires a license **and** a critic sign-off; this much quiet is a strong statement and needs to be an intentional one |

---

## Summary of enforcement

| Defect | Severity | Legal fix | Illegal fix |
|---|---|---|---|
| `UNDERWRITTEN` (gap > 1.5×rhythm) | P1 | add a real row from the brief | change spacing, shrink type, add padding |
| `SPARSE` (coverage < 40%) | P1 | add content, enlarge media, promote a figure | stretch existing rows |
| `UNLICENSED_SLACK` | P1 | declare a license, or fill | leave it |
| `FALSE_LICENSE` | P1 | remove the license and fill | widen the license definition |
| `OVERPACKED` (coverage > 78%) | P2 | split into two cards | shrink type |
| `CROWDED` (slack < 24px) | P2 | cut a row, or shorten copy | reduce the footer margin |
| `GAP_VARIANCE` (library CV > 0.35) | P2 | normalise the outlier cards to the rhythm | adjust `--rhythm` to fit the mess |
