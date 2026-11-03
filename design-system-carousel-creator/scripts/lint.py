"""
Design System Carousel Creator -- static source lint.

Checks the things a browser cannot tell you about: tag balance, raw values in
card markup, undeclared custom properties, and web chrome that has no business
in a social post. Runs in milliseconds and needs no browser, so it is the first
gate -- there is no point rendering a library whose markup is unbalanced.

It also enforces the constraints a user states in prose. "Each page must be
individual" or "it must not mention the source" are easy to honour once by hand
and easy to regress on the next edit. A constraint only a careful human enforces
is not a constraint, so both are fields in project.json and codes here.

Usage:
    python lint.py LIBRARY.html [--out lint.json] [--system design-system.json]
                                [--project DIR | --constraints constraints.json]
"""
from __future__ import annotations

import argparse
import html as _html
import json
import pathlib
import re
import sys

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>")
STYLE_ATTR_RE = re.compile(r'style\s*=\s*"([^"]*)"|style\s*=\s*\'([^\']*)\'', re.I)
VAR_DECL_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:")
VAR_USE_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")
# A use with no fallback: `var(--x)`. `var(--x, 50%)` resolves without a declaration.
VAR_BARE_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*\)")
# applyTheme() writes properties with setProperty('--x', ...); those are declared too.
VAR_SET_RE = re.compile(r"setProperty\(\s*['\"](--[A-Za-z0-9_-]+)['\"]")
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
PX_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)px")

# Values that are legitimately raw even inside card markup: hairline widths and
# zero. Everything else must resolve through a token.
PX_ALLOW = {"0", "1", "2"}


def _px_allowed(px: str) -> bool:
    """True for the hairline values (0/1/2px), however they are spelled.

    Compared numerically: stripping trailing "0"/"." characters instead would
    turn 10, 20, 100 and 1000 into 1 and 2 and wave them through.
    """
    try:
        return f"{float(px):g}" in PX_ALLOW
    except ValueError:
        return False

WEB_CHROME_TAGS = ["button", "nav", "form", "input", "select", "textarea",
                   "menu", "dialog", "fieldset"]
WEB_CHROME_TEXT = [
    "sign up", "sign in", "log in", "get started", "start free", "try free",
    "book a demo", "request a demo", "contact sales", "add to cart",
    "subscribe now", "learn more →", "most popular", "per month", "/mo",
    "billed annually", "free trial",
]

# ── independence ────────────────────────────────────────────────────────────
# A card that points at another card is a card missing content. The legal fix is
# to RESTATE the referenced fact here -- which is the density law again, wearing a
# different hat. "Delete the sentence" is not a fix; it leaves the card thinner
# than it was.
#
# These phrases came out of a real run rather than a thesaurus. Anchored to word
# boundaries: "above" inside "above all" is fine, "the chart above" is not, so the
# bare directionals require a preceding noun-ish word.
CROSS_REF_PHRASES = [
    r"\bas we saw\b", r"\bas seen (?:above|earlier|previously)\b",
    r"\bas (?:mentioned|noted|discussed) (?:above|earlier|previously)\b",
    r"\bpreviously\b", r"\bearlier we\b", r"\bcontinued\b", r"\bcontinues on\b",
    r"\bnext (?:slide|card|page)\b", r"\bprevious (?:slide|card|page)\b",
    r"\bsee (?:slide|card|page)\s*\d", r"\brefer back\b",
    # "back to" alone is far too broad: "Where surplus goes / Back to members" is an
    # answer, not a reference, and flagging it is the check crying wolf. A verifier
    # that fires on known-good input gets ignored, which is worse than not having
    # one -- the same reasoning scaffold.py's setProperty scan already carries.
    r"\bback to (?:the )?(?:slide|card|page|start|beginning|top|first)\b",
    r"\bthe (?:chart|figure|table|list|point|claim|number)s? (?:above|below)\b",
    r"\bin the (?:last|first) (?:slide|card)\b", r"\bpart\s+(?:two|three|2|3)\b",
    r"\b(?:continued|cont\.)\s*$", r"\brecall that\b", r"\bthe following (?:slide|card)\b",
    r"\bswipe (?:on|for|to)\b", r"\bkeep (?:reading|swiping)\b",
]
CROSS_REF_RE = re.compile("|".join(CROSS_REF_PHRASES), re.I)

