# 9 · Defect reference

Every code the auditor emits, what causes it, and the one legal fix.

Each defect object carries `code`, `severity`, `dim`, `detail`, `legal_fix`, and usually `card`.

| Severity | Meaning |
|---|---|
| **P0** | fails the gate outright, regardless of the total |
| **P1** | costs real points; fix before shipping |
| **P2** | accepted-but-noted; fails the gate only under `--strict` |

> **The defect names name causes, not symptoms.** `UNDERWRITTEN`, not `SPACING`. That is
> deliberate: the name is what determines which fix gets reached for, and every P1 below has a
> cosmetic fix that clears the check in under a minute and makes the library worse. Those are
> the "not this" columns.

---

## Integrity

### `OVERFLOW` · P0
A box extends past the artboard edge.

**Fix:** `min-width: 0` on the flex child holding the text; shorten the headline.
**Not:** `overflow: hidden` — that hides the symptom and keeps the broken layout.

Usually latent: it appears only once the copy is long enough, so a layout passes for twenty
cards and breaks on the twenty-first.

### `COLLISION` · P0
Two text boxes overlap.

**Fix:** restore `min-height: 0` on the `.inner` / `.fill` chain.

### `UNBALANCED` · P0
A tag is never closed. Reported with a line number.

**Fix:** close the tag at that line. Run `lint.py` every ten cards — at card 12 this is a
minute, at card 50 it is an hour of bisecting.

### `UNDECLARED_VAR` · P0
A `var(--x)` with no fallback and no `--x:` declaration or `setProperty('--x', …)` anywhere in
the document. `var(--x, fallback)` is not flagged.

**Fix:** declare the token, or use an existing role.

