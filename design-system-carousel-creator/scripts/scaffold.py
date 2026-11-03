"""
Design System Carousel Creator -- document scaffold + runtime installer.

Emits the exact .dc.html envelope a template library needs, and copies the two
runtime files next to it. Both steps are here rather than in a prompt because
"remember to include support.js" is the kind of instruction that gets followed
forty-nine times out of fifty, and the fiftieth produces a library that renders
as a blank page with no error message.

    python scaffold.py init OUT.dc.html --system design-system.json
    python scaffold.py runtime OUTDIR          # copy/refresh runtime only
    python scaffold.py verify OUT.dc.html      # check envelope + runtime

The envelope is not decorative. Each part earns its place:
  <script src="./support.js">   in <head>, FIRST -- defines DCLogic before use
  <x-dc>                        the component root the runtime mounts onto
  <helmet>                      head-injected: fonts, image-slot.js, :root tokens
  <section>                     the gallery: header + fixed-width artboard grid
  <script data-dc-script>       data-props schema + class Component extends DCLogic
Drop any one and the library silently degrades: no theme editor, no image slots,
or nothing rendered at all.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import pathlib
import re
import shutil
import sys
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME_DIR = HERE.parent / "assets" / "runtime"
CANVAS_SRC = HERE.parent / "assets" / "canvas" / "canvas.html"
CANVAS_FONT = HERE.parent / "assets" / "canvas" / "JetBrainsMono-latin.woff2.base64"
RUNTIME_FILES = ["support.js", "image-slot.js"]
VENDOR_FILES = ["react.production.min.js", "react-dom.production.min.js", "LICENSE-react.txt"]
DEFAULT_FONTS_URL ="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap"
SLOT_STATE = ".image-slots.state.json"

# Minimum plausible size for each runtime file. A truncated copy is worse than a
# missing one: the page half-loads and the failure looks like a design bug.
MIN_BYTES = {"support.js": 40_000, "image-slot.js": 30_000}
EXPECT_HEAD = {
    "support.js": "GENERATED from dc-runtime",
    "image-slot.js": "image-slot",
}


def install_runtime(outdir: pathlib.Path, quiet: bool = False) -> list[str]:
    outdir.mkdir(parents=True, exist_ok=True)
    done = []
    for name in RUNTIME_FILES:
        src = RUNTIME_DIR / name
        if not src.exists():
            sys.exit(f"FATAL: vendored runtime missing: {src}\n"
                     f"The plugin is incomplete -- restore assets/runtime/ before building.")
        dst = outdir / name
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            done.append(f"  = {name} (already current)")
            continue
        shutil.copy2(src, dst)
        done.append(f"  + {name} ({src.stat().st_size // 1024} KB)")

    # React and ReactDOM travel with the bundle. support.js would otherwise fetch
    # them from unpkg.com on every render, and offline (or behind a proxy that
    # blocks it) it hides the template and then fails to boot: a blank page.
    vend = outdir / "vendor"
    vend.mkdir(exist_ok=True)
    for name in VENDOR_FILES:
        src = RUNTIME_DIR / "vendor" / name
        if not src.exists():
            sys.exit(f"FATAL: vendored library missing: {src}\n"
                     f"Restore assets/runtime/vendor/ before building.")
        dst = vend / name
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            continue
        shutil.copy2(src, dst)
        done.append(f"  + vendor/{name} ({src.stat().st_size // 1024} KB)")
    if not quiet:
        print(f"runtime -> {outdir}")
        for line in done:
            print(line)
    return done


def _font_face() -> str:
    """The canvas UI face as a self-contained @font-face rule.

    JetBrains Mono, latin subset, variable weight, base64 into a data: URI. The
    canvas is the one part of this toolchain a designer looks at, so its
    typography must not depend on reaching a font CDN: behind a proxy that blocks
    fonts.gstatic.com the interface silently falls back to whatever monospace the
    OS supplies, the labels reflow, and the tool looks broken at the exact moment
    you are judging whether the work looks good.

    If the vendored file is missing, emit nothing. The stack in --ui-font degrades
    to the platform monospace, which is a worse interface but a working one.
    """
    if not CANVAS_FONT.exists():
        return "/* vendored UI font not found — falling back to platform monospace */"
    b64 = CANVAS_FONT.read_text(encoding="ascii").strip()
    return ("@font-face{\n"
            "  font-family:'JetBrains Mono';\n"
            "  font-style:normal;\n"
            "  font-weight:100 800;\n"
            "  font-display:block;\n"
            f"  src:url(data:font/woff2;charset=utf-8;base64,{b64}) format('woff2');\n"
            "}")


def install_canvas(outdir: pathlib.Path, manifest: dict | None = None,
                   document: str | None = None, quiet: bool = False) -> pathlib.Path | None:
    """Install the canvas host next to the library.

    A .dc.html expects a host application to supply the canvas, the zoom and the
    prop editor. Without one it renders and does nothing, with no console error --
    which reads as "the JavaScript isn't loading" even though nothing is broken.

    The host is part of the BUNDLE, not the EXPORT: it never touches the .dc.html,
    so verify / lint / measure still describe real artboards. It is regenerated on
    every scaffold, so edits belong in assets/canvas/canvas.html.
    """
    if not CANVAS_SRC.exists():
        if not quiet:
            print(f"  ! canvas host missing from the plugin: {CANVAS_SRC}")
        return None
    outdir.mkdir(parents=True, exist_ok=True)

    doc = document
    if doc is None and manifest:
        lib = (manifest.get("artifacts") or {}).get("library") or ""
        doc = pathlib.Path(lib).name or None
    if doc is None:
        hits = sorted(outdir.glob("*.dc.html"))
        doc = hits[0].name if hits else "library.dc.html"

    cv = (manifest or {}).get("canvas") or {}
    theme = ((manifest or {}).get("theme") or {}).get("default", "Black")
    title = (manifest or {}).get("name") or doc.replace(".dc.html", "")

    # Each placeholder is escaped for the context it lands in. A project called
    # `Q3 "Launch" #2` must not close an attribute, end a JS string or become a
    # URL fragment.
    src_url = "./" + urllib.parse.quote(doc)
    doc_js = json.dumps(src_url).replace("</", "<\\/")

    html = CANVAS_SRC.read_text(encoding="utf-8")
    html = (html
            .replace("__FONT_FACE__", _font_face())
            .replace("__DOC_SRC_JS__", doc_js)
            .replace("__DOC_SRC__", _html.escape(src_url, quote=True))
            .replace("__DOC_TITLE__", _html.escape(title, quote=True))
            .replace("__CARD_W__", str(cv.get("width", 1080)))
            .replace("__CARD_H__", str(cv.get("height", 1440)))
            .replace("__DEFAULT_DARK__", "true" if theme == "Black" else "false"))
    dst = outdir / "canvas.html"
    dst.write_text(html, encoding="utf-8")
    if not quiet:
        print(f"  + canvas.html  -> {doc}  (UI font embedded, no external requests)")
    return dst


def seed_slot_state(outdir: pathlib.Path) -> pathlib.Path:
    """Write an empty slot-state sidecar.

    image-slot.js fetches this file and handles the miss correctly, so a 404 here
    is the documented first-load state of something generated-never-authored. It
    is also the very first thing a user sees in the console, where it reads as a
    broken build. An empty object costs two bytes and removes the entire question.
    """
    p = outdir / SLOT_STATE
    if not p.exists():
        p.write_text("{}\n", encoding="utf-8")
    return p


def verify_runtime(outdir: pathlib.Path) -> list[str]:
    problems = []
    for name in RUNTIME_FILES:
        p = outdir / name
        if not p.exists():
            problems.append(f"MISSING: {name} -- the library will not render at all")
            continue
        size = p.stat().st_size
        if size < MIN_BYTES[name]:
            problems.append(f"TRUNCATED: {name} is {size} bytes, expected >= {MIN_BYTES[name]}")
            continue
        head = p.read_text(encoding="utf-8", errors="replace")[:400]
        if EXPECT_HEAD[name] not in head:
            problems.append(f"WRONG FILE: {name} does not look like the expected runtime")
    for name in VENDOR_FILES[:2]:
        p = outdir / "vendor" / name
        if not p.exists() or p.stat().st_size < 5_000:
            problems.append(f"MISSING: vendor/{name} -- React is not bundled, so the library "
                            f"needs unpkg.com at render time and is blank offline")
    return problems


def verify_local_assets(doc: pathlib.Path) -> list[str]:
    """Every ./relative reference in the document must resolve to a real file.

    This is the check that matters most and is easiest to skip. A missing
    ./fonts/Foo.otf does NOT raise an error anywhere -- the browser silently
    falls back to a default face and the entire library renders in the wrong
    typeface. The failure looks like a design problem, not a missing file, so
    it can survive several rounds of review before anyone works out why the
    display type looks wrong.
    """
    html = doc.read_text(encoding="utf-8", errors="replace")
    refs = set(re.findall(r"""["'(]\.(/[^"')\s]+)["')\s]""", html))
    problems = []
    for ref in sorted(refs):
        target = doc.parent / ref.lstrip("/")
        if not target.exists():
            problems.append(f"BROKEN REF: .{ref} -- referenced but not present "
                            f"(fonts fail SILENTLY to a fallback face)")
    return problems


def install_assets(outdir: pathlib.Path, fonts: pathlib.Path | None,
                   logos: pathlib.Path | None) -> None:
    """Copy licensed fonts and brand marks into the bundle.

    Local @font-face and inline logo SVGs are how a library carries a brand
    that Google Fonts cannot supply. They must travel with the document.
    """
    for src, name, exts in ((fonts, "fonts", (".otf", ".ttf", ".woff", ".woff2")),
                            (logos, "logos", (".svg", ".png"))):
        if not src:
            continue
        if not src.exists():
            print(f"  ! {name} source not found: {src}")
            continue
        dst = outdir / name
        dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in sorted(src.iterdir()):
            if f.is_file() and f.suffix.lower() in exts:
                shutil.copy2(f, dst / f.name)
                n += 1
        print(f"  + {name}/ ({n} files)")


ENVELOPE_CHECKS = [
    (r'<script src="\./support\.js"></script>', "support.js not loaded from <head>"),
    (r"window\.__resources\s*=", "React is not mapped to ./vendor/ -- support.js will "
                                 "fetch it from unpkg.com and the library is blank offline"),
    (r"<x-dc>", "missing <x-dc> component root"),
    (r"<helmet>", "missing <helmet> block"),
    (r"data-dc-script", "missing the data-dc-script logic block"),
    (r"data-props=", "missing the data-props schema -- no theme editor"),
    (r"class Component extends DCLogic", "missing the DCLogic subclass"),
    (r"componentDidMount", "applyTheme never called on mount"),
    (r"componentDidUpdate", "theme will not react to prop changes"),
]


def verify_document(path: pathlib.Path) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings).

    The image-slot rules need the error/warning split. A purely typographic
    library with no photography at all is a legitimate and often excellent
    choice -- one of the strongest libraries this format was studied from has
    120 formats and not a single image slot. Hard-failing that would mean the
    verifier rejects reference-quality work, so the real error condition is
    INCONSISTENCY: slots present but the runtime that drives them missing.
    """
    html = path.read_text(encoding="utf-8", errors="replace")
    problems = [msg for pat, msg in ENVELOPE_CHECKS if not re.search(pat, html)]

    # Every custom property used must be declared somewhere.
    declared = set(re.findall(r"(--[A-Za-z0-9_-]+)\s*:", html))
    setprop = set(re.findall(r"setProperty\(\s*['\"](--[A-Za-z0-9_-]+)", html))

    # The idiomatic applyTheme() builds an object literal per theme and loops:
    #     const v = dark ? { paper:'#0F0E0C', 'logo-filter':'invert(1)' } : {...};
    #     for (const k in v) r.setProperty('--' + k, v[k]);
    # so those keys ARE set properties even though '--' never appears next to
    # them. Scan the logic block for every `key: value` pair -- matching only
    # hex values (an earlier version's mistake) misses 'invert(1)', '1', 'none'
    # and reports a correct library as broken. A verifier that cries wolf on
    # known-good input gets ignored, which is worse than not having one.
    for block in re.findall(r"data-dc-script.*?</script>", html, re.S):
        for key in re.findall(r"['\"]?([A-Za-z][A-Za-z0-9-]*)['\"]?\s*:\s*['\"]", block):
            setprop.add("--" + key)

    # Same rule as lint.py: `var(--x, fallback)` resolves without a declaration.
    used = set(re.findall(r"var\(\s*(--[A-Za-z0-9_-]+)\s*\)", html))
    missing = sorted(used - declared - setprop)
    for v in missing[:10]:
        problems.append(f"undeclared custom property: {v}")

    warnings: list[str] = []
    slots = len(re.findall(r"<image-slot\b", html))
    has_runtime = bool(re.search(r'<script src="\./image-slot\.js"></script>', html))
    # Artboards are detected by shape rather than by two hard-coded heights: a 4:5
    # or 1:1 library is legitimate and a verifier that only knows 1440 and 1350
    # silently reports "no image slots in 0 cards" on it.
    cards = (len(re.findall(r"width:\s*\d{3,4}px;\s*height:\s*\d{3,4}px", html))
             or len(re.findall(r'class="[^"]*\bframe\b', html)))

    if slots and not has_runtime:
        problems.append(f"{slots} <image-slot> element(s) but image-slot.js is not "
                        f"loaded in <helmet> -- they will render as nothing")
    elif has_runtime and not slots:
        warnings.append("image-slot.js is loaded but no <image-slot> is used")
    elif cards and not slots:
        warnings.append(f"no image slots in {cards} cards -- deliberate for a purely "
                        f"typographic system, otherwise ~30-40% should carry one")
    return problems, warnings