# Attribution shapes that survive a term blacklist. A title can be removed from
# every card and walk straight back in as "edited by …" in a footer.
ATTRIBUTION_PATTERNS = [
    r"\bedited by\b", r"\bwritten by\b", r"\bfrom the book\b", r"\bexcerpt(?:ed)? from\b",
    r"\bsource:\s*\S", r"\bchapter\s+(?:\d+|one|two|three|four|five|six|seven)\b",
    r"\bpublished by\b", r"©\s*\d{4}\b", r"\b\d{4}\s*©", r"\(c\)\s*\d{4}\b", r"\bISBN\b", r"\bpp?\.\s*\d+\b",
    r"\bet al\.", r"\bibid\b", r"\bforeword by\b", r"\bafterword by\b",
]
ATTRIBUTION_RE = re.compile("|".join(ATTRIBUTION_PATTERNS), re.I)

# ── theming ─────────────────────────────────────────────────────────────────
COLOURISH_RE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\b(?:linear|radial|conic)-gradient\(", re.I)
KERNEL_REGION_RE = re.compile(
    r"/\*\s*dscc:kernel-begin.*?dscc:kernel-end\s*\*/", re.S)


def strip_tags(fragment: str) -> str:
    """Readable text from a markup fragment.

    Unescaping is not cosmetic. `&#9671;` (a decorative diamond in a footer)
    survives naive tag-stripping as the literal characters `& # 9 6 7 1 ;`, and the
    veracity check reads `9671` as a figure that does not appear in the brief --
    one decoration produces one INVENTED_FIGURE (P0) per card that carries it,
    which can fail the gate outright. Unescape first, strip second, unescape
    again for entities that were inside attributes.
    """
    text = _html.unescape(fragment)
    text = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", _html.unescape(text)).strip()


def find_cards(html: str, marker_class: str = "frame") -> list[tuple[int, int, str]]:
    """Return (start, end, inner_html) for each artboard, by depth tracking."""
    cards = []
    open_re = re.compile(r'<(\w+)[^>]*class\s*=\s*"[^"]*\b' + re.escape(marker_class) + r'\b[^"]*"[^>]*>')
    for m in open_re.finditer(html):
        if m.group(0).rstrip().endswith("/>"):
            continue
        tag = m.group(1)
        depth, i = 1, m.end()
        walker = re.compile(rf"</?{tag}\b[^>]*>", re.I)
        while depth > 0:
            n = walker.search(html, i)
            if not n:
                break
            if n.group(0).startswith("</"):
                depth -= 1
            elif not n.group(0).rstrip().endswith("/>"):
                depth += 1
            i = n.end()
        cards.append((m.start(), i, html[m.end():i]))
    return cards


def line_of(html: str, pos: int) -> int:
    return html.count("\n", 0, pos) + 1


def check_balance(html: str) -> list[dict]:
    """Report the first structural mismatch per offending tag name."""
    stack, issues = [], []
    body = html
    # ignore anything inside <script>/<style>
    body = re.sub(r"<script\b.*?</script>", lambda m: " " * len(m.group(0)), body,
                  flags=re.S | re.I)
    body = re.sub(r"<style\b.*?</style>", lambda m: " " * len(m.group(0)), body,
                  flags=re.S | re.I)
    body = re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), body, flags=re.S)

    for m in TAG_RE.finditer(body):
        closing, tag, _attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if tag in VOID or selfclose:
            continue
        if not closing:
            stack.append((tag, m.start()))
        else:
            if not stack:
                issues.append({"code": "UNBALANCED", "severity": "P0", "line": line_of(body, m.start()),
                               "detail": f"</{tag}> with nothing open"})
                continue
            if stack[-1][0] == tag:
                stack.pop()
            else:
                # find nearest matching open
                for k in range(len(stack) - 1, -1, -1):
                    if stack[k][0] == tag:
                        unclosed = [t for t, _ in stack[k + 1:]]
                        issues.append({"code": "UNBALANCED", "severity": "P0",
                                       "line": line_of(body, stack[k][1]),
                                       "detail": f"<{tag}> closed while {unclosed} still open"})
                        del stack[k:]
                        break
                else:
                    issues.append({"code": "UNBALANCED", "severity": "P0",
                                   "line": line_of(body, m.start()),
                                   "detail": f"</{tag}> never opened"})
    for tag, pos in stack:
        if tag in ("html", "body", "head"):
            continue
        issues.append({"code": "UNBALANCED", "severity": "P0", "line": line_of(body, pos),
                       "detail": f"<{tag}> never closed"})
    return issues[:20]


