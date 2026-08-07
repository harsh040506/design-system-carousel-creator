"""
Design System Carousel Creator -- project isolation.

    python project.py new "Brand Templates" --system DESIGN.md --source book.pdf
    python project.py list [ROOT]
    python project.py info [PROJECT_DIR]
    python project.py adopt WORKING_DIR --name "Brand Templates"
    python project.py set KEY VALUE            # dotted path into project.json

A run is a project, not a directory. Artifacts written into whatever directory you
happened to be standing in are artifacts a second run silently overwrites, and for a
tool meant to be run many times that failure is both certain and invisible until the
work is already gone.

A project is self-contained, relocatable and reproducible:

    <Project Name>/
      project.json     identity, wiring, constraints, pipeline state
      inputs/          frozen copies of the design system + every source document
      build/           design-system.json, content-brief.json, layout-plan.json, build.py
      dist/            the bundle: .dc.html, runtime, canvas.html, slot state, fonts
      audit/           scorecard/lint/measure/uniq + history.jsonl (append-only)
      shots/           per-card PNGs
      RELEASE.md

`dist/` is the deliverable. Nothing in it reaches outside itself, so it can be zipped,
served or handed over whole.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
MANIFEST = "project.json"
CREATOR_VERSION = "1.0.0"

DEFAULT_LAYOUT = {"inputs": "inputs", "build": "build", "dist": "dist",
                  "audit": "audit", "shots": "shots"}

# Extensions we are willing to freeze into inputs/. Anything else is referenced by
# path in the manifest but not copied -- silently duplicating a 4 GB video would be
# a surprising thing for `new` to do.
SOURCE_EXTS = {".md", ".txt", ".pdf", ".docx", ".doc", ".rtf", ".html", ".htm",
               ".json", ".csv", ".css"}
FREEZE_LIMIT = 64 * 1024 * 1024


# ────────────────────────────────────────────────────────────────── helpers ──
def now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "library"


def find_project(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """Walk up from `start` looking for project.json.

    Every stage calls this. It is why `/design-system-carousel-creator:audit` can take zero arguments: the
    manifest knows where the system, brief, plan and shots are, and wiring five
    paths by hand on every invocation is five chances to audit a library against
    the wrong brief.
    """
    p = (start or pathlib.Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / MANIFEST).exists():
            return cand
    return None


def load(project_dir: pathlib.Path) -> dict:
    return json.loads((project_dir / MANIFEST).read_text(encoding="utf-8"))


def save(project_dir: pathlib.Path, man: dict) -> None:
    man["updated"] = now()
    (project_dir / MANIFEST).write_text(json.dumps(man, indent=2), encoding="utf-8")


def path_of(project_dir: pathlib.Path, man: dict, key: str,
            default: str | None = None) -> pathlib.Path | None:
    """Resolve an artifact key to an absolute path, or None if unset."""
    rel = (man.get("artifacts") or {}).get(key, default)
    return (project_dir / rel) if rel else None


def stamp(project_dir: pathlib.Path, key: str, **extra) -> dict:
    """Mark a pipeline stage complete. Cheap, and it makes `info` truthful."""
    man = load(project_dir)
    man.setdefault("state", {})[key] = now()
    for k, v in extra.items():
        man["state"][k] = v
    save(project_dir, man)
    return man


def default_manifest(name: str, *, brand: str | None = None,
                     width: int = 1080, height: int = 1440,
                     cards: int = 50, columns: int = 5) -> dict:
    slug = slugify(name)
    return {
        "creator_version": CREATOR_VERSION,
        "name": name,
        "slug": slug,
        "created": now(),
        "updated": now(),
        "brand": brand or name,
        "layout": dict(DEFAULT_LAYOUT),
        "canvas": {"width": width, "height": height,
                   "ratio": _ratio(width, height), "rhythm": 64,
                   "cards": cards, "columns": columns},
        "artifacts": {
            "system": "build/design-system.json",
            "brief": "build/content-brief.json",
            "plan": "build/layout-plan.json",
            "builder": "build/build.py",
            "library": f"dist/{name}.dc.html",
            "canvas": "dist/canvas.html",
            "scorecard": "audit/scorecard.json",
            "critic": "audit/critic.json",
            "history": "audit/history.jsonl",
            "release": "RELEASE.md",
        },
        "inputs": {"design_system": None, "sources": []},
        "constraints": {
            "independent_cards": False,
            "no_source_attribution": False,
            "forbidden_terms": [],
            "forbidden_patterns": [],
            "required_terms": [],
        },
        "theme": {"default": "Black", "dark_first": True, "light_is_derived": False},
        "serve": {"port": 4173, "open": True, "watch": False},
        "state": {"distilled": None, "briefed": None, "planned": None,
                  "built": None, "audited": None, "shipped": None,
                  "passes": 0, "best_total": None},
        "notes": [],
    }


def _ratio(w: int, h: int) -> str:
    from math import gcd
    g = gcd(w, h) or 1
    return f"{w // g}:{h // g}"


# ────────────────────────────────────────────────────────────────────── new ──
README_TMPL = """# {name}