HEAD_TMPL = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>window.__resources = {{
  "https://unpkg.com/react@18.3.1/umd/react.production.min.js": "./vendor/react.production.min.js",
  "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js": "./vendor/react-dom.production.min.js"
}};</script>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<meta name="design_doc_mode" content="canvas">
{font_tags}<script src="./image-slot.js"></script>
<style>
  :root {{
{tokens}
    letter-spacing: normal;
  }}
  body {{ margin: 0; background: var(--canvas); }}
  image-slot {{ display: block; width: 100%; height: 100%; min-width: 0; }}
</style>
</helmet>

<section style="display:flex;flex-direction:column;gap:72px;padding:96px;font-family:var(--font-body)">
  <header style="display:flex;flex-direction:column;gap:18px;color:var(--gallery-fg)">
    <div style="font-size:15px;letter-spacing:0.22em;text-transform:uppercase;color:var(--gallery-mute)">{eyebrow}</div>
    <div style="font-family:var(--font-display);font-size:76px;line-height:1.08">{title}</div>
    <div style="font-size:17px;line-height:1.7;color:var(--gallery-mute);max-width:820px">{blurb}</div>
  </header>

  <div style="display:grid;grid-template-columns:repeat({cols},{w}px);gap:96px 72px;justify-content:start;align-items:start">

