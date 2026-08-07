"""
Design System Carousel Creator -- project report.

    python report.py                 # inside a project
    python report.py --project DIR --no-open

Renders the whole project as one self-contained HTML page: scorecard, dimension
bars, the score trail across refine passes, the per-card table with defects and
their legal fixes, thumbnails, and the constraints that were checked.

This is what you send to someone who is not going to read JSON. It exists because
"99.6/100, gate PASS" is a sentence, and the interesting part of a scorecard is
always the ten lines under it -- which dimension is carrying the total, which card
is weakest, what was accepted rather than fixed, and what was never scored at all.
A report that lists only successes is marketing.

Self-contained by construction: thumbnails are inlined as data URIs, so the file
can be emailed, and nothing in it phones anywhere.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import html as _html
import json
import pathlib
import sys
import webbrowser

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import project as proj      # noqa: E402
import score as score_mod   # noqa: E402

THUMB_LIMIT = 60
THUMB_BYTES = 220_000       # per image, before we skip it


def esc(s) -> str:
    return _html.escape(str(s if s is not None else ""))


def data_uri(p: pathlib.Path) -> str | None:
    try:
        if p.stat().st_size > THUMB_BYTES:
            return None
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    except OSError:
        return None


CSS = """
*{box-sizing:border-box}
body{margin:0;background:#0f0e0d;color:#eae7e1;
     font:400 14px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;
     -webkit-font-smoothing:antialiased}