A wave of these usually means [injection ordering](08-authoring.md#2--tokens-into-root-before-the-css-layer)
— the tokens were never written because a guard matched the CSS layer's own usage.

### `EMPTY_SLOT` · P1
A media slot renders under 100 × 100.

**Fix:** give the slot an explicit height and aspect ratio. A slot sized only by its content
collapses.

---

## Discipline

### `RAW_PX` · P1
A raw pixel value in card markup. Only `0`, `1` and `2` are legal (hairlines and zero).

**Fix:** replace with a spacing-scale token.

### `RAW_HEX` · P1
A raw colour in card markup.

**Fix:** replace with a colour-role token. A card naming a role is correct across all twelve
ground × theme states; a card carrying a hex is correct in one.

### `INLINE_TYPE` · P1
An inline `font-size`.

**Fix:** move to one of the nine type classes. This is what makes a library re-typable by
editing nine numbers.

### `OFF_SCALE` · P2
A pixel value in the stylesheet that is not on any declared scale. The scorecard lists the
values in one entry; the points themselves come from the number of distinct computed font sizes
and gaps.

**Fix:** collapse to the nearest locked step.

The kernel is exempt — it sits between `dscc:kernel-begin` / `dscc:kernel-end` sentinels and the
check skips it, because flagging a file you are instructed to copy verbatim would be the tool
contradicting itself.

### `WEB_CHROME` · P1
A `<button>`, `<nav>`, `<form>`, `<input>`, `<select>`, `<dialog>` or similar in an artboard.

**Fix:** translate it. A CTA becomes a tag or a closing line; a pricing card becomes a ledger;
a feature grid becomes an icon matrix.
**Not:** style the button to look less like a button.

### `WEB_CHROME_COPY` · P2
Call-to-action or pricing copy — "sign up", "book a demo", "per month", "billed annually".

**Fix:** rewrite it as a statement.

### `MONO_THEME_TOKEN` · P1
A colour-valued property declared in `:root`, used in card markup, and present in **neither**
branch of `applyTheme()`. On a two-theme document it is provably wrong in one of them.

**Fix:** put the token in **both** theme maps.
**Not:** pick one colour that is acceptable in both — it clears the check and produces a library
where nothing is quite right anywhere.

See [`theming.md`](../skills/carousel-craft/references/theming.md).

---

## Density

### `SPARSE` · P1
Ink coverage below 40%.

**Fix:** add content from the claim inventory, enlarge the media, promote a figure.
**Not:** stretch the existing rows apart.

### `UNDERWRITTEN` · P1
Max row gap exceeds 1.5 × rhythm.

**Fix:** **add a row from the claim inventory.**
**Not:** adjust spacing. Explicitly disallowed — see [the density law](02-concepts.md#4--the-density-law).

The gap is a *symptom* of missing content. Closing it by moving rows together leaves a card
that is still under-written and now also cramped.

### `UNLICENSED_SLACK` · P1
Bottom slack over 160px with no declared license.

**Fix:** declare `data-intent="breathe"` with a legal `data-license`, or fill the card.
Legal licenses: `cover`, `close`, `single-figure`, `media-led`, `few-rows`, `section-break`.

### `FALSE_LICENSE` · P1
A `few-rows` license on a card with more than 14 measured content boxes.

**Fix:** remove the license and fill.
**Not:** widen what the license means.

### `OVERPACKED` · P2
A text-dominant card above 88% ink coverage.

**Fix:** split into two cards — it is carrying more than one idea.
**Not:** shrink the type.

Full-bleed media cards are exempt; they cover the artboard by design.

### `CROWDED` · P2
Less than 24px between the lowest content and the footer rule. A `.note` pinned to the rule is
exempt.

**Fix:** cut a row or shorten copy.

### `GAP_VARIANCE` · P2
Library-wide gap coefficient of variation above 0.35.

**Fix:** normalise the outlier cards to `--rhythm`.

Systemic rather than per-card — usually composite cards on a fixed gap alongside ruled stacks
that distribute. No single card would reveal it.

---

## Distinction

### `DUP_LAYOUT` · P1
Two or more cards share a mechanic tuple.

**Fix, in this order:** change the enumerator → the chrome → the emphasis → the partition.
**Not:** rewrite the copy. Different words in the same structure is the same slide.

### `LOW_VARIETY` · P1
Mean pairwise Hamming distance below 2.6. Every pair differs on one axis: technically legal,
reads as repetitive.

**Fix:** vary a second axis on the closest pairs.

### `NARROW_RANGE` · P2
Fewer than eight of the ten partitions are used.

**Fix:** move cards onto unused partitions.

### `OVERUSED` · P2
One partition carries more than nine cards.

**Fix:** move the excess cards onto unused partitions.

### `MIX_OFF` · P2
The media, figure or ground counts are outside the target mix (scaled to the library's size).

**Fix:** re-plan those assignments toward the target.

### `BAD_AXIS` · P2
A mechanic axis value that is not in the vocabulary in
[`mechanics.md`](../skills/carousel-craft/references/mechanics.md). Usually a typo in the plan.

### `DUP_NAME` · P2
Two cards share a layout name. Names are how the plan, the builder and the report refer to a
card, so a duplicate makes every one of those references ambiguous.

### `FLAT_SURFACES` · P1
Fewer than five distinct grounds. Costs 5 Distinction points, so even a perfect 15 drops to 10 and
fails the Distinction ≥ 11 gate on its own.

**Fix:** assign more grounds. This is the highest-leverage move for perceived range and the one
generated libraries most consistently skip.

### `GROUND_CLUSTER` · P2
Two adjacent cards on the **same** loud ground (`ink`, `accent-1` or `accent-2`). Costs 1 Distinction point per
pair, to a maximum of 2.

**Fix:** move one of the pair, or give it another ground.

### `SLACK_REVIEW` · P2
A card with a legal `breathe` license and more than 520px of bottom slack that the critic has not
signed off. It clears when the card's index appears in `slack_signoff` in `critic.json`, or when the
card is filled.

---

## Veracity

### `UNSOURCED` · P1
A card with no `data-claim` ids, or ids not present in the brief.

**Fix:** attach a claim id, or cut the text.

### `INVENTED_FIGURE` · P0
A number on a card that does not appear anywhere in the brief.

**Fix:** source the number from the brief, or remove it.

**If you see this on every card at once, suspect a decorative character.** A numeric HTML entity
like `&#9671;` in a shared footer survives tag-stripping as `9671` and reads as a figure. Write
literal characters — the document is UTF-8.

A claim's `figure` field counts as brief text, so a number that lives only there is sourced.

### `CLAIM_REUSE` · P2
One or more claims carried by more than two cards. Costs the 1 Veracity point for claim spread.

**Fix:** draw a different claim from the unused pool.

---

## Constraints

Only active when declared in `project.json`. A breach fails the gate whatever the total says.
See [Constraints](07-constraints.md).

### `CROSS_REFERENCE` · P1
A card depends on having read another.

**Fix:** **restate** the referenced fact on this card.
**Not:** delete the sentence — that leaves the card thinner than it was.

### `SOURCE_LEAK` · P0
A forbidden term or attribution shape, in a card **or** in the chrome (header, eyebrow,
`<title>`, format labels). Attribute values such as `alt` are not scanned.

**Fix:** remove it, including from the chrome — that is where a removed title reappears.

### `MISSING_REQUIRED` · P1
A required term appears nowhere in the library.

### `BAD_CONSTRAINT` · P2
An entry in `forbidden_patterns` is not a valid regex. Named rather than crashing the audit.

---

## Meta

### `NO_CRITIC` · P2
No `critic.json`, so Craft's twenty points are unscored and the total is scaled up from
the deterministic points that could be scored (80 with a content brief, 70 without).

**Fix:** run the `design-critic` agent over `shots/` and re-score with `--critic`.

Present in the defect list rather than as a footnote, because a scaled total presented as
though it were a full 100 is the exact dishonesty the benchmark caveats exist to prevent.
Under `--strict` it fails the gate.

---

## Media slots

Reported by `scripts/slots.py audit`, not by the scorecard. It exits non-zero on a P0.

| Code | Severity | Means |
|---|---|---|
| `EMPTY_SLOT` | P1 | a slot has no `src` yet (the scorecard's `EMPTY_SLOT` is the rendered-size check above) |
| `BROKEN_SLOT` | P0 | a relative `src` points at a file that does not exist |
| `REMOTE_SLOT` | P1 | an `http(s)` `src` — the bundle must render offline, so copy the file in |
| `VAGUE_PLACEHOLDER` | P2 | the placeholder says "image" or "photo" instead of describing the subject |

---

## Per-card scoring

Each card starts at 100 and loses:

| | |
|---|---|
| `OVERFLOW` | −25 |
| `COLLISION` | −20 |
| `SOURCE_LEAK` | −20 |
| `INVENTED_FIGURE` | −15 |
| `SPARSE` | up to −14, scaled by how far below the floor |
| `CROSS_REFERENCE` | −12 |
| `UNDERWRITTEN` | up to −12, scaled by how far past the ceiling |
| `UNLICENSED_SLACK` | −10 |
| `WEB_CHROME` | −8 |
| `UNSOURCED` | −6 |
| `OVERPACKED` | −5 |
| `CROWDED` | −4 |
| `EMPTY_SLOT` | −3 |
| Craft (with a critic) | −1.2 × (20 − the card's craft points) |

Gate floor is 70 per card. The weakest card matters more than the average — a reader hits it
and the whole set loses credibility.

---

## When a defect is wrong

Suspect the measurement first, then say so. A harness can be confidently, precisely wrong:
measuring to a footer element rather than its top rule, or counting a card's background surface
as content.

Verify against three cards you have actually looked at before trusting it on fifty you haven't.
**If the harness is wrong, fix the harness** — do not quietly work around it, and do not "fix"
the library to satisfy a broken check.

The same applies to a check that fires on good work: tighten the check. A verifier that cries
wolf gets ignored, which is worse than not having one.
