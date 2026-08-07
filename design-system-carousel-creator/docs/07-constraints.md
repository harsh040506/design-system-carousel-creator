# 7 · Constraints

Turning what someone asked for in a sentence into something checked on every run.

---

## The problem

Two requests come up constantly:

> "Each page should be individual and not depend on any other page."

> "It shouldn't mention the source."

Both are easy to honour once, by hand, on the day they are asked. Both are easy to regress on
the next edit, and neither leaves any trace that a check ever happened. Someone reviews the
library at 2am three weeks later, skips the manual scan, and ships the leak.

**A constraint only a careful human enforces is not a constraint.** So each one becomes a field
in `project.json` and a code in the linter.

---

## Declaring them

At project creation:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py new "Acme Templates" \
  --independent \
  --no-source \
  --forbid "Acme Confidential" --forbid "Project Bluebird"
```

Or later:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py set constraints.independent_cards true
python ${CLAUDE_PLUGIN_ROOT}/scripts/dscc.py set constraints.forbidden_terms '["Acme Confidential"]'
```

In `project.json`:

```json
{
  "constraints": {
    "independent_cards": true,
    "no_source_attribution": true,
    "forbidden_terms": ["Acme Confidential", "Project Bluebird"],
    "forbidden_patterns": ["\\bdraft\\s+v\\d"],
    "required_terms": ["acme.com"]
  }
}
```

Every audit reports the result:

```
  constraints  forbidden_terms, independent_cards, no_source_attribution  ->  clean
```

---

## `independent_cards` → `CROSS_REFERENCE` (P1)

A card that points at another card fails.

Detected on a phrase list built from real copy, not a thesaurus: `as we saw`, `previously`,
`continued`, `next slide`, `see card 3`, `the chart above`, `in the last slide`, `part two`,
`recall that`, `swipe for`, `keep reading`, and similar.

Patterns are anchored to word boundaries and require enough context to be unambiguous. Bare
directionals need a noun — "the figure below" trips it, "above all" does not.

### The legal fix

**Restate the referenced fact on this card.** Not "delete the sentence."

A card that points elsewhere is a card *missing content*. Deleting the reference leaves it
thinner than it was, which is [the density law](02-concepts.md#4--the-density-law) wearing a
different hat. Pull the fact forward, or pull a claim from the unused pool.

### Why it also improves the work

Carousels are consumed out of order. Someone lands on card 31 from a share and never sees card
30. A library where every card stands alone is more robust to how the format is actually read,
independent of anyone having asked for it.

---

## `no_source_attribution` → `SOURCE_LEAK` (P0)

No title, author, editor, publisher or chapter name anywhere in the artwork.

**P0 rather than P1**, because this is the class of constraint where one violation is a total
failure rather than a degradation. A gate can pass at 96/100 with a scatter of P2s. It cannot
pass with the thing you were asked to remove printed on card 12.

Two mechanisms, both active:

**Forbidden terms** — case-insensitive literals. `--no-source` seeds this list automatically
from your source filenames, because a title removed from every card walks straight back in
through a footer.

**Attribution shapes** — regexes for the forms that survive a term blacklist:

```
edited by · written by · from the book · excerpt from · source: …
chapter N · published by · © 2024 · ISBN · pp. 12 · et al. · ibid
foreword by · afterword by
```

### It checks the chrome too

This is the part people miss. The scan covers the cards **and** everything around them: the
gallery header, the eyebrow, the `<title>` element, the format labels, and `alt` text. Those
are exactly where a removed title reappears — you clear all fifty cards and the document title
still says it.

### A consequence worth stating up front

With `no_source_attribution` on, pull-quotes run **unattributed**, as statements. Attribution
is the only honest alternative and it would name the source. Tell whoever asked for the
constraint that this is the trade, rather than letting them discover it in review.

---

## `forbidden_terms` and `forbidden_patterns`

Independent of `--no-source`, for anything else that must not appear: an internal codename, a
pre-announcement product name, a competitor, a legal phrase.

- `forbidden_terms` — literals, case-insensitive, escaped for you
- `forbidden_patterns` — Python regexes, applied to card text and to the chrome

An invalid regex produces `BAD_CONSTRAINT` (P2) naming the offending entry rather than crashing
the audit.

---

## `required_terms` → `MISSING_REQUIRED` (P1)

The inverse: something that must appear at least once across the library. A handle, a legal
line, a URL. Checked across cards and chrome combined — it needs to exist somewhere, not
everywhere.

---

## How constraints affect the gate

Constraints are **not a scored dimension**. They are worth being true, not worth points.

```
total ≥ 80  AND  min card ≥ 70  AND  zero P0  AND  density ≥ 15
AND  distinction ≥ 11  AND  every declared constraint clean
```

A breach fails the gate regardless of the total. There is no arithmetic in which "no card may
depend on another" is 87% satisfied.

The scorecard records both:

```json
{
  "constraints_checked": ["forbidden_terms", "independent_cards", "no_source_attribution"],
  "constraints_clean": true
}
```

That second field is why a PASS means something specific about what was asked for, rather than
only about geometry.

---

## When a constraint fires on good work

It happens, and the response matters.

A `CROSS_REFERENCE` pattern that matched a bare "back to" once failed a card reading *"Where
surplus goes / Back to members, as a yearly cheque"* — an answer, not a reference.

**Tighten the check. Do not edit the card.** A verifier that fires on known-good input gets
ignored, and an ignored verifier is worse than no verifier: it trains everyone to skim past the
output, including the true positives.

Patterns live in `CROSS_REF_PHRASES` and `ATTRIBUTION_PATTERNS` in
[`scripts/lint.py`](../scripts/lint.py). Both are plain lists.

---

## Testing your constraints

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/lint.py "dist/Acme.dc.html" \
  --project . --out /tmp/lint.json
```

Prints the defect counts in milliseconds, without the browser pass. Fast enough to iterate a
regex against.