a{color:#fe6a3c}
.wrap{max-width:1100px;margin:0 auto;padding:56px 28px 96px}
h1{font-size:34px;line-height:1.15;margin:0 0 6px;font-weight:500;letter-spacing:-.02em}
h2{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#8c8781;
   margin:52px 0 14px;font-weight:600}
.sub{color:#8c8781;font-size:13px;margin:0 0 34px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
      font-variant-numeric:tabular-nums}
.hero{display:flex;align-items:baseline;gap:18px;flex-wrap:wrap;
      padding:24px 26px;border-radius:16px;background:#191715;border:1px solid #2b2825}
.total{font-size:56px;font-weight:600;letter-spacing:-.03em;line-height:1}
.gate{padding:5px 12px;border-radius:999px;font-size:11px;letter-spacing:.14em;
      font-weight:700}
.gate.PASS{background:#123d22;color:#6ee79a}
.gate.FAIL{background:#3d1512;color:#ff8a6b}
.note{color:#8c8781;font-size:12px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-weight:600;font-size:11px;letter-spacing:.12em;
   text-transform:uppercase;color:#8c8781;padding:8px 10px;border-bottom:1px solid #2b2825}
td{padding:9px 10px;border-bottom:1px solid #201e1c;vertical-align:top}
tr:hover td{background:#151312}
.bar{height:8px;border-radius:99px;background:#262320;overflow:hidden;min-width:120px}
.bar > i{display:block;height:100%;background:#fe6a3c;border-radius:99px}
.bar.full > i{background:#6ee79a}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;
      letter-spacing:.08em;font-weight:600;margin:0 4px 4px 0}
.P0{background:#3d1512;color:#ff8a6b}
.P1{background:#3d3312;color:#f5cd6b}
.P2{background:#232a33;color:#9dc0e0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(122px,1fr));gap:14px}
.card{border-radius:10px;overflow:hidden;background:#191715;border:1px solid #2b2825}
.card img{display:block;width:100%;height:auto}
.card .cap{padding:7px 9px;font-size:10px;color:#8c8781;display:flex;
           justify-content:space-between;gap:6px}
.card.fail{border-color:#7a2a1e}
.trail{display:flex;align-items:flex-end;gap:6px;height:96px;padding:12px 0}
.trail div{flex:1;background:#2b2825;border-radius:4px 4px 0 0;position:relative;min-width:14px}
.trail div.best{background:#fe6a3c}
.trail span{position:absolute;top:-18px;left:0;right:0;text-align:center;
            font-size:10px;color:#8c8781}
.k{color:#8c8781}
.fix{color:#8c8781;font-size:12px}
@media (prefers-color-scheme:light){
  body{background:#faf9f7;color:#1c1a17}
  .hero,.card{background:#fff;border-color:#e6e2dc}
  h2,.sub,.note,.k,.fix,.card .cap{color:#6f6a63}
  th{border-color:#e6e2dc;color:#6f6a63} td{border-color:#efece7}
  tr:hover td{background:#f4f1ec} .bar{background:#e6e2dc} .trail div{background:#e6e2dc}
}
"""


def bar(v, w) -> str:
    if v is None:
        return '<span class="note">not scored</span>'
    pct = max(0, min(100, v / w * 100))
    cls = "bar full" if pct >= 97 else "bar"
    return f'<div class="{cls}"><i style="width:{pct:.0f}%"></i></div>'


def build(pd: pathlib.Path) -> pathlib.Path:
    man = proj.load(pd)
    A = man.get("artifacts", {})
    scp = pd / A.get("scorecard", "audit/scorecard.json")
    sc = json.loads(scp.read_text(encoding="utf-8")) if scp.exists() else {}
    hist = proj.read_history(pd)
    shots = pd / man["layout"]["shots"]

    parts: list[str] = []
    add = parts.append

    cv = man.get("canvas", {})
    add(f'<div class="wrap"><h1>{esc(man.get("name"))}</h1>')
    add(f'<p class="sub">{esc(man.get("brand"))} · {cv.get("width")}×{cv.get("height")} '
        f'({esc(cv.get("ratio"))}) · {cv.get("cards")} formats · '
        f'report generated {_dt.datetime.now():%Y-%m-%d %H:%M}</p>')

    if not sc:
        add('<p class="note">No scorecard yet — run <code>dscc.py audit</code>.</p></div>')
        return write(pd, "".join(parts), man)

    unscored = sc.get("unscored") or []
    out_of = sc.get("scored_out_of", 100)
    add('<div class="hero">')
    add(f'<div class="total mono">{sc.get("total")}</div>')
    add(f'<div class="note">out of {out_of}'
        + (f' — {", ".join(unscored)} not scored' if unscored else "") + "</div>")
    add(f'<div style="flex:1"></div><div class="gate {esc(sc.get("gate"))}">'
        f'{esc(sc.get("gate"))}</div></div>')

    if sc.get("gate_reasons"):
        add('<h2>Why the gate failed</h2><ul>')
        for r in sc["gate_reasons"]:
            add(f"<li>{esc(r)}</li>")
        add("</ul>")

    # ── dimensions ──────────────────────────────────────────────────────
    add("<h2>Dimensions</h2><table><tr><th>dimension</th><th>score</th>"
        "<th style='width:40%'></th><th>method</th></tr>")
    method = {"integrity": "deterministic", "discipline": "deterministic",
              "density": "deterministic", "distinction": "deterministic",
              "veracity": "deterministic (needs a brief)", "craft": "judged (critic agent)"}
    for k, w in score_mod.WEIGHTS.items():
        v = sc["dimensions"].get(k)
        val = "—" if v is None else f"{v:.1f} / {w}"
        add(f'<tr><td>{k}</td><td class="mono">{val}</td><td>{bar(v, w)}</td>'
            f'<td class="fix">{method[k]}</td></tr>')
    add("</table>")

    if sc.get("constraints_checked"):
        mark = "clean" if sc.get("constraints_clean") else "BREACHED"
        add(f'<h2>Constraints</h2><p>{esc(", ".join(sc["constraints_checked"]))} '
            f'&rarr; <b>{mark}</b></p>')

    # ── trail ───────────────────────────────────────────────────────────
    if len(hist) > 1:
        add(f"<h2>Score trail — {len(hist)} audits</h2><div class='trail'>")
        best = max((h.get("total") or 0) for h in hist)
        for h in hist[-24:]:
            t = h.get("total") or 0
            cls = " class='best'" if t == best else ""
            add(f"<div{cls} style='height:{max(6, t)}%'><span>{t}</span></div>")
        add("</div>")
        add(f'<p class="note">first {hist[0].get("total")} → latest '
            f'{hist[-1].get("total")} · best {best}</p>')

    # ── defects ─────────────────────────────────────────────────────────
    if sc.get("defect_counts"):
        add("<h2>Defects</h2><table><tr><th>code</th><th>n</th><th>severity</th>"
            "<th>legal fix</th></tr>")
        sev = {}
        for d in sc.get("defects", []):
            sev.setdefault(d["code"], d["severity"])
        for code, n in sorted(sc["defect_counts"].items(), key=lambda kv: -kv[1]):
            s = sev.get(code, "P2")
            add(f'<tr><td class="mono">{esc(code)}</td><td class="mono">{n}</td>'
                f'<td><span class="pill {s}">{s}</span></td>'
                f'<td class="fix">{esc(score_mod.LEGAL_FIX.get(code, ""))}</td></tr>')
        add("</table>")

    # ── cards ───────────────────────────────────────────────────────────
    rows = sorted(sc.get("cards", []), key=lambda r: r["score"])
    if rows:
        add(f"<h2>Cards — weakest first</h2><table><tr><th>#</th><th>format</th>"
            f"<th>score</th><th>cov</th><th>gap</th><th>defects</th></tr>")
        for r in rows[:20]:
            codes = " ".join(f'<span class="pill {d["severity"]}">{esc(d["code"])}</span>'
                             for d in r.get("defects", [])[:5]) or '<span class="note">—</span>'
            add(f'<tr><td class="mono">{r["index"]:02d}</td><td>{esc(r.get("layout"))}</td>'
                f'<td class="mono">{r["score"]:.1f}</td>'
                f'<td class="mono">{r["coverage"]:.0%}</td>'
                f'<td class="mono">{r["max_row_gap"]}</td><td>{codes}</td></tr>')
        add("</table>")
        if len(rows) > 20:
            add(f'<p class="note">{len(rows) - 20} more cards, all above '
                f'{rows[19]["score"]:.1f}</p>')

    # ── thumbnails ──────────────────────────────────────────────────────
    pngs = sorted(shots.glob("*.png"))[:THUMB_LIMIT] if shots.is_dir() else []
    if pngs:
        by_idx = {r["index"]: r for r in sc.get("cards", [])}
        add(f"<h2>Renders — {len(pngs)} cards</h2><div class='grid'>")
        for i, p in enumerate(pngs, 1):
            uri = data_uri(p)
            if not uri:
                continue
            row = by_idx.get(i)
            bad = row and any(d["severity"] == "P0" for d in row.get("defects", []))
            add(f'<div class="card{" fail" if bad else ""}"><img src="{uri}" alt="card {i}">'
                f'<div class="cap"><span class="mono">{i:02d}</span>'
                f'<span class="mono">{row["score"]:.0f}</span></div></div>'
                if row else
                f'<div class="card"><img src="{uri}" alt="card {i}">'
                f'<div class="cap"><span class="mono">{i:02d}</span></div></div>')
        add("</div>")

    # ── reproduce ───────────────────────────────────────────────────────
    add("<h2>Reproduce</h2><table>")
    for label, key in (("design system", "system"), ("content brief", "brief"),
                       ("layout plan", "plan"), ("builder", "builder"),
                       ("library", "library")):
        rel = A.get(key)
        exists = rel and (pd / rel).exists()
        add(f'<tr><td>{label}</td><td class="mono">{esc(rel or "—")}</td>'
            f'<td class="fix">{"present" if exists else "missing"}</td></tr>')
    add("</table>")
    add('<p class="note" style="margin-top:26px">'
        'python build/build.py &nbsp;·&nbsp; dscc.py audit &nbsp;·&nbsp; dscc.py preview</p>')
    add("</div>")
    return write(pd, "".join(parts), man)


def write(pd: pathlib.Path, body: str, man: dict) -> pathlib.Path:
    out = pd / (man.get("layout", {}).get("audit", "audit")) / "report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(man.get('name'))} — quality report</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>",
        encoding="utf-8")
    return out


def run(project_dir: pathlib.Path | None = None, open_browser: bool = True) -> int:
    pd = proj.find_project(project_dir)
    if not pd:
        print("not inside a Creator project (no project.json found walking up)")
        return 1
    out = build(pd)
    print(f"report -> {out}  ({out.stat().st_size // 1024} KB, self-contained)")
    if open_browser:
        webbrowser.open(out.resolve().as_uri())
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=None)
    ap.add_argument("--no-open", action="store_true", dest="no_open")
    a = ap.parse_args()
    sys.exit(run(pathlib.Path(a.project) if a.project else None, not a.no_open))


if __name__ == "__main__":
    main()