Design System Carousel Creator project. Everything this library needs is inside this folder.

```
inputs/    frozen copies of the design system and every source document
build/     design-system.json · content-brief.json · layout-plan.json · build.py
dist/      THE DELIVERABLE — .dc.html, runtime, canvas.html. Self-contained.
audit/     scorecard · lint · measure · uniq · history.jsonl
shots/     per-card PNGs
```

## Look at it

```
python {plugin}/scripts/dscc.py preview
```

Serves `dist/` and opens the canvas: drag to pan, ⌘/Ctrl+scroll to zoom, `D` for
theme, `I` for the card index, `A` for the audit overlay, `F` to focus a card.
The bundle needs a same-origin server — over `file://` the browser gives the iframe
an opaque origin and the theme bridge is blocked.

## Rebuild it

```
python build/build.py
```

The builder always re-scaffolds from scratch. Patching the document in place makes
the style layer sticky: an edit to the CSS silently does not reach the output, which
is a failure that looks exactly like the edit not working.

## Check it

```
python {plugin}/scripts/dscc.py audit          # zero-argument inside a project
```

Reads this project's manifest for the system, brief, plan and shots. Appends a line
to `audit/history.jsonl` every run, which is where the refine trail comes from at
ship time.

---

Created {created}{constraints}
"""


def cmd_new(a) -> int:
    name = a.name.strip()
    root = pathlib.Path(a.into or ".").resolve()
    target = root / (a.dirname or name)

    if target.exists() and any(target.iterdir()) and not a.force:
        print(f"refusing to write into a non-empty directory: {target}")
        print("  --force to proceed, or pick another name")
        return 1

    man = default_manifest(name, brand=a.brand, width=a.width, height=a.height,
                           cards=a.cards, columns=a.cols)

    if a.independent:
        man["constraints"]["independent_cards"] = True
    if a.no_source:
        man["constraints"]["no_source_attribution"] = True
    if a.forbid:
        man["constraints"]["forbidden_terms"] = list(dict.fromkeys(a.forbid))

    for sub in man["layout"].values():
        (target / sub).mkdir(parents=True, exist_ok=True)

    # ---- freeze the inputs -------------------------------------------------
    # Freezing the inputs at `new` time, before anything can drift, is the
    # difference between a habit and a guarantee. A step you have to remember at
    # ship time is a step that eventually does not happen, and six months later
    # nobody knows which brief produced which slides.
    inputs_dir = target / man["layout"]["inputs"]
    frozen: list[str] = []

    def freeze(src_str: str) -> str | None:
        src = pathlib.Path(src_str).expanduser()
        if not src.exists():
            print(f"  ! input not found, recorded by path only: {src}")
            return str(src)
        if src.stat().st_size > FREEZE_LIMIT:
            print(f"  ! {src.name} is {src.stat().st_size // 1_048_576} MB — "
                  f"recorded by path, not copied")
            return str(src.resolve())
        dst = inputs_dir / src.name
        shutil.copy2(src, dst)
        frozen.append(f"{man['layout']['inputs']}/{src.name}")
        return f"{man['layout']['inputs']}/{src.name}"

    if a.system:
        man["inputs"]["design_system"] = freeze(a.system)
    for s in (a.source or []):
        man["inputs"]["sources"].append(freeze(s))

    # Source metadata is where a title leaks back in after being removed from the
    # cards, so seed the forbidden list from the filenames when the constraint is on.
    if man["constraints"]["no_source_attribution"]:
        seeded = set(man["constraints"]["forbidden_terms"])
        for s in (a.source or []):
            stem = pathlib.Path(s).stem
            for part in re.split(r"\s+(?:edited\s+by|by|-|—|·)\s+", stem, flags=re.I):
                part = part.strip(" -_.")
                if len(part) >= 6:
                    seeded.add(part)
        man["constraints"]["forbidden_terms"] = sorted(seeded)

    save(target, man)

    # ---- install the bundle ------------------------------------------------
    import scaffold  # local import: keeps `new` usable when playwright is absent
    dist = target / man["layout"]["dist"]
    scaffold.install_runtime(dist, quiet=True)
    scaffold.install_canvas(dist, man, quiet=True)
    scaffold.seed_slot_state(dist)

    cons = ""
    bits = []
    if man["constraints"]["independent_cards"]:
        bits.append("- **Independent cards** — no card may depend on having read another "
                    "(`CROSS_REFERENCE`, P1)")
    if man["constraints"]["no_source_attribution"]:
        bits.append("- **No source attribution** — no title, author, editor, publisher or "
                    "chapter name anywhere in the artwork (`SOURCE_LEAK`, P0)")
    if bits:
        cons = "\n\n## Constraints on this project\n\n" + "\n".join(bits) + \
               "\n\nBoth are checked on every audit. They are not notes."

    (target / "README.md").write_text(
        README_TMPL.format(name=name, plugin="${CLAUDE_PLUGIN_ROOT}",
                           created=man["created"][:10], constraints=cons),
        encoding="utf-8")

    print(f"project -> {target}")
    for sub in man["layout"].values():
        print(f"  + {sub}/")
    for f in frozen:
        print(f"  + {f}")
    print(f"  + {man['layout']['dist']}/  (support.js · image-slot.js · canvas.html)")
    print(f"  + {MANIFEST}  + README.md")
    if bits:
        print(f"\n  constraints: " + ", ".join(
            k for k, v in man["constraints"].items() if v is True))
    print(f"\nnext:  /design-system-carousel-creator:distill    (writes {man['artifacts']['system']})")
    return 0


# ─────────────────────────────────────────────────────────────────── adopt ──
# Loose artifact names -> where they belong inside a project. Adopting an existing
# flat working directory is how work already done gets carried forward rather than
# rebuilt from scratch.
MIGRATE_MAP = [
    ("design-system.json", "build"), ("content-brief.json", "build"),
    ("layout-plan.json", "build"), ("build_library.py", "build"),
    ("scorecard.json", "audit"), ("lint.json", "audit"),
    ("measure.json", "audit"), ("uniq.json", "audit"), ("critic.json", "audit"),
]


def cmd_adopt(a) -> int:
    src = pathlib.Path(a.directory).resolve()
    if not src.is_dir():
        print(f"not a directory: {src}")
        return 1

    name = a.name or src.name
    target = pathlib.Path(a.into).resolve() if a.into else (src.parent / name)
    man = default_manifest(name)
    if a.independent:
        man["constraints"]["independent_cards"] = True
    if a.no_source:
        man["constraints"]["no_source_attribution"] = True
    if a.forbid:
        man["constraints"]["forbidden_terms"] = list(dict.fromkeys(a.forbid))

    for sub in man["layout"].values():
        (target / sub).mkdir(parents=True, exist_ok=True)

    moved: list[str] = []

    def take(p: pathlib.Path, sub: str, rename: str | None = None) -> str | None:
        if not p.exists():
            return None
        dst = target / man["layout"][sub] / (rename or p.name)
        if p.resolve() == dst.resolve():
            return f"{man['layout'][sub]}/{dst.name}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if p.is_dir():
            shutil.copytree(p, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(p, dst)
        moved.append(f"{man['layout'][sub]}/{dst.name}")
        return f"{man['layout'][sub]}/{dst.name}"

    for fname, sub in MIGRATE_MAP:
        take(src / fname, sub, "build.py" if fname == "build_library.py" else None)

    # audit-out/*.json -> audit/
    for legacy in ("audit-out", "forge_out"):
        d = src / legacy
        if d.is_dir():
            for f in d.glob("*.json"):
                take(f, "audit")

    # shots/
    if (src / "shots").is_dir():
        take(src / "shots", "shots")
        # take() on a dir copies INTO shots/shots; flatten that
        nested = target / man["layout"]["shots"] / "shots"
        if nested.is_dir():
            for f in nested.iterdir():
                shutil.move(str(f), target / man["layout"]["shots"] / f.name)
            nested.rmdir()

    # the bundle: any directory containing a .dc.html, or the cwd itself
    lib_src = None
    for cand in [src, *[d for d in src.iterdir() if d.is_dir()]]:
        hits = sorted(cand.glob("*.dc.html"))
        if hits:
            lib_src = hits[0]
            break
    dist = target / man["layout"]["dist"]
    if lib_src:
        for f in lib_src.parent.iterdir():
            if f.is_file() and f.name != "canvas.html":
                shutil.copy2(f, dist / f.name)
            elif f.is_dir() and f.name in ("fonts", "logos", "images"):
                shutil.copytree(f, dist / f.name, dirs_exist_ok=True)
        man["artifacts"]["library"] = f"{man['layout']['dist']}/{lib_src.name}"
        man["name"] = a.name or lib_src.name.replace(".dc.html", "")
        moved.append(man["artifacts"]["library"])

    # inputs: anything at the top of the source dir that looks like source material
    for f in sorted(src.iterdir()):
        if f.is_file() and f.suffix.lower() in SOURCE_EXTS and \
           f.name not in {n for n, _ in MIGRATE_MAP} and f.stat().st_size <= FREEZE_LIMIT:
            shutil.copy2(f, target / man["layout"]["inputs"] / f.name)
            rel = f"{man['layout']['inputs']}/{f.name}"
            if f.suffix.lower() == ".md" and man["inputs"]["design_system"] is None:
                man["inputs"]["design_system"] = rel
            else:
                man["inputs"]["sources"].append(rel)
            moved.append(rel)

    # adopt real values from the discovered system rather than the defaults
    sysp = target / man["artifacts"]["system"]
    if sysp.exists():
        try:
            sysd = json.loads(sysp.read_text(encoding="utf-8"))
            cv = sysd.get("canvas") or {}
            man["canvas"].update({k: v for k, v in cv.items() if k in man["canvas"]})
            man["canvas"]["ratio"] = cv.get("ratio", man["canvas"]["ratio"])
            man["brand"] = sysd.get("brand", man["brand"])
            man["state"]["distilled"] = now()
        except Exception:
            pass
    planp = target / man["artifacts"]["plan"]
    if planp.exists():
        man["state"]["planned"] = now()
        try:
            man["canvas"]["cards"] = len(
                json.loads(planp.read_text(encoding="utf-8")).get("cards", [])) \
                or man["canvas"]["cards"]
        except Exception:
            pass
    if (target / man["artifacts"]["brief"]).exists():
        man["state"]["briefed"] = now()
    if lib_src:
        man["state"]["built"] = now()
    scp = target / man["artifacts"]["scorecard"]
    carried = None
    if scp.exists():
        man["state"]["audited"] = now()
        try:
            carried = json.loads(scp.read_text(encoding="utf-8"))
            man["state"]["best_total"] = carried.get("total")
        except Exception:
            carried = None

    save(target, man)
    # After save, not before: append_history reads the manifest it is updating.
    if carried:
        append_history(target, carried, note="adopted from a flat working directory")

    # ---- repoint the builder -----------------------------------------------
    builder = target / man["artifacts"]["builder"]
    if builder.exists():
        for line in rewrite_builder_paths(builder, man):
            moved.append(line)

    import scaffold
    scaffold.install_runtime(dist, quiet=True)
    scaffold.install_canvas(dist, man, quiet=True)
    scaffold.seed_slot_state(dist)

    (target / "README.md").write_text(
        README_TMPL.format(name=man["name"], plugin="${CLAUDE_PLUGIN_ROOT}",
                           created=man["created"][:10], constraints=""),
        encoding="utf-8")

    print(f"adopted -> {target}")
    for m in moved[:40]:
        print(f"  + {m}")
    if len(moved) > 40:
        print(f"  … {len(moved) - 40} more")
    print(f"\n  the original at {src} is untouched — verify, then delete it yourself")
    print(f"next:  python {HERE.name}/../scripts/dscc.py audit  (from inside the project)")
    return 0


BUILDER_HEADER = '''# ── repointed by `dscc adopt` ──────────────────────────────────────────────
# This builder was written against a flat layout, where every artifact sat in one
# directory. The anchors below map those names onto the project layout. ROOT is
# kept as an alias so the rest of the file still reads naturally.
PROJECT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN  = pathlib.Path(r"__PLUGIN__")
ROOT    = PROJECT
# ────────────────────────────────────────────────────────────────────────────
'''


def rewrite_builder_paths(builder: pathlib.Path, man: dict) -> list[str]:
    """Repoint a flat-layout builder at the project layout.

    Mechanical and deliberately narrow: it rewrites the anchors a generated builder
    always has (ROOT, the plugin directory, the three build artifacts, the output
    document) and touches nothing else. Anything it could not resolve is printed
    rather than guessed at -- a builder that silently writes to the wrong path is
    worse than one that fails loudly.
    """
    src = builder.read_text(encoding="utf-8")
    orig = src
    changes: list[str] = []
    L = man["layout"]
    lib_name = pathlib.Path(man["artifacts"]["library"]).name

    src = src.replace('ROOT = pathlib.Path(__file__).resolve().parent\n',
                      BUILDER_HEADER.replace("__PLUGIN__", str(PLUGIN_ROOT)), 1)

    # the plugin, wherever it was reached through
    src = re.sub(r'ROOT\s*/\s*"design-system-carousel-creator"\s*/\s*', 'PLUGIN / ', src)
    src = re.sub(r'ROOT\s*/\s*"design-system-carousel-creator"', 'PLUGIN', src)

    # build artifacts
    for name in ("design-system.json", "content-brief.json", "layout-plan.json"):
        src = src.replace(f'ROOT / "{name}"', f'PROJECT / "{L["build"]}" / "{name}"')

    # the output document, whatever folder it used to live in
    src = re.sub(r'ROOT\s*/\s*"[^"]+"\s*/\s*"' + re.escape(lib_name) + r'"',
                 f'PROJECT / "{L["dist"]}" / "{lib_name}"', src)
    src = re.sub(r'ROOT\s*/\s*"' + re.escape(lib_name) + r'"',
                 f'PROJECT / "{L["dist"]}" / "{lib_name}"', src)

    # shots and audit output, if the builder wrote them
    src = src.replace('ROOT / "audit-out"', f'PROJECT / "{L["audit"]}"')
    src = src.replace('ROOT / "shots"', f'PROJECT / "{L["shots"]}"')

    if src != orig:
        builder.write_text(src, encoding="utf-8")
        changes.append(f"{man['artifacts']['builder']}  (paths repointed)")

    leftover = sorted(set(re.findall(r'ROOT\s*/\s*"([^"]+)"', src)))
    if leftover:
        print(f"\n  ! {builder.name} still references, relative to the project root:")
        for x in leftover[:8]:
            print(f"      ROOT / \"{x}\"")
        print("    check these by hand before trusting a rebuild")
    return changes


# ───────────────────────────────────────────────────────────────── history ──
def append_history(project_dir: pathlib.Path, scorecard: dict,
                   note: str = "") -> None:
    """One line per audit, ever. Append-only.

    The refine trail stops being something reconstructed from memory at ship time,
    and `/design-system-carousel-creator:refine` gains the ability to notice that a fix it already tried did
    not move the number.
    """
    man = load(project_dir)
    hp = project_dir / man["artifacts"].get("history", "audit/history.jsonl")
    hp.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "at": now(),
        "total": scorecard.get("total"),
        "gate": scorecard.get("gate"),
        "dimensions": scorecard.get("dimensions"),
        "defects": scorecard.get("defect_counts"),
        "min_card": min((c.get("score", 100) for c in scorecard.get("cards", [])),
                        default=None),
        "unscored": scorecard.get("unscored"),
        "note": note,
    }
    with hp.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")

    best = man.get("state", {}).get("best_total")
    t = scorecard.get("total")
    man.setdefault("state", {})["audited"] = now()
    man["state"]["passes"] = man["state"].get("passes", 0) + 1
    if t is not None and (best is None or t > best):
        man["state"]["best_total"] = t
    save(project_dir, man)


def read_history(project_dir: pathlib.Path) -> list[dict]:
    man = load(project_dir)
    hp = project_dir / man["artifacts"].get("history", "audit/history.jsonl")
    if not hp.exists():
        return []
    rows = []
    for line in hp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


# ──────────────────────────────────────────────────────────────── list/info ──
def cmd_list(a) -> int:
    root = pathlib.Path(a.root or ".").resolve()
    found = sorted(p.parent for p in root.glob(f"*/{MANIFEST}"))
    found += sorted(p.parent for p in root.glob(f"*/*/{MANIFEST}"))
    found = sorted(set(found))
    if (root / MANIFEST).exists():
        found.insert(0, root)
    if not found:
        print(f"no Creator projects under {root}")
        print("  create one:  python project.py new \"Brand Templates\"")
        return 0
    print(f"{'project':<40}{'cards':>6}{'score':>8}  state")
    print("-" * 78)
    for d in found:
        try:
            m = load(d)
        except Exception:
            continue
        st = m.get("state", {})
        stage = "new"
        for k in ("shipped", "audited", "built", "planned", "briefed", "distilled"):
            if st.get(k):
                stage = k
                break
        total = st.get("best_total")
        print(f"{m.get('name', d.name)[:39]:<40}"
              f"{m.get('canvas', {}).get('cards', 0):>6}"
              f"{('      --' if total is None else format(total, '8.1f'))}  {stage}")
    return 0


def cmd_info(a) -> int:
    d = find_project(pathlib.Path(a.directory) if a.directory else None)
    if not d:
        print("not inside a Creator project (no project.json found walking up)")
        return 1
    m = load(d)
    print(f"{m['name']}   [{m['slug']}]   dscc {m.get('creator_version')}")
    print(f"  {d}")
    cv = m.get("canvas", {})
    print(f"\n  canvas       {cv.get('width')}x{cv.get('height')} ({cv.get('ratio')})"
          f"  ·  {cv.get('cards')} cards  ·  {cv.get('columns')} columns")

    cons = {k: v for k, v in (m.get("constraints") or {}).items() if v}
    if cons:
        print("\n  constraints")
        for k, v in cons.items():
            print(f"    {k:<24} {v if not isinstance(v, list) else f'{len(v)} entries'}")

    print("\n  pipeline")
    order = [("distilled", "system"), ("briefed", "brief"), ("planned", "plan"),
             ("built", "library"), ("audited", "scorecard"), ("shipped", "release")]
    for key, art in order:
        ts = (m.get("state") or {}).get(key)
        p = path_of(d, m, art)
        exists = "·" if (p and p.exists()) else " "
        print(f"    {exists} {key:<12} {ts[:19] if ts else '—'}")

    hist = read_history(d)
    if hist:
        print(f"\n  audits ({len(hist)})")
        for h in hist[-6:]:
            dims = h.get("dimensions") or {}
            miss = ",".join(k for k, v in dims.items() if v is None) or "-"
            print(f"    {h['at'][:19]}  {h.get('total', 0):>5}  {h.get('gate', '?'):<4}"
                  f"  min {h.get('min_card') or 0:>5.1f}  unscored:{miss}")

    lib = path_of(d, m, "library")
    if lib and lib.exists():
        print(f"\n  bundle       {lib.parent.name}/  "
              f"({sum(f.stat().st_size for f in lib.parent.rglob('*') if f.is_file()) // 1024} KB)")
        print(f"  preview      dscc.py preview")
    return 0


def cmd_set(a) -> int:
    d = find_project()
    if not d:
        print("not inside a Creator project")
        return 1
    m = load(d)
    node = m
    parts = a.key.split(".")
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    raw = a.value
    if raw.lower() in ("true", "false"):
        val: object = raw.lower() == "true"
    elif re.fullmatch(r"-?\d+", raw):
        val = int(raw)
    elif re.fullmatch(r"-?\d*\.\d+", raw):
        val = float(raw)
    elif raw.startswith("[") or raw.startswith("{"):
        val = json.loads(raw)
    else:
        val = raw
    node[parts[-1]] = val
    save(d, m)
    print(f"{a.key} = {json.dumps(val)}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="create an isolated project")
    n.add_argument("name")
    n.add_argument("--into", default=None, help="parent directory (default: cwd)")
    n.add_argument("--dirname", default=None, help="folder name if different from --name")
    n.add_argument("--brand", default=None)
    n.add_argument("--system", default=None, help="design system file to freeze")
    n.add_argument("--source", action="append", default=[], help="repeatable")
    n.add_argument("--width", type=int, default=1080)
    n.add_argument("--height", type=int, default=1440)
    n.add_argument("--cards", type=int, default=50)
    n.add_argument("--cols", type=int, default=5)
    n.add_argument("--independent", action="store_true",
                   help="no card may depend on another (CROSS_REFERENCE)")
    n.add_argument("--no-source", action="store_true", dest="no_source",
                   help="no source attribution anywhere in the artwork (SOURCE_LEAK)")
    n.add_argument("--forbid", action="append", default=[],
                   help="forbidden literal, repeatable")
    n.add_argument("--force", action="store_true")
    n.set_defaults(fn=cmd_new)

    m = sub.add_parser("adopt", help="pull an existing flat working directory into a project")
    m.add_argument("directory")
    m.add_argument("--name", default=None)
    m.add_argument("--into", default=None)
    m.add_argument("--independent", action="store_true")
    m.add_argument("--no-source", action="store_true", dest="no_source")
    m.add_argument("--forbid", action="append", default=[])
    m.set_defaults(fn=cmd_adopt)

    l = sub.add_parser("list", help="list projects under a root")
    l.add_argument("root", nargs="?", default=".")
    l.set_defaults(fn=cmd_list)

    i = sub.add_parser("info", help="show one project's wiring and history")
    i.add_argument("directory", nargs="?", default=None)
    i.set_defaults(fn=cmd_info)

    s = sub.add_parser("set", help="set a dotted key in project.json")
    s.add_argument("key")
    s.add_argument("value")
    s.set_defaults(fn=cmd_set)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
