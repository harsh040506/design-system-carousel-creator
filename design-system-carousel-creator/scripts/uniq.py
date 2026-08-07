"""
Design System Carousel Creator -- layout distinction.

"Fifty unique layouts" is only enforceable once "unique" is defined. Here it is
tuple equality over six axes, plus a mean-distance floor to catch the subtler
failure: a set where every pair differs on exactly one axis is collision-free
and still monotonous.

Reads a layout-plan.json or a library.manifest.json (same card shape), or falls
back to scraping data-layout / data-mechanic attributes out of an HTML library.

Usage:
    python uniq.py PLAN.json [--out uniq.json]
    python uniq.py LIBRARY.html [--out uniq.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from collections import Counter
from itertools import combinations

AXES = ["partition", "flow", "enumerator", "emphasis", "media", "chrome"]

VOCAB = {
    "partition": ["monolith", "stack", "duo", "triad", "grid", "rail", "chain",
                  "strip", "ledger", "overlay"],
    "flow": ["vertical", "horizontal", "z", "radial", "centred"],
    "enumerator": ["none", "number", "pip", "rule", "chip", "icon", "glyph"],
    "emphasis": ["display", "figure", "media", "quote", "panel", "diagram"],
    "media": ["none", "inset", "sidecar", "full-bleed", "repeated"],
    # Surface grounds, not a light/dark toggle. A named set of five or six is
    # the highest-leverage move for perceived range and the one generated
    # libraries most consistently skip -- see house-standard.md section 2.
    "chrome": ["paper", "panel", "ink", "accent-1", "accent-2", "grey", "flush",
               "standard", "plate", "tinted"],   # last three: legacy aliases
}

CHROME_ALIAS = {"standard": "paper", "plate": "ink", "tinted": "panel"}

TARGETS = {
    "media_cards": (14, 20),
    "figure_cards": (8, 12),
    "min_partitions": 8,
    "max_per_partition": 9,
    "mean_distance": 2.6,
    "min_grounds": 5,
}

# Per-50-card distribution for surface grounds, scaled to the actual card count.
GROUND_MIX = {
    "paper": (20, 26), "panel": (6, 9), "ink": (6, 9),
    "accent-1": (4, 6), "accent-2": (2, 4), "grey": (3, 5),
}


def load_cards(path: pathlib.Path) -> list[dict]:
    if path.suffix.lower() in (".json",):
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("cards", data if isinstance(data, list) else [])
    html = path.read_text(encoding="utf-8", errors="replace")
    cards = []
    for i, m in enumerate(re.finditer(r'<div[^>]*class="[^"]*\bframe\b[^"]*"[^>]*>', html), 1):
        tag = m.group(0)

        def attr(name):
            a = re.search(rf'{name}\s*=\s*"([^"]*)"', tag)
            return a.group(1) if a else None

        mech = attr("data-mechanic")
        card = {"index": i, "layout": attr("data-layout") or f"card-{i:02d}"}
        if mech and ":" in mech:
            parts = mech.split(":")
            for k, v in zip(AXES, parts):
                card[k] = v
        else:
            # degraded: infer only what the class list reveals
            cls = re.search(r'class="([^"]*)"', tag)
            cls = cls.group(1) if cls else ""
            card["chrome"] = ("plate" if "plate" in cls else
                              "flush" if "flush" in cls else
                              "tinted" if ("tinted" in cls or "taupe" in cls) else "standard")
        cards.append(card)
    return cards


def tuple_of(c: dict) -> tuple:
    return tuple(str(c.get(a, "?")) for a in AXES)


def analyse(cards: list[dict]) -> dict:
    n = len(cards)
    defects: list[dict] = []
    complete = [c for c in cards if all(a in c for a in AXES)]
    degraded = len(complete) < n

    tuples = {c["index"]: tuple_of(c) for c in cards}

    # ---- collisions -------------------------------------------------------
    groups: dict[tuple, list[int]] = {}
    for idx, t in tuples.items():
        if "?" in t:
            continue
        groups.setdefault(t, []).append(idx)
    dups = {":".join(t): v for t, v in groups.items() if len(v) > 1}
    for t, idxs in dups.items():
        defects.append({"code": "DUP_LAYOUT", "severity": "P1",
                        "detail": f"cards {idxs} share mechanic {t}"})

    # ---- pairwise distance -------------------------------------------------
    dists = []
    worst = None
    for a, b in combinations(complete, 2):
        ta, tb = tuple_of(a), tuple_of(b)
        d = sum(1 for x, y in zip(ta, tb) if x != y)
        dists.append(d)
        if worst is None or d < worst[0]:
            worst = (d, a["index"], b["index"])
    mean_d = round(sum(dists) / len(dists), 2) if dists else 0.0
    if complete and mean_d < TARGETS["mean_distance"]:
        defects.append({"code": "LOW_VARIETY", "severity": "P1",
                        "detail": f"mean pairwise distance {mean_d} < {TARGETS['mean_distance']}"})

    # ---- distribution ------------------------------------------------------
    def count(axis, value):
        return sum(1 for c in cards if c.get(axis) == value)

    parts = Counter(c.get("partition") for c in cards if c.get("partition"))
    grounds = Counter(CHROME_ALIAS.get(c.get("chrome"), c.get("chrome"))
                      for c in cards if c.get("chrome"))
    dist = {
        "partitions_used": len(parts),
        "partition_counts": dict(parts.most_common()),
        "media_cards": sum(1 for c in cards if c.get("media") not in (None, "none")),
        "grounds_used": len(grounds),
        "ground_counts": dict(grounds.most_common()),
        "fullbleed_cards": count("chrome", "flush") + count("media", "full-bleed"),
        "figure_cards": count("emphasis", "figure"),
        "enumerators_used": len({c.get("enumerator") for c in cards if c.get("enumerator")}),
    }

    if complete:
        if dist["partitions_used"] < TARGETS["min_partitions"]:
            defects.append({"code": "NARROW_RANGE", "severity": "P2",
                            "detail": f"only {dist['partitions_used']} partitions used, want >= {TARGETS['min_partitions']}"})
        for p, k in parts.items():
            if k > TARGETS["max_per_partition"]:
                defects.append({"code": "OVERUSED", "severity": "P2",
                                "detail": f"partition '{p}' on {k} cards (max {TARGETS['max_per_partition']})"})
        for key in ("media_cards", "figure_cards"):
            lo, hi = TARGETS[key]
            if not (lo <= dist[key] <= hi):
                defects.append({"code": "MIX_OFF", "severity": "P2",
                                "detail": f"{key}={dist[key]}, target {lo}-{hi}"})

        # --- surface grounds: the axis generated libraries skip -------------
        if dist["grounds_used"] < TARGETS["min_grounds"]:
            defects.append({"code": "FLAT_SURFACES", "severity": "P1",
                            "detail": f"only {dist['grounds_used']} surface ground(s) used "
                                      f"({', '.join(sorted(grounds))}); want >= {TARGETS['min_grounds']} "
                                      f"named grounds, not a light/dark pair"})
        scale = n / 50.0
        for g, (lo, hi) in GROUND_MIX.items():
            k = grounds.get(g, 0)
            lo_s, hi_s = round(lo * scale), round(hi * scale)
            if k and not (lo_s <= k <= hi_s):
                defects.append({"code": "MIX_OFF", "severity": "P2",
                                "detail": f"ground '{g}' on {k} cards, target {lo_s}-{hi_s}"})

        # --- loud grounds must not cluster ----------------------------------
        loud = {"ink", "accent-1", "accent-2"}
        ordered = sorted((c for c in cards if c.get("chrome")), key=lambda c: c["index"])
        for a, b in zip(ordered, ordered[1:]):
            ga = CHROME_ALIAS.get(a.get("chrome"), a.get("chrome"))
            gb = CHROME_ALIAS.get(b.get("chrome"), b.get("chrome"))
            if ga in loud and ga == gb and b["index"] == a["index"] + 1:
                defects.append({"code": "GROUND_CLUSTER", "severity": "P2",
                                "detail": f"cards {a['index']} and {b['index']} both on '{ga}' "
                                          f"-- loud grounds are punctuation, they should not cluster"})

    # ---- vocabulary sanity -------------------------------------------------
    for c in complete:
        for axis in AXES:
            v = c.get(axis)
            if v and v not in VOCAB[axis]:
                defects.append({"code": "BAD_AXIS", "severity": "P2", "card": c["index"],
                                "detail": f"{axis}='{v}' is not in the vocabulary"})

    names = [c.get("layout") for c in cards if c.get("layout")]
    dup_names = [k for k, v in Counter(names).items() if v > 1]
    for k in dup_names:
        defects.append({"code": "DUP_NAME", "severity": "P2", "detail": f"layout name '{k}' reused"})

    return {
        "cards": n,
        "complete_tuples": len(complete),
        "degraded": degraded,
        "duplicates": dups,
        "mean_distance": mean_d,
        "min_distance": worst[0] if worst else None,
        "closest_pair": list(worst[1:]) if worst else None,
        "distribution": dist,
        "defects": defects,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Check layout distinction across a library.")
    ap.add_argument("plan")
    ap.add_argument("--out", default="uniq.json")
    a = ap.parse_args()

    cards = load_cards(pathlib.Path(a.plan))
    res = analyse(cards)
    res["source"] = a.plan
    pathlib.Path(a.out).write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(f"distinction over {res['cards']} cards ({res['complete_tuples']} with full tuples)")
    if res["degraded"]:
        print("  ! degraded: cards without data-mechanic cannot be collision-checked")
    print(f"  duplicates      {len(res['duplicates'])}")
    print(f"  mean distance   {res['mean_distance']}  min {res['min_distance']}")
    print(f"  partitions used {res['distribution']['partitions_used']}")
    print(f"  grounds used    {res['distribution'].get('grounds_used', 0)}  "
          f"{res['distribution'].get('ground_counts', {})}")
    for d in res["defects"][:12]:
        print(f"  {d['code']:<14} {d['detail']}")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