<!-- CARDS GO HERE -->

  </div>
</section>

</x-dc>
<script type="text/x-dc" data-dc-script data-props="{props}">
class Component extends DCLogic {{
  applyTheme() {{
    const dark = (this.props.theme ?? 'White') === 'Black';
    const r = document.documentElement.style;
    const v = dark ? {dark} : {light};
    for (const k in v) r.setProperty('--' + k, v[k]);
    r.setProperty('--label-vis', (this.props.showLabels ?? true) ? 'block' : 'none');
  }}
  componentDidMount() {{ this.applyTheme(); }}
  componentDidUpdate() {{ this.applyTheme(); }}
  renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
"""

DEFAULT_PROPS = {
    "theme": {"editor": "enum", "default": "White", "options": ["White", "Black"],
              "tsType": "string", "section": "Theme"},
    "showLabels": {"editor": "boolean", "default": True, "tsType": "boolean",
                   "section": "Theme"},
}


def cmd_init(a) -> int:
    out = pathlib.Path(a.output)
    system = {}
    if a.system:
        # A mistyped --system used to scaffold silently with placeholder tokens.
        if not pathlib.Path(a.system).exists():
            sys.exit(f"not found: {a.system} (--system takes build/design-system.json)")
        system = json.loads(pathlib.Path(a.system).read_text(encoding="utf-8"))

    themes = system.get("themes", {})
    light = themes.get("light", {}) or {"--paper": "#FFFFFF", "--ink": "#111111"}
    dark = themes.get("dark", {}) or {"--paper": "#111111", "--ink": "#F2F2F2"}

    def jsobj(d):
        # json.dumps, not hand-quoting: a value like "'Fraunces', serif" used to end
        # the string early and leave applyTheme a syntax error and the library blank.
        return json.dumps({k.lstrip("-"): v for k, v in d.items()}, ensure_ascii=False)

    flat = {}
    for group in ("constant", "typography", "type", "figures", "weights", "spacing",
                  "radii", "texture"):
        g = system.get(group)
        if isinstance(g, dict):
            flat.update(g)
    tokens = {**light, **flat}
    tokens.setdefault("--canvas", "#1A1A1A")
    tokens.setdefault("--gallery-fg", "#EDEDED")
    tokens.setdefault("--gallery-mute", "#9C9C9C")
    tokens.setdefault("--font-body", "system-ui, sans-serif")
    tokens.setdefault("--font-display", "Georgia, serif")
    tokens.setdefault("--label-vis", "block")     # applyTheme toggles it; :root declares it

    token_lines = "\n".join(f"    {k}: {v};" for k, v in tokens.items())
    canvas = system.get("canvas", {})
    props = json.dumps(DEFAULT_PROPS).replace('"', "&quot;")

    fonts = (a.fonts or "").strip()
    if fonts.lower() in ("", "none"):
        font_tags = ""
    else:
        font_tags = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">\n'
                     f'<link href="{_html.escape(fonts, quote=True)}" rel="stylesheet">\n')

    def esc(s: str) -> str:
        return _html.escape(str(s), quote=False)

    html = HEAD_TMPL.format(
        font_tags=font_tags, tokens=token_lines,
        eyebrow=esc(a.eyebrow or f"{system.get('brand', 'Library')} · {canvas.get('width', 1080)} × {canvas.get('height', 1440)}"),
        title=esc(a.title or system.get("brand", "Template Library")),
        blurb=esc(a.blurb or "Generated by Design System Carousel Creator."),
        cols=a.cols, w=canvas.get("width", 1080),
        props=props, light=jsobj(light), dark=jsobj(dark),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"scaffold -> {out}")
    install_runtime(out.parent)

    # The bundle is not finished at the runtime. Without a canvas host the document
    # renders and does nothing; without the slot sidecar the console opens on a 404
    # that reads as a broken build. Both are two-line installs.
    man = _manifest_near(out)
    install_canvas(out.parent, man, document=out.name)
    seed_slot_state(out.parent)

    install_assets(out.parent,
                   pathlib.Path(a.fonts_dir) if a.fonts_dir else None,
                   pathlib.Path(a.logos_dir) if a.logos_dir else None)

    if not a.no_builder:
        emit_builder(out, man, cols=a.cols, fonts=a.fonts,
                     theme=((man or {}).get("theme") or {}).get("default", "Black"))

    print("\nInsert cards at the <!-- CARDS GO HERE --> marker, then:")
    print(f"  python {pathlib.Path(__file__).name} verify \"{out}\"")
    return 0


def _manifest_near(path: pathlib.Path) -> dict | None:
    """Find project.json by walking up. Optional: scaffold still works standalone."""
    p = path.resolve().parent
    for cand in [p, *p.parents]:
        f = cand / "project.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                return None
    return None


BUILDER_TMPL = HERE.parent / "assets" / "builder" / "build.py.tmpl"


def emit_builder(document: pathlib.Path, manifest: dict | None,
                 cols: int = 5, theme: str = "Black",
                 fonts: str = DEFAULT_FONTS_URL) -> pathlib.Path | None:
    """Write build/build.py unless one already exists.

