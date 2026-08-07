"""
Design System Carousel Creator -- image slots.

    python slots.py list    LIB.dc.html
    python slots.py fill    LIB.dc.html --from photos/ [--by order|id]
    python slots.py clear   LIB.dc.html
    python slots.py state   LIB.dc.html
    python slots.py audit   LIB.dc.html

A library demoed with grey rectangles reads as unfinished no matter how good the
layouts are. Saying so in the build instructions is not the same as giving anyone
a way to fix it -- this is that way.

Remote hotlinking stays refused. A dead URL renders worse than a described slot,
and the document has to render offline -- that is not a limitation to work around,
it is the format. But "the user has a folder of photographs" is the common case,
and copying them into the bundle and writing the src is a hundred lines.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import pathlib
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SLOT_RE = re.compile(r"<image-slot\b([^>]*)>", re.I)
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif")
STATE_FILE = ".image-slots.state.json"


def attrs(tag_body: str) -> dict[str, str]:
    return {k.lower(): v for k, v in ATTR_RE.findall(tag_body)}


FRAME_OPEN_RE = re.compile(r'class\s*=\s*"[^"]*\bframe\b')


def card_index_at(html: str, pos: int) -> str | None:
    """Which artboard a slot sits in.

    data-card is the specified way and the one worth reading. It is also easy to
    omit by accident -- a card can carry data-layout, -mechanic, -intent and
    -claim with no data-card at all, and nothing else notices because the auditor
    finds cards by the .frame class. So: read the attribute, and when it is not
    there, fall back to counting frames. Reporting "card —" for every slot on the
    page is a worse answer than an ordinal.
    """
    head = html[:pos]
    m = None
    for m2 in re.finditer(r'data-card\s*=\s*"([^"]*)"', head):
        m = m2
    if m:
        return m.group(1)
    n = len(FRAME_OPEN_RE.findall(head))
    return f"~{n}" if n else None


def collect(path: pathlib.Path) -> list[dict]:
    html = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in SLOT_RE.finditer(html):
        a = attrs(m.group(1))
        out.append({
            "id": a.get("id") or a.get("slot") or f"slot-{len(out) + 1}",
            "card": card_index_at(html, m.start()),
            "src": a.get("src") or "",
            "placeholder": _html.unescape(a.get("placeholder") or a.get("alt") or ""),
            "pos": m.start(),
        })
    return out


# ───────────────────────────────────────────────────────────────────── list ──
def cmd_list(a) -> int:
    slots = collect(pathlib.Path(a.library))
    if not slots:
        print("no <image-slot> elements — a purely typographic library is a legitimate "
              "choice, and one of the strongest references has 120 formats and no slots")
        return 0
    filled = sum(1 for s in slots if s["src"])
    print(f"{len(slots)} slots · {filled} filled · {len(slots) - filled} empty\n")
    print(f"  {'id':<16}{'card':>5}  {'src':<28}placeholder")
    for s in slots:
        print(f"  {s['id'][:15]:<16}{(s['card'] or '—'):>5}  "
              f"{(s['src'] or '—')[:27]:<28}{s['placeholder'][:40]}")
    return 0


# ───────────────────────────────────────────────────────────────────── fill ──
def cmd_fill(a) -> int:
    lib = pathlib.Path(a.library)
    src_dir = pathlib.Path(a.source)
    if not src_dir.is_dir():
        print(f"not a directory: {src_dir}")
        return 1

    images = sorted(f for f in src_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTS)
    if not images:
        print(f"no images in {src_dir} ({', '.join(IMAGE_EXTS)})")
        return 1

    slots = collect(lib)
    empty = [s for s in slots if not s["src"] or a.overwrite]
    if not empty:
        print("every slot already has a src — pass --overwrite to replace them")
        return 0

    images_dir = lib.parent / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # by id: a file named for the slot wins, which is how you keep a specific
    # photograph on a specific card across rebuilds. Otherwise fall back to order.
    by_stem = {f.stem.lower(): f for f in images}
    pairs: list[tuple[dict, pathlib.Path]] = []
    pool = list(images)
    for s in empty:
        f = by_stem.get(s["id"].lower())
        if f and a.by in ("id", "auto"):
            pairs.append((s, f))
            if f in pool:
                pool.remove(f)
    matched = {id(s) for s, _ in pairs}
    if a.by in ("order", "auto"):
        for s in empty:
            if id(s) in matched or not pool:
                continue
            pairs.append((s, pool.pop(0)))

    html = lib.read_text(encoding="utf-8")
    n = 0
    for s, f in pairs:
        dst = images_dir / f.name
        if not dst.exists() or dst.stat().st_size != f.stat().st_size:
            shutil.copy2(f, dst)
        rel = f"./images/{f.name}"
        # rewrite in place by position, longest-last so offsets stay valid
        tag_m = SLOT_RE.search(html, max(0, s["pos"] - 1))
        if not tag_m:
            continue
        body = tag_m.group(1)
        new_body = re.sub(r'\ssrc\s*=\s*"[^"]*"', "", body)
        new_body = f'{new_body.rstrip()} src="{rel}"'
        html = html[:tag_m.start()] + f"<image-slot{new_body}>" + html[tag_m.end():]
        n += 1
        print(f"  {s['id']:<16} <- {f.name}")

    lib.write_text(html, encoding="utf-8")
    write_state(lib)
    print(f"\nfilled {n} slot(s) · images copied to {images_dir.relative_to(lib.parent)}/")
    left = len(slots) - sum(1 for s in collect(lib) if s["src"])
    if left:
        print(f"  {left} still empty — they will read as unfinished in the export")
    return 0


def cmd_clear(a) -> int:
    lib = pathlib.Path(a.library)
    html = lib.read_text(encoding="utf-8")
    html2 = SLOT_RE.sub(lambda m: "<image-slot" + re.sub(r'\ssrc\s*=\s*"[^"]*"', "", m.group(1)) + ">", html)
    lib.write_text(html2, encoding="utf-8")
    print(f"cleared every src in {lib.name}")
    return 0


# ──────────────────────────────────────────────────────────────────── state ──
def write_state(lib: pathlib.Path) -> pathlib.Path:
    """Generate the sidecar image-slot.js reads.

    It is generated-never-authored, and it 404s on first load until something is
    reframed. Harmless, documented, and still the first thing anyone sees in the
    console — where it reads as a broken build. Writing it removes the question.
    """
    p = lib.parent / STATE_FILE
    prev = {}
    if p.exists():
        try:
            prev = json.loads(p.read_text(encoding="utf-8")) or {}
        except Exception:
            prev = {}
    state = dict(prev)
    for s in collect(lib):
        if s["src"]:
            entry = state.get(s["id"]) or {}
            entry.setdefault("src", s["src"])
            state[s["id"]] = entry
    p.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return p


def cmd_state(a) -> int:
    p = write_state(pathlib.Path(a.library))
    print(f"-> {p}  ({p.stat().st_size} bytes)")
    return 0


# ──────────────────────────────────────────────────────────────────── audit ──
def cmd_audit(a) -> int:
    lib = pathlib.Path(a.library)
    slots = collect(lib)
    empty = [s for s in slots if not s["src"]]
    missing = [s for s in slots if s["src"] and s["src"].startswith(".")
               and not (lib.parent / s["src"].lstrip("./")).exists()]
    remote = [s for s in slots if s["src"].startswith(("http://", "https://"))]
    generic = [s for s in slots
               if s["placeholder"].strip().lower() in ("", "image", "photo", "picture")]

    rows = []
    for s in empty:
        rows.append(("EMPTY_SLOT", "P1", s["card"],
                     f'{s["id"]}: no src — "{s["placeholder"] or "no description"}"'))
    for s in missing:
        rows.append(("BROKEN_SLOT", "P0", s["card"], f'{s["id"]}: {s["src"]} does not exist'))
    for s in remote:
        rows.append(("REMOTE_SLOT", "P1", s["card"],
                     f'{s["id"]}: {s["src"][:48]} — the document must render offline'))
    for s in generic:
        rows.append(("VAGUE_PLACEHOLDER", "P2", s["card"],
                     f'{s["id"]}: placeholder is "{s["placeholder"]}" — describe the subject'))

    if a.json:
        print(json.dumps({"slots": len(slots), "filled": len(slots) - len(empty),
                          "defects": [{"code": c, "severity": sv, "card": cd, "detail": d}
                                      for c, sv, cd, d in rows]}, indent=2))
    else:
        print(f"{len(slots)} slots · {len(slots) - len(empty)} filled")
        for c, sv, cd, d in rows:
            print(f"  {sv}  {c:<18} card {cd or '—':>3}  {d}")
        if not rows:
            print("  clean")
    return 1 if any(sv == "P0" for _, sv, _, _ in rows) else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("list", help="every slot with its id, card and placeholder")
    l.add_argument("library"); l.set_defaults(fn=cmd_list)

    f = sub.add_parser("fill", help="map local images onto slots and copy them in")
    f.add_argument("library")
    f.add_argument("--from", dest="source", required=True)
    f.add_argument("--by", choices=["auto", "id", "order"], default="auto",
                   help="auto: match by filename==slot id first, then fill in order")
    f.add_argument("--overwrite", action="store_true")
    f.set_defaults(fn=cmd_fill)

    c = sub.add_parser("clear", help="remove every src")
    c.add_argument("library"); c.set_defaults(fn=cmd_clear)

    s = sub.add_parser("state", help="write .image-slots.state.json")
    s.add_argument("library"); s.set_defaults(fn=cmd_state)

    a = sub.add_parser("audit", help="report empty, broken, remote and vague slots")
    a.add_argument("library")
    a.add_argument("--json", action="store_true")
    a.set_defaults(fn=cmd_audit)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
