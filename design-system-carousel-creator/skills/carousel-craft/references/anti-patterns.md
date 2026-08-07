# Anti-Patterns

Every known failure mode, its tell, its actual cause, and its fix. Ordered by how much damage it
does. Most were learned expensively; the point of writing them down is that they should never need
to be learned again.

---

## P0 — the library is broken

### Text through the frame edge

**Tell.** A headline or body block visibly clipped or bleeding past the artboard boundary.

**Cause, almost always.** A flex child with `flex:1` and no `min-width:0`. Flex items default to
`min-width:auto`, which means they refuse to shrink below their content's intrinsic width. The
container is 1080px, the pane says "I need 640px minimum," the image says "I need 400px," and
something has to give — so the text just overflows.

**Fix.** `min-width:0` on every flex child that contains text. Not a workaround; it is the correct
declaration. The same applies to `min-height:0` on vertical flex children.

**Why it hides.** It only manifests when the copy is long enough. A layout can pass for twenty cards
and break on the twenty-first.

### Content colliding with chrome

**Tell.** Body text overlapping the masthead or crossing the footer rule.

**Cause.** A content region that isn't `min-height:0`, or absolutely-positioned content measured
against the wrong containing block.

**Fix.** The `.inner` → `.fill` → region chain must carry `min-height:0` at every level. Never
position content absolutely relative to `.frame` unless it is decorative.

### Unbalanced markup

**Tell.** Cards after some index render subtly wrong — inherited plate colours, wrong widths, cards
nesting inside each other.

**Cause.** One missing `</div>` somewhere in three thousand lines.

**Fix.** `dscc lint --balance` counts opening and closing tags per card region. Run it after every
build. Do not attempt to find this by reading.

---

## P1 — the library ships bad work

### The arbitrary gap

**Tell.** Rows in a list separated by 180px, 210px, 224px. No two cards agree.

**Cause.** `justify-content:space-between` on an under-written card. The gaps are leftover space
divided by row count — nobody chose them.

**Fix.** Add real rows from the claim inventory. See `density-law.md`.

**Explicitly not the fix.** Reducing the gap, adding padding, enlarging type to fill, or switching
the whole library to top-alignment. The last one is a real temptation and it trades one bad default
for another — most cards *should* fill.

### Over-correcting a scoped instruction

**Tell.** A fix requested for four specific cards has been applied to all fifty.

**Cause.** Reading "these cards should leave space at the bottom" as a global design principle
rather than a per-card note.

**Fix.** Scope changes to the cards named. When a fix seems to want to be global, that is a claim
about the whole library and needs to be stated and confirmed as one — not assumed.

### Duplicate layouts

**Tell.** Three question-and-answer cards that differ only in wording. Two timelines. Four 2×2 grids
that are interchangeable.

**Cause.** Building cards one at a time. Each is a reasonable local choice; the set is repetitive
and you never see the set.

**Fix.** Plan all fifty tuples in a table before building. Check collisions mechanically
(`dscc uniq`). Resolve by changing enumerator, chrome, emphasis, or partition — in that order of
cost. Changing the words is not a resolution.

### Scale drift

**Tell.** An audit finds twenty distinct `margin-top` values, eighteen `gap` values, twelve one-off
display sizes.

**Cause.** Fifty cards built over multiple sessions, each with a local judgement call that was
individually defensible.

**Fix.** Lock the scales up front, forbid raw values in card markup, and let the linter enforce it.
Retrofitting is possible but expensive — it means touching every card.

**Prevention beats cure by an order of magnitude here.** This is the strongest argument for doing
distillation properly before drawing anything.

### Website chrome in a social post

**Tell.** Buttons. "Get started." Pricing tiers with feature checklists. Nav bars. Sign-up forms.
Tabs.

**Cause.** The brand's design system *is* a web design system, and its components are all web
components. Applying it faithfully produces web UI.

**Fix.** Translate, don't apply. A CTA button becomes a tag or a bold closing line. A pricing card
becomes a ledger. A nav bar becomes a masthead. A feature grid becomes an icon matrix. The token
layer transfers directly; the component layer must be re-imagined for a medium where nothing is
clickable.

### Copy that reads like a report

**Tell.** Full sentences with subordinate clauses. Body text at 21px. Paragraphs.

**Cause.** Source material pasted in rather than edited down.

**Fix.** Headlines under nine words. Body rows under twenty. Every slide states one claim. If the
copy needs a subordinate clause to make sense, it is two slides.

### Invented facts

**Tell.** A statistic in a slide that appears nowhere in the source documents.

**Cause.** Writing from memory of the material rather than from an extracted inventory, then
reaching for a plausible-sounding number to fill a figure slot.

**Fix.** Every text node traces to a claim ID. The auditor checks it. A figure slot with no backing
claim is a defect, not an opportunity.

---

## P2 — the library is worse than it should be

### Decorative elements counted as content

**Tell.** The auditor reports a card as overflowing, and the card looks fine.

**Cause.** A motif that intentionally bleeds off the edge is measured as content overflow.

**Fix.** Exclude `.motif, .dot-grid, .bleed, .scrim` and their descendants from geometry checks.
Bleeding decoration is the intent, not the bug. `measure.py` already does this — the note is here so
nobody "fixes" it back.

### Two focal points

**Tell.** The card is legible but the eye doesn't know where to start.

**Cause.** A display headline *and* a hero figure *and* a full-width image, all fighting.

**Fix.** Demote everything but one. The demoted elements are usually still doing their job a step
down the ramp.

### The uniform box grid

**Tell.** Everything is in a rounded rectangle. The card reads as a dashboard.

**Cause.** Panels used as the default separator.

**Fix.** Hairline rules separate at a fraction of the visual cost. Reserve filled panels for genuine
figure/ground changes — when everything is a box, nothing has weight.