    Never overwrites: the emitted file is a starting point that gets filled in with
    the actual card composition, and clobbering that on a re-scaffold would be a
    far worse bug than the one it prevents.
    """
    if not BUILDER_TMPL.exists():
        return None
    if manifest:
        root = document.resolve().parent
        for cand in [root, *root.parents]:
            if (cand / "project.json").exists():
                root = cand
                break
        dst = root / (manifest.get("artifacts", {}).get("builder") or "build/build.py")
        lib_rel = document.resolve().relative_to(root).as_posix()
        name = manifest.get("name") or document.stem
    else:
        # The builder treats its parent's parent as the project root, so outside a
        # project it lives in <doc dir>/build/ to keep the library where it is.
        dst = document.parent / "build" / "build.py"
        lib_rel = document.name
        name = document.stem.replace(".dc", "")

    if dst.exists():
        print(f"  = {dst.name} (kept — a builder already exists)")
        return dst

    def py_str(s: str) -> str:
        """Body of a double-quoted Python literal (no surrounding quotes)."""
        return json.dumps(s, ensure_ascii=False)[1:-1]

    # The name lands in three kinds of place: a docstring / CSS comment (where a
    # triple quote or `*/` would end it early) and string literals (where a `"`
    # would). A project called `Q3 "Launch" #2` used to emit a builder that did not
    # parse.
    doc_name = (name.replace("\\", "/").replace('"""', "'''").replace("*/", "* /")
                    .replace("\n", " "))
    src = BUILDER_TMPL.read_text(encoding="utf-8")
    src = (src.replace("__PROJECT_NAME_STR__", py_str(name))
              .replace("__LIBRARY_REL_STR__", py_str(lib_rel))
              .replace("__FONTS_STR__", py_str(fonts or "none"))
              .replace("__PROJECT_NAME__", doc_name)
              .replace("__PLUGIN_ROOT__", str(HERE.parent))
              .replace("__LIBRARY_REL__", lib_rel)
              .replace("__COLS__", str(cols))
              .replace("__DEFAULT_THEME__", theme))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src, encoding="utf-8")
    print(f"  + {dst.name}  (the library's source — edit here, not in the HTML)")
    return dst