def theme_maps(html: str) -> tuple[set[str], int]:
    """Custom properties written by applyTheme(), and how many theme branches exist.

    The idiomatic shape is one object literal per theme:
        const v = dark ? { paper:'#0F0E0C', 'motif-fill':'radial-gradient(…)' } : {…};
        for (const k in v) r.setProperty('--' + k, v[k]);
    so the keys are set properties even though '--' never appears beside them.
    """
    keys: set[str] = set()
    branches = 0
    for block in re.findall(r"data-dc-script.*?</script>", html, re.S):
        for lit in re.findall(r"\{([^{}]*:[^{}]*)\}", block):
            found = re.findall(r"['\"]?([A-Za-z][A-Za-z0-9-]*)['\"]?\s*:\s*['\"]", lit)
            if found:
                branches += 1
                keys.update("--" + k for k in found)
        keys.update(re.findall(r"setProperty\(\s*['\"](--[A-Za-z0-9_-]+)", block))
    return keys, branches


def check_theming(html: str, card_html: str) -> list[dict]:
    """MONO_THEME_TOKEN — a colour that cannot respond to the theme.

    The generalisation of a real defect: the Horizon motif's fill was declared once
    in :root and never entered either theme map, so in dark mode it was a dark disc
    under dark type on a light ground, and flipping to light mirrored the bug. Both
    illegible, and neither visible to any check that existed.

    Static and therefore checkable: a colour-valued property that is used inside
    card markup and appears in NEITHER theme branch is, on a two-theme document,
    wrong in exactly one of them.

    Legal fix: put the token in both theme maps. Illegal fix: darken it until it
    "works in both", which is how you get a library where nothing is quite right
    anywhere.
    """
    themed, branches = theme_maps(html)
    if branches < 2:
        return []                       # single-theme document: nothing to mismatch
    root_blocks = re.findall(r":root[^{]*\{([^}]*)\}", html, re.S)
    used_in_cards = set(VAR_USE_RE.findall(card_html))
    out = []
    for block in root_blocks:
        for decl in re.split(r";", block):
            m = re.match(r"\s*(--[A-Za-z0-9_-]+)\s*:\s*(.+)$", decl, re.S)
            if not m:
                continue
            name, value = m.group(1), m.group(2).strip()
            if name not in used_in_cards or name in themed:
                continue
            if not COLOURISH_RE.search(value):
                continue
            if "var(" in value:
                continue                # an alias: it inherits whatever it points at
            out.append({"code": "MONO_THEME_TOKEN", "severity": "P1", "detail":
                        f"{name} is a colour used in card markup but appears in neither "
                        f"theme map — it cannot respond to the theme"})
    return out[:12]


