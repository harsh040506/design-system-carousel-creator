"""
Design System Carousel Creator -- command line.

    python dscc.py new "Brand Templates"       create an isolated project
    python dscc.py list                        every project under a root
    python dscc.py info                        this project's wiring and history
    python dscc.py doctor                      check the toolchain / a design system
    python dscc.py build                       run the project's builder
    python dscc.py audit [LIB.html]            lint + measure + uniq + score
    python dscc.py preview                     serve the bundle, open the canvas
    python dscc.py report                      one HTML report for the whole project
    python dscc.py bench CAND.html REF.html..  compare against reference libraries
    python dscc.py shots LIB.html DIR          render per-card PNGs for the critic
    python dscc.py adopt DIR                   pull an existing flat working directory into a project

Inside a project most of these take no arguments: the manifest knows where the
system, brief, plan and shots live. Wiring five paths by hand on every invocation
is five chances to audit a library against the wrong brief.

Nothing here depends on Claude. Run it in CI, run it on a library you built by
hand, run it on somebody else's. That independence is the point: a quality claim
that only the thing making the claim can verify is not a quality claim.
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows cp1252 guard

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lint as lint_mod          # noqa: E402
import uniq as uniq_mod          # noqa: E402
import score as score_mod        # noqa: E402
import project as proj           # noqa: E402

REQUIRED_TOKENS = [
    "--surface", "--surface-2", "--surface-3", "--ink", "--muted", "--faint",
    "--on-ink", "--rule", "--accent",
    "--plate-bg", "--plate-fg", "--plate-mute", "--plate-rule", "--plate-well",
    "--font-display", "--font-body", "--font-mono",
    "--t-display", "--t-heading", "--t-heading-sm", "--t-body-xl", "--t-body-lg",
    "--t-body-sm", "--t-caption", "--t-mono", "--t-kicker",
    "--f-hero", "--f-lg", "--f-md", "--f-sm", "--f-xs",
    "--w-display", "--w-body", "--w-med", "--w-bold", "--grain",
]

TYPE_FLOORS = {"--t-display": 120, "--t-heading": 52, "--t-body-xl": 34,
               "--t-body-sm": 23, "--t-caption": 19}


# ─────────────────────────────────────────────────────────────── doctor ──
def cmd_doctor(args) -> int:
    ok = True
    print("toolchain")
    print(f"  python            {sys.version.split()[0]}")
    try:
        import playwright  # noqa: F401
        print("  playwright        installed")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                b = pw.chromium.launch()
                b.close()
            print("  chromium          launchable")
        except Exception as e:
            ok = False
            print(f"  chromium          FAILED - run: playwright install chromium ({e})")
    except ImportError:
        ok = False
        print("  playwright        MISSING - pip install playwright && playwright install chromium")

    kernel = HERE.parent / "skills" / "carousel-craft" / "assets" / "kernel.css"
    print(f"  kernel.css        {'found' if kernel.exists() else 'MISSING'}")
    ok &= kernel.exists()

    if args.system:
        p = pathlib.Path(args.system)
        if not p.exists():
            print(f"\ndesign system     MISSING at {p}")
            return 1
        # Pointing doctor at the raw brand document is the obvious thing to try and
        # used to produce a JSONDecodeError traceback. --system wants the DISTILLED
        # artifact; say which stage produces it rather than the parser's opinion.
        try:
            sysd = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"\ndesign system     {p.name} is not JSON")
            print("  --system takes the DISTILLED artifact (build/design-system.json),")
            print(f"  not the brand document. Run /design-system-carousel-creator:distill on {p.name} first.")
            return 1
        if not isinstance(sysd, dict):
            print(f"\ndesign system     {p.name} is JSON but not an object")
            return 1
        flat: dict[str, str] = {}
        for theme in ("light", "dark"):
            flat.update({k: v for k, v in (sysd.get("themes", {}).get(theme) or {}).items()})
        # `typography` is what the JSON Schema and scaffold.py read; doctor used to
        # flatten only `typography_tokens`, so a system declaring the font family
        # tokens correctly was reported as missing all three. The workaround was to
        # emit both groups with identical values, which then ships in the artifact
        # forever. Accept either name, and say so when both disagree.
        for group in ("constant", "typography", "typography_tokens", "type",
                      "figures", "weights", "texture", "spacing", "radii"):
            g = sysd.get(group)
            if isinstance(g, dict):
                flat.update({k: str(v) for k, v in g.items()})

        print(f"\ndesign system     {p.name}")
        a_, b_ = sysd.get("typography"), sysd.get("typography_tokens")
        if isinstance(a_, dict) and isinstance(b_, dict):
            clash = sorted(k for k in set(a_) & set(b_) if str(a_[k]) != str(b_[k]))
            if clash:
                ok = False
                print(f"  AMBIGUOUS TYPE    typography and typography_tokens disagree on "
                      f"{', '.join(clash[:4])} — scaffold reads `typography`")
            else:
                print("  typography        both groups present and identical "
                      "(one is now enough — `typography` is canonical)")
        missing = [t for t in REQUIRED_TOKENS if t not in flat]
        if missing:
            ok = False
            print(f"  missing tokens    {len(missing)}")
            for m in missing[:14]:
                print(f"    {m}")
        else:
            print("  tokens            complete")

        for tok, floor in TYPE_FLOORS.items():
            v = flat.get(tok, "")
            try:
                px = float(str(v).replace("px", ""))
            except ValueError:
                continue
            if px < floor:
                ok = False
                print(f"  TYPE TOO SMALL    {tok}={v} < {floor}px floor for a 1080 artboard")

        for theme in ("light", "dark"):
            t = sysd.get("themes", {}).get(theme) or {}
            seen: dict[str, str] = {}
            for role in ("--ink", "--muted", "--faint", "--surface", "--surface-2"):
                v = str(t.get(role, "")).lower()
                if v and v in seen:
                    ok = False
                    print(f"  COLLAPSED ROLE    {theme}: {role} == {seen[v]} ({v})")
                elif v:
                    seen[v] = role

        cov = sysd.get("coverage")
        if cov is not None:
            print(f"  source coverage   {cov}  (rest derived)")

    print("\n" + ("READY" if ok else "NOT READY"))
    return 0 if ok else 1


# ──────────────────────────────────────────────────────────────── audit ──
def run_audit(library: pathlib.Path, outdir: pathlib.Path, selector: str | None,
              rhythm: int, system=None, critic=None, brief=None,
              plan: pathlib.Path | None = None, shots: pathlib.Path | None = None,
              constraints: dict | None = None, strict: bool = False) -> dict:
    import measure as measure_mod

    if not library.exists():
        raise FileNotFoundError(
            f"library not found: {library}\n"
            f"  cwd: {pathlib.Path.cwd()}\n"
            f"  (paths with '&' or spaces need quoting in most shells)")
    outdir.mkdir(parents=True, exist_ok=True)
    lr = lint_mod.lint(library, system, constraints)
    (outdir / "lint.json").write_text(json.dumps(lr, indent=2), encoding="utf-8")

    mr = measure_mod.measure(library, selector, shots, rhythm)
    (outdir / "measure.json").write_text(json.dumps(mr, indent=2), encoding="utf-8")

    ur = uniq_mod.analyse(uniq_mod.load_cards(plan or library))
    (outdir / "uniq.json").write_text(json.dumps(ur, indent=2), encoding="utf-8")

    sc = score_mod.score(lr, mr, ur, critic, brief, strict=strict)
    sc["library_file"] = str(library)
    (outdir / "scorecard.json").write_text(json.dumps(sc, indent=2), encoding="utf-8")
    return sc


def wire_from_project(args) -> tuple[pathlib.Path | None, dict]:
    """Fill unset audit arguments from the project manifest.

    Explicit flags always win, so `dscc audit some-other.html` still does exactly
    what it says. But inside a project the zero-argument form is the one that
    cannot be wired to the wrong brief.
    """
    pd = proj.find_project(pathlib.Path(getattr(args, "project", None) or "."))
    if not pd:
        return None, {}
    man = proj.load(pd)
    A = man.get("artifacts", {})

    def fill(attr, key, must_exist=True):
        if getattr(args, attr, None):
            return
        rel = A.get(key)
        if not rel:
            return
        p = pd / rel
        if p.exists() or not must_exist:
            setattr(args, attr, str(p))

    if not getattr(args, "library", None):
        lib = A.get("library")
        if lib and (pd / lib).exists():
            args.library = str(pd / lib)
        else:
            hits = sorted((pd / man["layout"]["dist"]).glob("*.dc.html"))
            if hits:
                args.library = str(hits[0])
    fill("system", "system")
    fill("brief", "brief")
    fill("plan", "plan")
    fill("critic", "critic")
    if not getattr(args, "out", None) or args.out == "audit-out":
        args.out = str(pd / man["layout"]["audit"])
    if not getattr(args, "shots", None):
        args.shots = str(pd / man["layout"]["shots"])
    if getattr(args, "rhythm", None) in (None, 64):
        args.rhythm = (man.get("canvas") or {}).get("rhythm", 64)
    return pd, man


def _print_card_table(sc: dict, limit: int) -> None:
    rows = sorted(sc["cards"], key=lambda r: r["score"])[:limit]
    if not rows:
        return
    print(f"\n  weakest {len(rows)} cards")
    print(f"    {'#':>3}  {'score':>5}  {'cov':>5}  {'gap':>5}  {'slack':>5}  defects")
    for r in rows:
        codes = ",".join(sorted({d['code'] for d in r["defects"]})) or "-"
        print(f"    {r['index']:>3}  {r['score']:>5.1f}  {r['coverage']:>4.0%}  "
              f"{r['max_row_gap']:>5}  {r['bottom_slack']:>5}  {codes[:56]}")


def cmd_audit(args) -> int:
    pd, man = wire_from_project(args)
    if not args.library:
        print("no library to audit — pass one, or run inside a project that has built one")
        return 2
    lib = pathlib.Path(args.library)
    out = pathlib.Path(args.out)
    load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8")) if p and pathlib.Path(p).exists() else None
    selector = None if getattr(args, "auto", False) else args.selector
    constraints = (man.get("constraints") or {}) if man else \
        lint_mod.load_constraints(lib.parent)
    if pd:
        print(f"project  {man.get('name')}  ({pd})")
        wired = [f"{k}={pathlib.Path(v).name}" for k, v in
                 (("system", args.system), ("brief", args.brief),
                  ("plan", args.plan), ("critic", args.critic)) if v]
        print(f"  wired  {', '.join(wired) or '— nothing found'}")
    try:
        sc = run_audit(lib, out, selector, args.rhythm,
                       system=load(args.system), critic=load(args.critic), brief=load(args.brief),
                       plan=pathlib.Path(args.plan) if args.plan else None,
                       shots=pathlib.Path(args.shots) if args.shots else None,
                       constraints=constraints, strict=getattr(args, "strict", False))
    except FileNotFoundError as e:
        print(f"\n{e}")
        return 2

    if pd:
        proj.append_history(pd, sc, note=getattr(args, "note", "") or "")

    print(f"\nSCORE  {sc['total']}/100   gate: {sc['gate']}")
    for r in sc["gate_reasons"]:
        print(f"   x {r}")
    print("")
    for k, w in score_mod.WEIGHTS.items():
        v = sc["dimensions"][k]
        bar = "" if v is None else "#" * int(round(v / w * 24))
        print(f"  {k:<12} {'  --' if v is None else format(v, '5.1f')} /{w:>3}  {bar}")
    if sc["unscored"]:
        print(f"\n  unscored: {', '.join(sc['unscored'])} "
              f"(scored out of {sc['scored_out_of']})")
    if sc["degraded"]:
        print("  ! degraded mode: no manifest, artboard auto-detected, "
              "slack licensing unreadable")

    if sc.get("constraints_checked"):
        mark = "clean" if sc.get("constraints_clean") else "BREACHED"
        print(f"\n  constraints  {', '.join(sc['constraints_checked'])}  ->  {mark}")

    if pd:
        hist = proj.read_history(pd)
        if len(hist) > 1:
            trail = " → ".join(str(h.get("total")) for h in hist[-6:])
            print(f"\n  trail        {trail}   (pass {len(hist)})")

    if sc["defect_counts"]:
        print("\n  defects")
        for c, k in sorted(sc["defect_counts"].items(), key=lambda kv: -kv[1]):
            fix = score_mod.LEGAL_FIX.get(c, "")
            print(f"    {c:<18} {k:>3}   {fix[:60]}")
    _print_card_table(sc, args.top)
    print(f"\n  artifacts -> {out}/")
    return 0 if sc["gate"] == "PASS" else 1


# ──────────────────────────────────────────────────────────────── bench ──
def cmd_bench(args) -> int:
    """Same auditor, candidate and references, one table. Caveats printed."""
    targets = [("candidate", pathlib.Path(args.candidate))]
    for r in args.references:
        p = pathlib.Path(r)
        targets.append((p.stem[:22], p))

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, path in targets:
        if not path.exists():
            print(f"  ! {path} not found, skipping")
            continue
        print(f"auditing {name} ...")
        selector = args.selector if name == "candidate" else None
        try:
            sc = run_audit(path, out / name.replace(" ", "-"), selector, args.rhythm)
        except Exception as e:
            print(f"  ! {name} failed to audit: {type(e).__name__}: {str(e)[:120]}")
            continue
        d = sc["dimensions"]
        rows.append({
            "name": name, "path": str(path),
            "integrity": d["integrity"], "discipline": d["discipline"],
            "density": d["density"], "distinction": d["distinction"],
            "veracity": d["veracity"], "shared": sc["shared_deterministic"],
            "cards": sc["library"].get("cards", 0),
            "coverage": sc["library"].get("coverage_mean", 0),
            "gap_cv": sc["library"].get("gap_cv", 0),
            "fonts": sc["library"].get("distinct_font_sizes", 0),
            "degraded": sc["degraded"],
        })

    print("\n" + "=" * 78)
    print("BENCHMARK -- identical deterministic auditor, all libraries")
    print("=" * 78)
    hdr = f"{'library':<24}{'n':>4}{'Integ':>7}{'Disc':>6}{'Dens':>6}{'Dist':>6}{'Verac':>7}{'Shared/70':>11}"
    print(hdr)
    print("-" * 78)
    for r in sorted(rows, key=lambda x: -x["shared"]):
        ver = "  --" if r["veracity"] is None else f"{r['veracity']:5.1f}"
        print(f"{r['name']:<24}{r['cards']:>4}{r['integrity']:>7.1f}{r['discipline']:>6.1f}"
              f"{r['density']:>6.1f}{r['distinction']:>6.1f}{ver:>7}{r['shared']:>11.1f}")
    print("-" * 78)
    print(f"{'library':<24}{'':>4}{'coverage':>10}{'gap CV':>10}{'font sizes':>13}")
    for r in sorted(rows, key=lambda x: -x["shared"]):
        print(f"{r['name']:<24}{'':>4}{r['coverage']:>9.1%}{r['gap_cv']:>10.2f}{r['fonts']:>13}")

    print("\ncaveats, stated because a benchmark that hides them is worthless:")
    print("  1. Veracity is unscoreable without a content brief, so references show '--'")
    print("     and the comparison is made on the 70 deterministic points all share.")
    deg = [r["name"] for r in rows if r["degraded"]]
    if deg:
        print(f"  2. Degraded mode for: {', '.join(deg)}. No manifest, so the artboard is")
        print("     auto-detected and slack licensing cannot be read -- unlicensed slack is")
        print("     scored IN THEIR FAVOUR. The candidate is held to the stricter standard.")
    print("  3. Distinction is capped at 60% for libraries without data-mechanic markup,")
    print("     because tuple collisions cannot be checked on them at all.")

    (out / "benchmark.json").write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"\n  -> {out}/benchmark.json")
    return 0


# ──────────────────────────────────────────────────────────────── shots ──
def cmd_shots(args) -> int:
    import measure as measure_mod
    d = pathlib.Path(args.dir)
    if d.exists() and args.clean:
        shutil.rmtree(d)
    measure_mod.measure(pathlib.Path(args.library), args.selector, d, args.rhythm)
    print(f"  -> {d}/  ({len(list(d.glob('*.png')))} PNGs)")
    return 0


# ────────────────────────────────────────────────────────── build / preview ──
def cmd_build(args) -> int:
    """Run the project's builder. The library is regenerable or it is a liability."""
    pd = proj.find_project()
    if not pd:
        print("not inside a Creator project — nothing to build")
        return 1
    man = proj.load(pd)
    builder = proj.path_of(pd, man, "builder")
    if not builder or not builder.exists():
        print(f"no builder at {builder} — emit one:")
        lib = proj.path_of(pd, man, "library")
        print(f'  python scaffold.py builder "{lib}"')
        return 1
    print(f"building {man['name']} …")
    r = subprocess.run([sys.executable, str(builder), *(args.rest or [])],
                       cwd=str(builder.parent))
    if r.returncode == 0:
        proj.stamp(pd, "built")
        lib = proj.path_of(pd, man, "library")
        if lib and lib.exists():
            import scaffold as scaffold_mod
            scaffold_mod.install_canvas(lib.parent, man, document=lib.name, quiet=True)
            scaffold_mod.seed_slot_state(lib.parent)
        print("\nnext:  dscc.py audit    then    dscc.py preview")
    return r.returncode