### Flat gradient

**Tell.** The motif looks like a CSS default.

**Cause.** It is a CSS default.

**Fix.** `feTurbulence` noise as a data-URI, `mix-blend-mode:overlay`, ~0.75 opacity. Two lines.

### Plate cards clustered

**Tell.** Cards 26–30 are all inverted; the rest of the library is uniformly light.

**Cause.** Assigning chrome by category rather than by rhythm.

**Fix.** Distribute plate cards every 4–6 slides across the whole sequence. They are punctuation;
punctuation doesn't cluster.

### Concluding line floating mid-card

**Tell.** A summarising sentence sits between two list rows and reads as a third row.

**Cause.** It was written in document order and placed in document order.

**Fix.** `.note` — `margin-top:auto`, pinned above the footer rule. A conclusion belongs at the end
of the card, spatially as well as sequentially.

---

## Process anti-patterns

### Measuring the wrong thing and trusting it

An early harness reported every card as "very tight" — it was measuring the distance to the footer
*element* rather than to the footer's top rule, and counting the decorative motif as content. Both
produced confident, precise, wrong numbers.

**Rule.** When a measurement contradicts the eye, suspect the measurement first. Verify the harness
against three cards you have looked at closely before trusting it on fifty you haven't.

### Fixing symptoms because they are closer

Every defect in the P1 list has a cosmetic fix that makes the symptom disappear in under a minute
and makes the library worse. The gap-adjustment fix for `UNDERWRITTEN` is the archetype. The
auditor's defect names are chosen to name the *cause* — `UNDERWRITTEN`, not `SPACING` — because the
name is what determines which fix gets reached for.

### Non-ASCII in tooling output on Windows

`UnicodeEncodeError: 'charmap' codec can't encode character '→'`. Set
`PYTHONIOENCODING=utf-8`, or keep script output ASCII. Arrows in a progress message are not worth a
crashed audit run.

---

## Build-tooling failure modes

These are failures in the *generator*, not in a card — but each one silently corrupts every card it
touches, so they belong in this catalogue rather than in a separate document nobody reads.

### The sticky style layer

Patching the document in place and guarding the CSS insert with a marker check:

```python
if "BRAND LAYER" not in doc:      # looks careful, is a trap
    doc = insert_css(doc)
```

is idempotence in the wrong shape for a generator. After the first successful build the condition is
never true again, so every subsequent edit to the CSS silently does not reach the output. The symptom
is indistinguishable from the edit not working, which sends the search into the CSS instead of the
build script.

**Rule.** Re-scaffold from scratch on every build. Regeneration is cheap and it cannot go stale.

### Injection ordering

Writing ground tokens into `:root` *after* the CSS layer is inserted, guarded by
`if "--gp-bg" not in doc`, fails silently: the CSS layer's own `var(--gp-bg)` uses satisfy the guard,
so the tokens are never written and the document fills with `UNDECLARED_VAR` P0s — pointing at a file
that, read on its own, looks correct.

**Rule.** Declare before you reference. Guard on a declaration-shaped sentinel (`"    --gp-bg: "`),
never on a bare token name, which appears on both sides of the assignment.

### A decorative character read as a statistic

`&#9671;` in a footer survives naive tag-stripping as the literal characters `& # 9 6 7 1 ;`. A
veracity check built on that extraction reads `9671` as a figure, cannot find it in the brief, and
emits `INVENTED_FIGURE` (P0) — once per card that carries the same decoration, which is a gate failure
from a single lozenge.

**Rule.** Never emit numeric HTML entities. The document is UTF-8: write `◇`. `lint.py` unescapes
before extracting text, and the emitted builder asserts no `&#\d+;` survives.

### box-sizing on a fixed artboard

`.frame` sets `width`, `height` **and** `padding` with no declared `box-sizing`. Under content-box the
padding is *added*: a 1080×1440 artboard renders at 1216×1553. Nothing errors, and a geometry harness
measures the wrong box, so coverage, gaps and slack are all computed against an artboard that does not
exist.

**Rule.** The artboard is a contract. `box-sizing:border-box` on `.frame` and its descendants is part
of it, not a style preference. In `kernel.css`.

### The linter flagging what it told you to copy

A scale check that inspects every declaration outside `:root`, including the kernel that the skill
instructs you to copy verbatim, produces defects the user is explicitly forbidden to fix.

**Rule.** A tool must not contradict its own instructions. The kernel carries
`dscc:kernel-begin` / `dscc:kernel-end` sentinels and the scale check skips between them.

### A check that cries wolf

A `CROSS_REFERENCE` pattern that matches a bare `back to` fails a card reading *"Where surplus goes /
Back to members, as a yearly cheque"* — an answer, not a reference.

**Rule.** A verifier that fires on known-good input gets ignored, which is worse than not having one.
Tighten the pattern; do not edit the card to satisfy it. (`scaffold.py`'s `setProperty` scan carries
the same note for the same reason.)

### A bundle nobody can open

A library can ship correct, complete, and inert: a `.dc.html` expects a host application to supply the
canvas, the zoom and the prop editor, and a static server supplies none of them. It renders and does
nothing, with no error — which reads as a script failure even though nothing is broken.

**Rule.** Ship the host. `scaffold init` installs `canvas.html` into the bundle and the pipeline ends
at `dscc preview`. A library nobody has looked at is not finished.

### A theme-neutral colour that is nothing of the kind

See `theming.md`. A colour fill declared once in `:root` and made ground-aware but not theme-aware
is a dark disc under dark type in one theme and the exact mirror of that in the other — invisible
while looking at either theme alone.

**Rule.** Every colour used in card markup lives in **both** theme maps. `MONO_THEME_TOKEN` (P1).