def cmd_runtime(a) -> int:
    install_runtime(pathlib.Path(a.outdir))
    return 0


def cmd_canvas(a) -> int:
    out = pathlib.Path(a.outdir)
    man = _manifest_near(out / "x")
    p = install_canvas(out, man, document=a.document)
    seed_slot_state(out)
    if p:
        print(f"canvas -> {p}")
        print("  serve it:  python serve.py --dir \"%s\"" % out)
    return 0 if p else 1


def cmd_builder(a) -> int:
    doc = pathlib.Path(a.document).resolve()
    man = _manifest_near(doc)
    p = emit_builder(doc, man, cols=a.cols)
    return 0 if p else 1


def cmd_verify(a) -> int:
    path = pathlib.Path(a.document)
    if not path.exists():
        sys.exit(f"not found: {path}")
    errors, warnings = verify_document(path)
    errors += verify_runtime(path.parent) + verify_local_assets(path)

    # The canvas is a warning, not an error: the document is valid without it, but
    # a bundle nobody can open is not finished, and silence here is what let the
    # first run ship one.
    if not (path.parent / "canvas.html").exists():
        warnings.append("no canvas.html beside the library — the document renders but "
                        "nothing pans, zooms or toggles. Run: scaffold.py canvas "
                        f'"{path.parent}"')
    if not (path.parent / SLOT_STATE).exists() and "<image-slot" in \
            path.read_text(encoding="utf-8", errors="replace"):
        warnings.append(f"no {SLOT_STATE} — first load will 404 on a generated sidecar "
                        f"(harmless, but it reads as a broken build)")

    if a.json:
        print(json.dumps({"file": str(path), "ok": not errors,
                          "errors": errors, "warnings": warnings}, indent=2))
        return 1 if errors else 0
    if errors:
        print(f"FAIL  {path.name}")
        for p in errors:
            print(f"  x {p}")
        for w in warnings:
            print(f"  ! {w}")
        return 1
    print(f"OK    {path.name} -- envelope intact, runtime present, local refs resolve")
    for w in warnings:
        print(f"  ! {w}")
    return 0


