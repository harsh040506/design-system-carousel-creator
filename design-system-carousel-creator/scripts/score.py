"""
Design System Carousel Creator -- the quality scorecard.

Merges lint.json + measure.json + uniq.json (+ optional critic.json and
content-brief.json) into one scored, gated verdict.

Six dimensions, 100 points. Eighty are computed here from measurements and are
identical on every run; twenty come from the critic agent. The split is the
point: a model reading a screenshot will say "spacing looks consistent" while
three cards differ by 60px, and it cannot see 4px of overflow at all. Give those
to arithmetic and reserve judgement for what needs taste.

Usage:
    python score.py --lint lint.json --measure measure.json --uniq uniq.json
                    [--critic critic.json] [--brief content-brief.json]
                    [--out scorecard.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent


def plugin_version() -> str:
    """The one version string, read from the plugin manifest.

    Recorded on every scorecard and history row: a scoring rule that changes between
    versions makes totals from either side incomparable, and the record should say so.
    """
    try:
        man = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return str(man.get("version") or "unknown")
    except (OSError, ValueError):
        return "unknown"


WEIGHTS = {"integrity": 20, "discipline": 15, "density": 20,
           "distinction": 15, "veracity": 10, "craft": 20}

GATE = {"total": 80, "min_card": 70, "density": 15, "distinction": 11}

COVERAGE_FLOOR = 0.40
COVERAGE_CEIL = 0.88          # calibrated: see schema/calibration.json
SLACK_FREE = 160          # px of bottom slack needing no license
SLACK_REVIEW = 520        # px of licensed slack that also needs critic sign-off
# A figure is digits with internal separators only: "2024," or "40." at the end of
# a sentence is the number 2024 or 40, not an invented figure.
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
LEGAL_LICENSES = {"cover", "close", "single-figure", "media-led",
                  "few-rows", "section-break"}

LEGAL_FIX = {
    "OVERFLOW": "add min-width:0 to the flex child holding text; shorten the headline",
    "COLLISION": "restore min-height:0 on the .inner/.fill chain",
    "UNBALANCED": "close the tag reported at the given line",
    "UNDECLARED_VAR": "declare the token in :root, or use an existing role",
    "EMPTY_SLOT": "give the media slot an explicit height and aspect ratio",
    "RAW_PX": "replace with a spacing-scale token",
    "RAW_HEX": "replace with a colour-role token",
    "INLINE_TYPE": "move to one of the nine type classes",
    "OFF_SCALE": "collapse to the nearest locked scale step",
    "SPARSE": "ADD CONTENT from the claim inventory -- do not stretch what is there",
    "UNDERWRITTEN": "ADD A ROW from the claim inventory -- adjusting spacing is not a fix",
    "UNLICENSED_SLACK": "declare a license from the list, or fill the card",
    "FALSE_LICENSE": "remove the license and fill; do not widen the definition",
    "OVERPACKED": "split into two cards -- it is carrying more than one idea",
    "CROWDED": "cut a row or shorten copy",
    "GAP_VARIANCE": "normalise the outlier cards to --rhythm",
    "DUP_LAYOUT": "change enumerator, then chrome, then emphasis, then partition",
    "LOW_VARIETY": "vary a second axis on the closest pairs",
    "NARROW_RANGE": "move cards onto unused partitions until at least eight are in play",
    "OVERUSED": "move the excess cards of that partition onto unused ones",
    "MIX_OFF": "re-plan media, figure or ground assignments toward the target mix",
    "FLAT_SURFACES": "assign more named grounds (panel, ink, accent-1, accent-2, grey)",
    "GROUND_CLUSTER": "move one card of the pair, or give it a quieter ground",
    "BAD_AXIS": "use a value from the mechanic vocabulary in mechanics.md",
    "DUP_NAME": "give every layout a unique name",
    "WEB_CHROME": "translate the component: a button becomes a tag or a closing line",
    "WEB_CHROME_COPY": "rewrite as a statement; a carousel card does not sell a plan",
    "UNSOURCED": "attach a claim id, or cut the text",
    "INVENTED_FIGURE": "source the number from the brief, or remove it",
    "CLAIM_REUSE": "draw a different claim from the unused pool; no claim carries more than two cards",
    # constraints and theming
    "CROSS_REFERENCE": "RESTATE the referenced fact on this card -- a cross-reference "
                       "is a card missing content; deleting the sentence is not a fix",
    "SOURCE_LEAK": "remove the attribution, including from labels, chrome and <title>",
    "MISSING_REQUIRED": "add the required term once, in the closing card or the footer",
    "MONO_THEME_TOKEN": "put the token in BOTH theme maps -- do not compromise on one "
                        "colour that is mediocre in each",
    "BAD_CONSTRAINT": "fix the regex in project.json constraints.forbidden_patterns",
    "SLACK_REVIEW": "have the design-critic sign the card off (slack_signoff), or fill it",
    "NO_CRITIC": "run the design-critic agent over shots/ and re-score with --critic",
}

# Deterministic dimensions each defect belongs to, used for reporting and for the
# strict-mode gate. A defect nobody can attribute to a dimension is a defect nobody
# prioritises.
DEFECT_DIM = {
    "OVERFLOW": "integrity", "COLLISION": "integrity", "UNBALANCED": "integrity",
    "UNDECLARED_VAR": "integrity", "EMPTY_SLOT": "integrity",
    "RAW_PX": "discipline", "RAW_HEX": "discipline", "INLINE_TYPE": "discipline",
    "OFF_SCALE": "discipline", "WEB_CHROME": "discipline", "WEB_CHROME_COPY": "discipline",
    "MONO_THEME_TOKEN": "discipline",
    "SPARSE": "density", "UNDERWRITTEN": "density", "UNLICENSED_SLACK": "density",
    "FALSE_LICENSE": "density", "OVERPACKED": "density", "CROWDED": "density",
    "SLACK_REVIEW": "density",
    "GAP_VARIANCE": "density",
    "DUP_LAYOUT": "distinction", "LOW_VARIETY": "distinction",
    "OVERUSED": "distinction", "MIX_OFF": "distinction", "NARROW_RANGE": "distinction",
    "FLAT_SURFACES": "distinction", "GROUND_CLUSTER": "distinction",
    "BAD_AXIS": "distinction", "DUP_NAME": "distinction",
    "UNSOURCED": "veracity", "INVENTED_FIGURE": "veracity", "CLAIM_REUSE": "veracity",
    "CROSS_REFERENCE": "constraints", "SOURCE_LEAK": "constraints",
    "MISSING_REQUIRED": "constraints", "BAD_CONSTRAINT": "constraints",
}


def _grade(value, full_at, zero_at, points):
    """Linear points between two thresholds; direction inferred."""
    if full_at == zero_at:
        return points if value == full_at else 0.0
    if full_at < zero_at:                      # lower is better
        if value <= full_at:
            return points
        if value >= zero_at:
            return 0.0
        return points * (zero_at - value) / (zero_at - full_at)
    if value >= full_at:                       # higher is better
        return points
    if value <= zero_at:
        return 0.0
    return points * (value - zero_at) / (full_at - zero_at)


def score(lint: dict, measure: dict, uniq: dict,
          critic: dict | None = None, brief: dict | None = None,
          strict: bool = False) -> dict:
    cards = measure.get("cards", [])
    n = max(1, len(cards))
    lib = measure.get("library", {})
    ceiling = lib.get("gap_ceiling", 96)
    counts = lint.get("counts", {})
    defects: list[dict] = []

    def add(code, severity, detail, card=None):
        d = {"code": code, "severity": severity, "detail": detail,
             "dim": DEFECT_DIM.get(code, ""), "legal_fix": LEGAL_FIX.get(code, "")}
        if card is not None:
            d["card"] = card
        defects.append(d)

    # ── INTEGRITY ────────────────────────────────────────────────────────
    ok_overflow = ok_collide = ok_slots = 0
    for c in cards:
        if c["overflow"]:
            add("OVERFLOW", "P0", f"{len(c['overflow'])} box(es) past the artboard: "
                                  f"{c['overflow'][0]['cls'][:50]}", c["index"])
        else:
            ok_overflow += 1
        if c["collisions"]:
            add("COLLISION", "P0", f"{len(c['collisions'])} overlapping text box pair(s)", c["index"])
        else:
            ok_collide += 1
        if c.get("tiny_media", 0):
            add("EMPTY_SLOT", "P1", f"{c['tiny_media']} media slot(s) under 100x100", c["index"])
        else:
            ok_slots += 1

    unbalanced = counts.get("UNBALANCED", 0)
    undeclared = counts.get("UNDECLARED_VAR", 0)
    for d in lint.get("defects", []):
        if d["code"] in ("UNBALANCED", "UNDECLARED_VAR"):
            add(d["code"], "P0", d.get("detail", ""), d.get("card"))

    integrity = (6 * ok_overflow / n + 5 * ok_collide / n +
                 (4 if not unbalanced else 0) + (3 if not undeclared else 0) +
                 2 * ok_slots / n)

    # ── DISCIPLINE ───────────────────────────────────────────────────────
    for code in ("RAW_PX", "RAW_HEX", "INLINE_TYPE"):
        if counts.get(code):
            add(code, "P1", f"{counts[code]} occurrence(s) across the library")
    # Web chrome is a per-card failure (it costs the card 8), so it keeps its card.
    for d in lint.get("defects", []):
        if d["code"] in ("WEB_CHROME", "WEB_CHROME_COPY"):
            add(d["code"], d.get("severity", "P1"), d.get("detail", ""), d.get("card"))
    for d in lint.get("defects", []):
        if d["code"] == "MONO_THEME_TOKEN":
            add(d["code"], d.get("severity", "P1"), d.get("detail", ""))
    # Stylesheet values off every declared scale. The points come from the computed
    # spread below; this entry names the values so the drift can actually be found.
    off = [d.get("detail", "").split("px")[0] for d in lint.get("defects", [])
           if d["code"] == "OFF_SCALE"]
    if off:
        add("OFF_SCALE", "P2", f"{len(off)} stylesheet value(s) off every declared scale: "
                               f"{', '.join(p + 'px' for p in off[:8])}")
    discipline = (
        4 * (1 - min(1.0, counts.get("RAW_PX", 0) / n)) +
        3 * (1 - min(1.0, counts.get("RAW_HEX", 0) / n)) +
        3 * (1 - min(1.0, counts.get("INLINE_TYPE", 0) / n)) +
        _grade(lib.get("distinct_font_sizes", 99), 11, 22, 3) +
        _grade(lib.get("distinct_gaps", 99), 8, 20, 2)
    )
    # A colour that cannot follow the theme is a discipline failure, not a taste
    # one: on a two-theme document it is provably wrong in one of them.
    discipline = max(0.0, discipline - 1.5 * min(2, counts.get("MONO_THEME_TOKEN", 0)))

    # ── DENSITY ──────────────────────────────────────────────────────────
    ok_cov = ok_gap = ok_slack = ok_pack = 0
    signoff = {int(i) for i in (critic or {}).get("slack_signoff", [])
               if isinstance(i, (int, float))}
    for c in cards:
        cov = c["coverage"]
        if cov >= COVERAGE_FLOOR:
            ok_cov += 1
        else:
            add("SPARSE", "P1", f"ink coverage {cov:.0%} < {COVERAGE_FLOOR:.0%}", c["index"])
        if c["max_row_gap"] <= ceiling:
            ok_gap += 1
        else:
            add("UNDERWRITTEN", "P1",
                f"max row gap {c['max_row_gap']}px > {ceiling}px ceiling", c["index"])

        slack, lic, intent = c["bottom_slack"], c.get("license"), c.get("intent")
        if slack <= SLACK_FREE:
            ok_slack += 1
            # A pinned `.note` sitting on the footer rule is the intended
            # composition, not crowding. Only unpinned content counts as jammed.
            if slack < 24 and not c.get("pinned_bottom"):
                add("CROWDED", "P2", f"only {slack}px above the footer rule", c["index"])
        elif intent == "breathe" and lic in LEGAL_LICENSES:
            ok_slack += 1
            # A licence is not enough for this much quiet: it has to be a decision
            # somebody looked at. Until the critic signs the card off it is a P2,
            # which reads as "needs a look" without failing the gate by itself.
            if slack > SLACK_REVIEW and c["index"] not in signoff:
                add("SLACK_REVIEW", "P2",
                    f"{slack}px of licensed slack (> {SLACK_REVIEW}px) awaits critic "
                    f"sign-off", c["index"])
            if lic == "few-rows" and c["content_boxes"] > 14:
                add("FALSE_LICENSE", "P1",
                    f"license 'few-rows' on a card with {c['content_boxes']} content boxes", c["index"])
                ok_slack -= 1
        elif measure.get("degraded"):
            ok_slack += 1                      # foreign library: no manifest to read
        else:
            add("UNLICENSED_SLACK", "P1",
                f"{slack}px of bottom slack with no declared license", c["index"])

        # A full-bleed photo card covers the whole artboard by design; calling it
        # overpacked flags the intent. Only TEXT-dominant cards can be walls.
        text_dominant = c.get("media_boxes", 0) == 0
        if cov <= COVERAGE_CEIL or not text_dominant:
            ok_pack += 1
        else:
            add("OVERPACKED", "P2",
                f"text-only card at {cov:.0%} ink coverage (> {COVERAGE_CEIL:.0%})", c["index"])

    cv = lib.get("gap_cv", 0)
    if cv > 0.35:
        add("GAP_VARIANCE", "P2", f"library gap CV {cv} > 0.35")
    density = (7 * ok_cov / n + 6 * ok_gap / n + 4 * ok_slack / n +
               _grade(cv, 0.35, 0.70, 2) + 1 * ok_pack / n)

    # ── DISTINCTION ──────────────────────────────────────────────────────
    u = uniq or {}
    dup_cards = sum(len(v) for v in (u.get("duplicates") or {}).values())
    for t, idxs in (u.get("duplicates") or {}).items():
        add("DUP_LAYOUT", "P1", f"cards {idxs} share mechanic {t}")
    dist_defects = {d["code"] for d in u.get("defects", [])}
    dd = u.get("distribution", {})
    distinction = (
        6 * (1 - min(1.0, dup_cards / n)) +
        _grade(u.get("mean_distance", 0), 2.6, 1.4, 4) +
        _grade(dd.get("partitions_used", 0), 8, 3, 2) +
        (0 if "OVERUSED" in dist_defects else 2) +
        (0 if "MIX_OFF" in dist_defects else 1)
    )
    # Surface grounds are the axis generated libraries most often skip, so the two
    # ground defects cost points rather than only appearing in the list. Fewer than
    # five named grounds takes 5 (a perfect 15 leaves 10: alone enough to fail the
    # Distinction >= 11 gate);
    # each pair of adjacent loud grounds takes 1, capped at 2.
    if "FLAT_SURFACES" in dist_defects:
        distinction -= 5
    clusters = sum(1 for d in u.get("defects", []) if d["code"] == "GROUND_CLUSTER")
    distinction -= min(2, clusters)
    distinction = max(0.0, distinction)
    for d in u.get("defects", []):
        if d["code"] not in ("DUP_LAYOUT",):
            add(d["code"], d.get("severity", "P2"), d.get("detail", ""), d.get("card"))
    if u.get("degraded"):
        distinction = min(distinction, WEIGHTS["distinction"] * 0.6)

    # ── VERACITY ─────────────────────────────────────────────────────────
    veracity = None
    if brief:
        # A claim's `figure` field is the schema's declared home for its number, so
        # it counts as brief text alongside the prose.
        claim_text = " ".join(f"{c.get('text', '')} {c.get('figure', '')}"
                              for c in brief.get("claims", []))
        claim_ids = {c.get("id") for c in brief.get("claims", [])}
        brief_nums = set(NUM_RE.findall(claim_text))
        sourced = invented = 0
        use_count: dict[str, int] = {}
        per = {c["index"]: c for c in lint.get("per_card", [])}
        for c in cards:
            lc = per.get(c["index"], {})
            ids = lc.get("claims") or []
            if ids and set(ids) <= claim_ids:
                sourced += 1
                for cid in set(ids):
                    use_count[cid] = use_count.get(cid, 0) + 1
            else:
                add("UNSOURCED", "P1", "no claim ids attached to this card", c["index"])
            for num in set(NUM_RE.findall(lc.get("text", ""))):
                if len(num) >= 2 and num not in brief_nums:
                    invented += 1
                    add("INVENTED_FIGURE", "P0", f"'{num}' does not appear in the brief", c["index"])
                    break
        reused = sorted(cid for cid, k in use_count.items() if k > 2)
        if reused:
            add("CLAIM_REUSE", "P2",
                f"{len(reused)} claim(s) used on more than 2 cards: {', '.join(reused[:6])}")
        veracity = (5 * sourced / n + 4 * (1 - min(1.0, invented / n)) +
                    (0 if reused else 1))

    # ── CONSTRAINTS ──────────────────────────────────────────────────────
    # Not a scored dimension: a constraint is not worth points, it is worth being
    # true. Violations enter the defect list and the gate, and the checked list is
    # reported so a PASS says something specific about the constraints rather than
    # only about geometry.
    checked = lint.get("constraints_checked") or []
    for d in lint.get("defects", []):
        if d["code"] in ("CROSS_REFERENCE", "SOURCE_LEAK", "MISSING_REQUIRED",
                         "BAD_CONSTRAINT"):
            add(d["code"], d.get("severity", "P1"), d.get("detail", ""), d.get("card"))

    # ── CRAFT ────────────────────────────────────────────────────────────
    craft = None
    craft_by_card: dict[int, float] = {}
    if critic:
        subs = ["hierarchy", "social_native", "thumbnail", "copy", "interest"]
        rows = critic.get("cards", [])
        for r in rows:
            # anchored deductions only: a deduction must cite a visible reason
            vals = []
            for s in subs:
                v = r.get(s)
                if isinstance(v, dict):
                    if v.get("score", 5) < 5 and not v.get("reason"):
                        v = 5                       # unanchored deduction discarded
                    else:
                        v = v.get("score", 3)
                vals.append(max(1, min(5, v if isinstance(v, (int, float)) else 3)))
            card_craft = sum(vals) / len(vals) / 5 * WEIGHTS["craft"]
            # A row without an integer index cannot be attributed to a card; keying
            # it as 0 used to collapse several rows into one and halve the mean.
            idx = r.get("index")
            if isinstance(idx, int):
                craft_by_card[idx] = card_craft
        craft = sum(craft_by_card.values()) / len(craft_by_card) if craft_by_card else None

    dims = {"integrity": round(integrity, 2), "discipline": round(discipline, 2),
            "density": round(density, 2), "distinction": round(distinction, 2),
            "veracity": None if veracity is None else round(veracity, 2),
            "craft": None if craft is None else round(craft, 2)}

    scored = {k: v for k, v in dims.items() if v is not None}
    available = sum(WEIGHTS[k] for k in scored)
    raw = sum(scored.values())
    total = round(raw / available * 100, 1) if available else 0.0

    # ── per-card ─────────────────────────────────────────────────────────
    by_card: dict[int, list[dict]] = {}
    for d in defects:
        if d.get("card"):
            by_card.setdefault(d["card"], []).append(d)

    card_rows = []
    for c in cards:
        s, ds = 100.0, by_card.get(c["index"], [])
        codes = [d["code"] for d in ds]
        s -= 25 * codes.count("OVERFLOW")
        s -= 20 * codes.count("COLLISION")
        s -= 15 * codes.count("INVENTED_FIGURE")
        if "SPARSE" in codes:
            s -= 14 * min(1.0, (COVERAGE_FLOOR - c["coverage"]) / COVERAGE_FLOOR + 0.4)
        if "UNDERWRITTEN" in codes:
            s -= 12 * min(1.0, (c["max_row_gap"] - ceiling) / ceiling + 0.4)
        s -= 10 * codes.count("UNLICENSED_SLACK")
        s -= 8 * codes.count("WEB_CHROME")
        s -= 6 * codes.count("UNSOURCED")
        s -= 5 * codes.count("OVERPACKED")
        s -= 4 * codes.count("CROWDED")
        s -= 3 * codes.count("EMPTY_SLOT")
        s -= 20 * codes.count("SOURCE_LEAK")       # a constraint breach, not a blemish
        s -= 12 * codes.count("CROSS_REFERENCE")
        if craft_by_card:
            s -= (WEIGHTS["craft"] - craft_by_card.get(c["index"], WEIGHTS["craft"])) * 1.2
        card_rows.append({
            "index": c["index"], "layout": c.get("layout"),
            "score": round(max(0.0, min(100.0, s)), 1),
            "coverage": c["coverage"], "max_row_gap": c["max_row_gap"],
            "bottom_slack": c["bottom_slack"],
            "defects": [{"code": d["code"], "severity": d["severity"],
                         "detail": d["detail"], "legal_fix": d["legal_fix"]} for d in ds],
        })

    min_card = min((r["score"] for r in card_rows), default=100.0)
    p0 = [d for d in defects if d["severity"] == "P0"]

    reasons = []
    if total < GATE["total"]:
        reasons.append(f"total {total} < {GATE['total']}")
    if min_card < GATE["min_card"]:
        worst = min(card_rows, key=lambda r: r["score"])
        reasons.append(f"card {worst['index']} at {worst['score']} < {GATE['min_card']}")
    if p0:
        reasons.append(f"{len(p0)} P0 defect(s)")
    if dims["density"] < GATE["density"]:
        reasons.append(f"density {dims['density']} < {GATE['density']}")
    if dims["distinction"] < GATE["distinction"]:
        reasons.append(f"distinction {dims['distinction']} < {GATE['distinction']}")

    # A declared constraint that is violated fails the gate regardless of the total.
    # These are not quality gradients: the user said "no card may depend on another"
    # and either that is true of the library or it is not.
    breaches = [d for d in defects if d["code"] in
                ("CROSS_REFERENCE", "SOURCE_LEAK", "MISSING_REQUIRED")]
    if breaches:
        by = {}
        for d in breaches:
            by[d["code"]] = by.get(d["code"], 0) + 1
        reasons.append("constraint breach: " +
                       ", ".join(f"{k} x{v}" for k, v in sorted(by.items())))

    # Craft's absence used to be a footnote under a total presented as if it were
    # out of 100. Saying it out loud, in the gate reasons, is the same honesty the
    # bench caveats already practise.
    if dims["craft"] is None:
        note = (f"craft unscored — total {total} is the {round(raw, 1)} points earned of "
                f"{available} scoreable, scaled to 100 so the gate stays comparable; "
                f"it is not a 100-point total. "
                f"Run design-critic over shots/ and re-score with --critic")
        if strict:
            reasons.append(note)
        else:
            defects.append({"code": "NO_CRITIC", "severity": "P2", "dim": "craft",
                            "detail": note, "legal_fix": LEGAL_FIX["NO_CRITIC"]})

    if strict:
        # Everything accepted-but-unresolved becomes a failure. This is the switch
        # for actually closing GAP_VARIANCE rather than noting it for a third run.
        p2 = [d for d in defects if d["severity"] == "P2" and d["code"] != "NO_CRITIC"]
        if p2:
            codes = sorted({d["code"] for d in p2})
            reasons.append(f"--strict: {len(p2)} P2 defect(s) ({', '.join(codes[:6])})")

    order = {"P0": 0, "P1": 1, "P2": 2}
    defects.sort(key=lambda d: (order.get(d["severity"], 3),
                                -WEIGHTS.get(d.get("dim", ""), 0), d.get("card") or 0))

    return {
        "scorer_version": plugin_version(),
        "total": total,
        "gate": "PASS" if not reasons else "FAIL",
        "gate_reasons": reasons,
        "dimensions": dims,
        "weights": WEIGHTS,
        "scored_out_of": available,
        "raw_points": round(raw, 2),
        "unscored": [k for k, v in dims.items() if v is None],
        "shared_deterministic": round(
            sum(dims[k] for k in ("integrity", "discipline", "density", "distinction")), 2),
        "min_card": min_card,
        "cards": card_rows,
        "defects": defects,
        "defect_counts": {c: sum(1 for d in defects if d["code"] == c)
                          for c in sorted({d["code"] for d in defects})},
        "library": lib,
        "degraded": bool(measure.get("degraded")),
        "strict": bool(strict),
        "constraints_checked": checked,
        "constraints_clean": not breaches,
    }


def _load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8")) if p and pathlib.Path(p).exists() else None


def main() -> None:
    ap = argparse.ArgumentParser(description="Produce a quality scorecard.")
    ap.add_argument("--lint", default="lint.json")
    ap.add_argument("--measure", default="measure.json")
    ap.add_argument("--uniq", default="uniq.json")
    ap.add_argument("--critic", default=None)
    ap.add_argument("--brief", default=None)
    ap.add_argument("--out", default="scorecard.json")
    ap.add_argument("--strict", action="store_true",
                    help="promote every accepted-but-unresolved P2 into a gate failure")
    a = ap.parse_args()

    # Scoring a missing measure.json as empty used to print a confident score from
    # nothing -- in CI, from the wrong working directory, with exit 0.
    missing = [p for p in (a.lint, a.measure, a.uniq) if not pathlib.Path(p).exists()]
    if missing:
        print(f"not found: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)

    sc = score(_load(a.lint) or {}, _load(a.measure) or {}, _load(a.uniq) or {},
               _load(a.critic), _load(a.brief), strict=a.strict)
    pathlib.Path(a.out).write_text(json.dumps(sc, indent=2), encoding="utf-8")

    print(f"\nSCORE  {sc['total']}/100   gate: {sc['gate']}")
    if sc["gate_reasons"]:
        for r in sc["gate_reasons"]:
            print(f"   x {r}")
    print("")
    for k, w in WEIGHTS.items():
        v = sc["dimensions"][k]
        print(f"  {k:<12} {'--' if v is None else format(v, '5.1f')} / {w}")
    print(f"\n  weakest card  {sc['min_card']}")
    if sc["defect_counts"]:
        print("  defects:")
        for c, k in sorted(sc["defect_counts"].items(), key=lambda kv: -kv[1]):
            print(f"    {c:<20} {k}")
    print(f"\n  -> {a.out}")
    sys.exit(0 if sc["gate"] == "PASS" else 1)


if __name__ == "__main__":
    main()