def check_constraints(cards_text: list[tuple[int, str]], chrome_text: str,
                      constraints: dict) -> list[dict]:
    """Turn the manifest's prose constraints into defects."""
    out: list[dict] = []
    if not constraints:
        return out

    if constraints.get("independent_cards"):
        for idx, text in cards_text:
            for m in CROSS_REF_RE.finditer(text):
                frag = text[max(0, m.start() - 34):m.end() + 34].strip()
                out.append({"code": "CROSS_REFERENCE", "severity": "P1", "card": idx,
                            "detail": f'"…{frag}…" — this card depends on another'})
                break                   # one per card is enough to act on

    terms = [t for t in (constraints.get("forbidden_terms") or []) if t]
    pats = [p for p in (constraints.get("forbidden_patterns") or []) if p]
    if constraints.get("no_source_attribution"):
        pats = pats + ATTRIBUTION_PATTERNS

    if terms or pats:
        compiled = []
        for t in terms:
            compiled.append((t, re.compile(re.escape(t), re.I)))
        for p in pats:
            try:
                compiled.append((p, re.compile(p, re.I)))
            except re.error:
                out.append({"code": "BAD_CONSTRAINT", "severity": "P2",
                            "detail": f"forbidden_patterns entry is not a valid regex: {p}"})
        # The chrome is where a title walks back in after being removed from every
        # card: gallery header, eyebrow, <title>, format labels, alt text.
        for label, idx, text in ([("chrome", None, chrome_text)] +
                                 [("card", i, t) for i, t in cards_text]):
            for src, rx in compiled:
                m = rx.search(text)
                if m:
                    frag = text[max(0, m.start() - 24):m.end() + 24].strip()
                    out.append({"code": "SOURCE_LEAK", "severity": "P0", "card": idx,
                                "detail": f'{label}: "{src}" → "…{frag}…"'})
    required = [t for t in (constraints.get("required_terms") or []) if t]
    if required:
        whole = chrome_text + " " + " ".join(t for _, t in cards_text)
        for t in required:
            if t.lower() not in whole.lower():
                out.append({"code": "MISSING_REQUIRED", "severity": "P1",
                            "detail": f'required term "{t}" appears nowhere in the library'})
    return out


def lint(path: pathlib.Path, system: dict | None = None,
         constraints: dict | None = None) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    defects: list[dict] = []

    defects += check_balance(html)

    # ---- custom properties -------------------------------------------------
    declared = set(VAR_DECL_RE.findall(html)) | set(VAR_SET_RE.findall(html))
    used = set(VAR_USE_RE.findall(html))
    for v in sorted(set(VAR_BARE_RE.findall(html)) - declared):
        defects.append({"code": "UNDECLARED_VAR", "severity": "P0", "detail": v})
    unused = sorted(declared - used)

    # ---- per-card checks ---------------------------------------------------
    cards = find_cards(html)
    if not cards:
        cards = find_cards(html, "card")
    per_card = []
    for i, (start, _end, inner) in enumerate(cards, 1):
        cd: list[dict] = []
        for m in STYLE_ATTR_RE.finditer(inner):
            decl = m.group(1) or m.group(2) or ""
            for px in PX_RE.findall(decl):
                if not _px_allowed(px):
                    cd.append({"code": "RAW_PX", "severity": "P1", "card": i,
                               "detail": f"{px}px in inline style"})
            if re.search(r"font-size", decl, re.I):
                cd.append({"code": "INLINE_TYPE", "severity": "P1", "card": i,
                           "detail": decl.strip()[:70]})
            for hx in HEX_RE.findall(decl):
                cd.append({"code": "RAW_HEX", "severity": "P1", "card": i, "detail": hx})
        for t in WEB_CHROME_TAGS:
            for m in re.finditer(rf"<{t}\b", inner, re.I):
                cd.append({"code": "WEB_CHROME", "severity": "P1", "card": i,
                           "detail": f"<{t}> element in a social artboard"})
        text = strip_tags(inner).lower()
        for phrase in WEB_CHROME_TEXT:
            if phrase in text:
                cd.append({"code": "WEB_CHROME_COPY", "severity": "P2", "card": i,
                           "detail": f'call-to-action / pricing copy: "{phrase}"'})
        # de-duplicate identical findings within a card
        seen, dedup = set(), []
        for d in cd:
            k = (d["code"], d["detail"])
            if k in seen:
                continue
            seen.add(k)
            dedup.append(d)
        defects += dedup
        # Card text and claim ids feed the veracity dimension: every number on a
        # slide has to be findable in the brief, and that is a lookup, not a memory.
        card_text = strip_tags(inner)
        claims = re.findall(r'data-claim\s*=\s*"([^"]*)"', html[start:_end])
        claim_ids = [c for spec in claims for c in re.split(r"[,\s]+", spec) if c]
        per_card.append({"index": i, "line": line_of(html, start),
                         "bytes": len(inner), "defects": len(dedup),
                         "text": card_text[:4000], "claims": claim_ids})

    # ---- scale conformance against the design system -----------------------
    if system:
        legal_px = set()
        for group in ("spacing", "radii", "type", "figures"):
            for v in (system.get(group) or {}).values():
                m = re.match(r"(\d+)px", str(v))
                if m:
                    legal_px.add(m.group(1))
        style_blocks = re.findall(r"<style\b[^>]*>(.*?)</style>", html, re.S | re.I)
        css = "\n".join(style_blocks)
        # The kernel is copy-verbatim by instruction. Flagging its own primitives as
        # off-scale would be the tool contradicting its own instruction and produce
        # defects nobody is permitted to fix. Skip anything between the kernel's
        # sentinels.
        css = KERNEL_REGION_RE.sub(" ", css)
        # only inspect declarations that are not inside :root
        css_body = re.sub(r":root[^{]*\{[^}]*\}", "", css, flags=re.S)
        off = sorted({p for p in PX_RE.findall(css_body)
                      if p not in legal_px and not _px_allowed(p)})
        for p in off[:25]:
            defects.append({"code": "OFF_SCALE", "severity": "P2",
                            "detail": f"{p}px is not on any declared scale"})

    # ---- theming -----------------------------------------------------------
    card_html = "\n".join(inner for _, _, inner in cards)
    defects += check_theming(html, card_html)

    # ---- declared constraints ----------------------------------------------
    # The gallery chrome is checked separately from the cards because that is
    # where a removed title reappears: header, eyebrow, <title>, format labels.
    chrome = html
    for _s, _e, inner in cards:
        chrome = chrome.replace(inner, " ")
    chrome = re.sub(r"<script\b.*?</script>", " ", chrome, flags=re.S | re.I)
    chrome = re.sub(r"<style\b.*?</style>", " ", chrome, flags=re.S | re.I)
    chrome_text = strip_tags(chrome)
    cards_text = [(c["index"], c["text"]) for c in per_card]
    constraint_defects = check_constraints(cards_text, chrome_text, constraints or {})
    defects += constraint_defects

    counts: dict[str, int] = {}
    for d in defects:
        counts[d["code"]] = counts.get(d["code"], 0) + 1

    return {
        "source": str(path),
        "cards_found": len(cards),
        "declared_vars": len(declared),
        "unused_vars": unused,
        "defects": defects,
        "counts": counts,
        "per_card": per_card,
        "has_system": bool(system),
        "constraints_checked": sorted(k for k, v in (constraints or {}).items() if v),
        "constraints_clean": not constraint_defects,
    }