def cmd_assets(a) -> int:
    out = pathlib.Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    print(f"assets -> {out}")
    install_assets(out,
                   pathlib.Path(a.fonts) if a.fonts else None,
                   pathlib.Path(a.logos) if a.logos else None)
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="write a .dc.html envelope and install the runtime")
    i.add_argument("output")
    i.add_argument("--system", default=None)
    i.add_argument("--title", default=None)
    i.add_argument("--eyebrow", default=None)
    i.add_argument("--blurb", default=None)
    i.add_argument("--cols", type=int, default=5)
    i.add_argument("--fonts", default=DEFAULT_FONTS_URL,
                   help="webfont stylesheet URL for the <link> tag. Pass '' (or 'none') "
                        "to emit no external request and rely on --fonts-dir / system fonts")
    i.add_argument("--fonts-dir", default=None,
                   help="directory of licensed font files to copy into ./fonts/")
    i.add_argument("--logos-dir", default=None,
                   help="directory of brand SVG/PNG marks to copy into ./logos/")
    i.add_argument("--no-builder", action="store_true",
                   help="skip emitting build/build.py (set by the builder itself, "
                        "which re-scaffolds on every run)")
    i.set_defaults(fn=cmd_init)

    r = sub.add_parser("runtime", help="copy/refresh support.js + image-slot.js")
    r.add_argument("outdir")
    r.set_defaults(fn=cmd_runtime)

    c = sub.add_parser("canvas", help="(re)install the canvas host into a bundle")
    c.add_argument("outdir")
    c.add_argument("--document", default=None, help="the .dc.html to host")
    c.set_defaults(fn=cmd_canvas)

    bl = sub.add_parser("builder", help="emit build/build.py for a document")
    bl.add_argument("document")
    bl.add_argument("--cols", type=int, default=5)
    bl.set_defaults(fn=cmd_builder)

    s = sub.add_parser("assets", help="copy licensed fonts / brand logos into a bundle")
    s.add_argument("outdir")
    s.add_argument("--fonts", default=None, help="source directory of font files")
    s.add_argument("--logos", default=None, help="source directory of logo files")
    s.set_defaults(fn=cmd_assets)

    v = sub.add_parser("verify", help="check envelope, runtime, and local asset refs")
    v.add_argument("document")
    v.add_argument("--json", action="store_true", help="machine-readable, for CI")
    v.set_defaults(fn=cmd_verify)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