def cmd_preview(args) -> int:
    import serve as serve_mod
    directory, pd, paths, builder = serve_mod.resolve_target(args)
    port = args.port
    if port is None and pd:
        try:
            port = (proj.load(pd).get("serve") or {}).get("port", 4173)
        except Exception:
            port = 4173
    return serve_mod.serve(directory, port=port or 4173,
                           open_browser=not args.no_open, page=args.page,
                           watch=args.watch, project_dir=pd, watch_paths=paths,
                           builder=builder, quiet=args.quiet)


def cmd_report(args) -> int:
    import report as report_mod
    return report_mod.run(pathlib.Path(args.project) if args.project else None,
                          open_browser=not args.no_open)


def _delegate(mod_name: str, argv: list[str]) -> int:
    """Run another script's CLI with the given argv. Keeps one entry point."""
    script = HERE / f"{mod_name}.py"
    return subprocess.run([sys.executable, str(script), *argv]).returncode


def main() -> None:
    ap = argparse.ArgumentParser(prog="dscc", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    # project management delegates to project.py so there is exactly one
    # implementation and two ways to reach it
    for name, help_ in (("new", "create an isolated project"),
                        ("list", "list projects under a root"),
                        ("info", "show this project's wiring and history"),
                        ("adopt", "pull an existing flat working directory into a project"),
                        ("set", "set a dotted key in project.json")):
        pp = sub.add_parser(name, help=help_, add_help=False)
        pp.add_argument("rest", nargs=argparse.REMAINDER)
        pp.set_defaults(fn=(lambda n: lambda a: _delegate("project", [n, *a.rest]))(name))

    bd = sub.add_parser("build", help="run the project's builder")
    bd.add_argument("rest", nargs=argparse.REMAINDER)
    bd.set_defaults(fn=cmd_build)

    pv = sub.add_parser("preview", help="serve the bundle and open the canvas")
    pv.add_argument("--dir", default=None)
    pv.add_argument("--port", type=int, default=None)
    pv.add_argument("--page", default="canvas.html")
    pv.add_argument("--no-open", action="store_true", dest="no_open")
    pv.add_argument("--watch", action="store_true",
                    help="rebuild on change and push a reload to the canvas")
    pv.add_argument("--quiet", action="store_true")
    pv.set_defaults(fn=cmd_preview)
    sv = sub.add_parser("serve", help="alias for preview --no-open")
    sv.add_argument("--dir", default=None)
    sv.add_argument("--port", type=int, default=None)
    sv.add_argument("--page", default="canvas.html")
    sv.add_argument("--watch", action="store_true")
    sv.add_argument("--quiet", action="store_true")
    sv.set_defaults(fn=cmd_preview, no_open=True)

    rp = sub.add_parser("report", help="render the whole project as one HTML page")
    rp.add_argument("--project", default=None)
    rp.add_argument("--no-open", action="store_true", dest="no_open")
    rp.set_defaults(fn=cmd_report)

    sl = sub.add_parser("slots", help="list / fill / audit image slots", add_help=False)
    sl.add_argument("rest", nargs=argparse.REMAINDER)
    sl.set_defaults(fn=lambda a: _delegate("slots", a.rest))


    d = sub.add_parser("doctor", help="check toolchain and validate a design system")
    d.add_argument("--system", default=None)
    d.set_defaults(fn=cmd_doctor)

    a = sub.add_parser("audit", help="lint + measure + uniq + score")
    a.add_argument("library", nargs="?", default=None,
                   help="omit inside a project — the manifest knows")
    a.add_argument("--project", default=None)
    a.add_argument("--note", default=None, help="recorded in audit/history.jsonl")
    a.add_argument("--strict", action="store_true",
                   help="promote every accepted-but-unresolved P2 into a failure")
    a.add_argument("--out", default="audit-out")
    a.add_argument("--selector", default=".frame")
    a.add_argument("--auto", action="store_true",
                   help="auto-detect artboards instead of using --selector "
                        "(degraded mode: for libraries not built by this plugin)")
    a.add_argument("--rhythm", type=int, default=64)
    a.add_argument("--system", default=None)
    a.add_argument("--critic", default=None)
    a.add_argument("--brief", default=None)
    a.add_argument("--plan", default=None)
    a.add_argument("--shots", default=None)
    a.add_argument("--top", type=int, default=8)
    a.set_defaults(fn=cmd_audit)

    b = sub.add_parser("bench", help="compare a candidate against reference libraries")
    b.add_argument("candidate")
    b.add_argument("references", nargs="+")
    b.add_argument("--out", default="bench-out")
    b.add_argument("--selector", default=".frame")
    b.add_argument("--rhythm", type=int, default=64)
    b.set_defaults(fn=cmd_bench)

    s = sub.add_parser("shots", help="render per-card PNGs for the critic")
    s.add_argument("library")
    s.add_argument("dir")
    s.add_argument("--selector", default=".frame")
    s.add_argument("--rhythm", type=int, default=64)
    s.add_argument("--clean", action="store_true")
    s.set_defaults(fn=cmd_shots)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