def load_constraints(near: pathlib.Path,
                     explicit: pathlib.Path | None = None) -> dict:
    """Find the constraints to enforce, without requiring anyone to pass them.

    Walking up for project.json is what lets `/design-system-carousel-creator:audit` take zero arguments.
    Wiring five paths by hand on every invocation is five chances to audit a
    library against the wrong brief.
    """
    if explicit and explicit.exists():
        d = json.loads(explicit.read_text(encoding="utf-8"))
        return d.get("constraints", d)
    p = near.resolve()
    for cand in [p, *p.parents]:
        f = cand / "project.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8")).get("constraints") or {}
            except Exception:
                return {}
    return {}


def main() -> None:
    ap = argparse.ArgumentParser(description="Static lint for a carousel library.")
    ap.add_argument("library")
    ap.add_argument("--out", default="lint.json")
    ap.add_argument("--system", default=None)
    ap.add_argument("--project", default=None,
                    help="project directory — reads constraints from project.json")
    ap.add_argument("--constraints", default=None,
                    help="JSON file holding a constraints object directly")
    a = ap.parse_args()

    system = None
    if a.system and pathlib.Path(a.system).exists():
        system = json.loads(pathlib.Path(a.system).read_text(encoding="utf-8"))

    constraints = load_constraints(
        pathlib.Path(a.project) if a.project else pathlib.Path(a.library).parent,
        pathlib.Path(a.constraints) if a.constraints else None)

    res = lint(pathlib.Path(a.library), system, constraints)
    pathlib.Path(a.out).write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(f"linted {res['cards_found']} cards from {a.library}")
    if res["counts"]:
        for code, n in sorted(res["counts"].items(), key=lambda kv: -kv[1]):
            print(f"  {code:<18} {n}")
    else:
        print("  clean")
    print(f"  -> {a.out}")
    sys.exit(1 if any(d["severity"] == "P0" for d in res["defects"]) else 0)


if __name__ == "__main__":
    main()
