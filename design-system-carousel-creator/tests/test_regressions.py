"""
Regression tests for the defects that were found by reading and then running the code.

    python -m unittest discover -s tests -v        (from the plugin root)

Stdlib only, no browser, no network: these cover the pure-Python logic. The Playwright
side (measure.py) is exercised by `dscc.py audit` on a real project.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lint      # noqa: E402
import project   # noqa: E402
import score     # noqa: E402
import scaffold  # noqa: E402
import uniq      # noqa: E402


class RawPx(unittest.TestCase):
    """px.rstrip('.0') used to turn 10, 20, 100, 200, 1000 into 1 or 2 and pass them."""

    def test_hairlines_are_allowed_however_spelled(self):
        for px in ("0", "1", "2", "1.0", "2.0", "0.0"):
            self.assertTrue(lint._px_allowed(px), px)

    def test_everything_else_is_flagged(self):
        for px in ("10", "20", "100", "200", "1000", "3", "24", "12.0", "2.5", "0.5"):
            self.assertFalse(lint._px_allowed(px), px)


class Attribution(unittest.TestCase):
    """`\\b©` needs a word character before it, so '© 2024 Acme' never matched."""

    def test_copyright_notices(self):
        for s in ("Acme © 2024", "© 2024 Acme", "Acme© 2024", "(c) 2021 Acme", "2024 ©"):
            self.assertTrue(lint.ATTRIBUTION_RE.search(s), s)

    def test_plain_years_are_not_attribution(self):
        for s in ("Revenue grew in 2024", "A 2024 plan"):
            self.assertFalse(lint.ATTRIBUTION_RE.search(s), s)


def _card(i, slack=100, cov=0.55):
    return {"index": i, "overflow": [], "collisions": [], "coverage": cov, "max_row_gap": 60,
            "bottom_slack": slack, "content_boxes": 8, "media_boxes": 0, "tiny_media": 0,
            "layout": f"L{i}", "intent": "fill"}


def _score(uniq_defects=(), critic=None, brief=None, per_card=None, slack=100):
    cards = [_card(i, slack) for i in range(1, 6)]
    measure = {"cards": cards, "library": {"gap_ceiling": 96, "gap_cv": 0.1,
                                           "distinct_font_sizes": 10, "distinct_gaps": 8}}
    uniq = {"duplicates": {}, "mean_distance": 3.0, "distribution": {"partitions_used": 9},
            "defects": list(uniq_defects)}
    lint_json = {"counts": {}, "defects": [], "per_card": per_card or []}
    return score.score(lint_json, measure, uniq, critic=critic, brief=brief)


class Scoring(unittest.TestCase):
    def test_flat_surfaces_costs_points_and_fails_distinction(self):
        base = _score()
        flat = _score([{"code": "FLAT_SURFACES", "severity": "P1", "detail": "2 grounds"}])
        self.assertEqual(round(base["dimensions"]["distinction"] - flat["dimensions"]["distinction"], 2), 5)
        self.assertLess(flat["dimensions"]["distinction"], score.GATE["distinction"])
        self.assertEqual(flat["gate"], "FAIL")

    def test_ground_clusters_cost_one_each_capped_at_two(self):
        base = _score()["dimensions"]["distinction"]
        three = _score([{"code": "GROUND_CLUSTER", "severity": "P2", "detail": "x"}] * 3)
        self.assertEqual(round(base - three["dimensions"]["distinction"], 2), 2)

    def test_unscored_craft_is_described_as_scaled_not_out_of_100(self):
        sc = _score()
        self.assertIn("craft", sc["unscored"])
        self.assertEqual(sc["scored_out_of"], 70)             # integrity..distinction, no brief
        self.assertIn("raw_points", sc)
        note = next(d for d in sc["defects"] if d["code"] == "NO_CRITIC")["detail"]
        self.assertIn("scaled to 100", note)
        self.assertNotIn("out of 80", note)

    def test_licensed_slack_over_520_needs_critic_signoff(self):
        def run(signoff):
            cards = [dict(_card(1, slack=600), intent="breathe", license="cover")]
            measure = {"cards": cards, "library": {"gap_ceiling": 96, "gap_cv": 0.1}}
            uniq = {"duplicates": {}, "mean_distance": 3.0,
                    "distribution": {"partitions_used": 9}, "defects": []}
            critic = {"cards": [], "slack_signoff": signoff}
            return score.score({"counts": {}, "defects": []}, measure, uniq, critic=critic)
        self.assertTrue(any(d["code"] == "SLACK_REVIEW" for d in run([])["defects"]))
        self.assertFalse(any(d["code"] == "SLACK_REVIEW" for d in run([1])["defects"]))

    def test_veracity_counts_figure_field_and_per_claim_reuse(self):
        claims = [{"id": f"c{i:03d}", "text": "A claim", "figure": "7,500"} for i in range(1, 4)]
        brief = {"claims": claims}
        per = [{"index": i, "claims": ["c001"], "text": "We reached 7,500 people"}
               for i in range(1, 6)]
        sc = _score(brief=brief, per_card=per)
        codes = [d["code"] for d in sc["defects"]]
        self.assertNotIn("INVENTED_FIGURE", codes)            # 7,500 is only in `figure`
        self.assertIn("CLAIM_REUSE", codes)                   # c001 on five cards


    def test_sentence_punctuation_is_not_part_of_a_figure(self):
        brief = {"claims": [{"id": "c001", "text": "Rates rose 40% in 2024, to 7,500.5"}]}
        per = [{"index": i, "claims": ["c001"], "text": "In 2024, rates rose 40%. Now 7,500.5."}
               for i in range(1, 3)]
        sc = _score(brief=brief, per_card=per)
        self.assertNotIn("INVENTED_FIGURE", [d["code"] for d in sc["defects"]])

    def test_critic_rows_without_an_index_do_not_halve_craft(self):
        perfect = {s: 5 for s in ("hierarchy", "social_native", "thumbnail", "copy", "interest")}
        sc = _score(critic={"cards": [dict(perfect, index=1), dict(perfect), dict(perfect)]})
        self.assertEqual(sc["dimensions"]["craft"], 20)

    def test_web_chrome_costs_the_card_it_is_on(self):
        lint_json = {"counts": {"WEB_CHROME": 1}, "per_card": [],
                     "defects": [{"code": "WEB_CHROME", "severity": "P1", "card": 3,
                                  "detail": "<button> element in a social artboard"}]}
        sc = score.score(lint_json, {"cards": [_card(i) for i in range(1, 6)], "library": {}},
                         {"duplicates": {}, "mean_distance": 3.0, "defects": []})
        by = {c["index"]: c["score"] for c in sc["cards"]}
        self.assertLess(by[3], by[2])


class Lint(unittest.TestCase):
    def _lint(self, html):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "lib.dc.html"
            p.write_text(html, encoding="utf-8")
            return lint.lint(p)

    def test_fallbacks_and_set_properties_are_not_undeclared(self):
        html = ("<style>:root{--a:1px}.x{width:var(--a);border-radius:var(--r, 50%);"
                "display:var(--label-vis)}.y{color:var(--missing)}</style>"
                "<script>r.setProperty('--label-vis','block')</script>")
        undeclared = {d["detail"] for d in self._lint(html)["defects"]
                      if d["code"] == "UNDECLARED_VAR"}
        self.assertEqual(undeclared, {"--missing"})


class Uniq(unittest.TestCase):
    def test_a_bare_list_plan_loads(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "plan.json"
            p.write_text('[{"index": 1, "partition": "duo"}]', encoding="utf-8")
            self.assertEqual(len(uniq.load_cards(p)), 1)

    def test_flush_is_not_a_ground(self):
        grounds = ["paper", "panel", "ink", "accent-1", "flush"]
        cards = [{"index": i + 1, "partition": "duo", "flow": "vertical", "enumerator": "none",
                  "emphasis": "display", "media": "none", "chrome": g, "layout": f"L{i}"}
                 for i, g in enumerate(grounds)]
        res = uniq.analyse(cards)
        self.assertIn("FLAT_SURFACES", [d["code"] for d in res["defects"]])


class ProjectNaming(unittest.TestCase):
    def test_safe_filename_is_legal_on_windows_and_url_safe(self):
        name = project.safe_filename('Q3 "Launch": v2? #1 | 100%')
        for ch in '<>:"/\\|?*#%':
            self.assertNotIn(ch, name)
        self.assertTrue(name)
        self.assertEqual(project.safe_filename('???'), project.slugify('???'))

    def test_manifest_keeps_display_name_but_cleans_library_path(self):
        man = project.default_manifest('Q3 "Launch" #2')
        self.assertEqual(man["name"], 'Q3 "Launch" #2')
        self.assertNotIn('"', man["artifacts"]["library"])
        self.assertNotIn("#", man["artifacts"]["library"])


class Scaffold(unittest.TestCase):
    def test_canvas_placeholders_are_escaped_for_their_context(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d)
            man = {"name": 'A "B" <i>&</i> #1', "canvas": {"width": 1080, "height": 1440}}
            scaffold.install_canvas(out, man, document="a b#1.dc.html", quiet=True)
            html = (out / "canvas.html").read_text(encoding="utf-8")
        self.assertNotIn("__DOC_", html)
        self.assertIn("&lt;i&gt;", html)                      # title is HTML-escaped
        self.assertIn('const DOC_SRC = "./a%20b%231.dc.html";', html)   # JS-safe, URL-quoted

    def test_builder_emits_parseable_python_for_hostile_names(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            doc = root / "dist" / "lib.dc.html"
            doc.parent.mkdir()
            doc.write_text("<html></html>", encoding="utf-8")
            (root / "project.json").write_text("{}", encoding="utf-8")
            man = {"name": 'Say "hi" \\ and """ and */', "artifacts": {"builder": "build/build.py"}}
            dst = scaffold.emit_builder(doc, man, cols=5, theme="Black")
            compile(dst.read_text(encoding="utf-8"), str(dst), "exec")

    def test_builder_template_resolves_plugin_without_a_baked_path(self):
        src = (ROOT / "assets" / "builder" / "build.py.tmpl").read_text(encoding="utf-8")
        self.assertIn("DSCC_PLUGIN_ROOT", src)
        self.assertIn("def ground_class", src)
        self.assertIn("def mechanic_of", src)
        self.assertIn("inject_tokens(doc, TOKENS_LIGHT)", src)


class Bundle(unittest.TestCase):
    def test_react_is_vendored_and_matches_the_runtimes_pinned_hashes(self):
        import base64
        import hashlib
        import re
        runtime = (ROOT / "assets" / "runtime" / "support.js").read_text(encoding="utf-8")
        pins = dict(re.findall(r'(REACT(?:_DOM)?)_SRI = "sha384-([^"]+)"', runtime))
        for key, fname in (("REACT", "react.production.min.js"),
                           ("REACT_DOM", "react-dom.production.min.js")):
            blob = (ROOT / "assets" / "runtime" / "vendor" / fname).read_bytes()
            digest = base64.b64encode(hashlib.sha384(blob).digest()).decode()
            self.assertEqual(digest, pins[key], fname)

    def test_scaffold_maps_unpkg_to_vendor(self):
        self.assertIn("window.__resources", scaffold.HEAD_TMPL)
        self.assertIn("./vendor/react.production.min.js", scaffold.HEAD_TMPL)

    def test_kernel_default_artboard_matches_project_default(self):
        css = (ROOT / "skills" / "carousel-craft" / "assets" / "kernel.css").read_text(encoding="utf-8")
        self.assertIn("--card-h:1440px", css)
        self.assertNotIn("img-slot", css)

    def test_command_frontmatter_hints_are_quoted_yaml(self):
        """An unquoted `argument-hint: [--watch]` is a YAML parse error and drops ALL metadata."""
        for f in sorted((ROOT / "commands").glob("*.md")):
            line = next((l for l in f.read_text(encoding="utf-8").splitlines()
                         if l.startswith("argument-hint:")), None)
            if line:
                val = line.split(":", 1)[1].strip()
                self.assertTrue(val.startswith('"') and val.endswith('"'), f"{f.name}: {val}")

    def test_plugin_manifests_are_valid_json(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "design-system-carousel-creator")
        market = json.loads((ROOT.parent / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(market["plugins"][0]["source"], "./design-system-carousel-creator")

    def test_one_version_everywhere(self):
        """plugin.json is the source; the marketplace, changelog and scorecards follow it."""
        version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        market = json.loads((ROOT.parent / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(market["plugins"][0]["version"], version)
        self.assertIn(f"## {version}", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertEqual(score.plugin_version(), version)
        self.assertEqual(_score()["scorer_version"], version)


class DefectCatalogue(unittest.TestCase):
    def test_every_scored_code_has_a_dimension_and_a_legal_fix(self):
        for code in score.DEFECT_DIM:
            self.assertTrue(score.LEGAL_FIX.get(code), code)

    def test_every_emitted_code_is_documented(self):
        import re
        shapes = re.compile(r'"code":\s*"([A-Z_]+)"|add\("([A-Z_]+)"|\("([A-Z_]+)", "P[012]"')
        emitted = {code for f in (ROOT / "scripts").glob("*.py")
                   for groups in shapes.findall(f.read_text(encoding="utf-8"))
                   for code in groups if code}
        doc = (ROOT / "docs" / "09-defects.md").read_text(encoding="utf-8")
        missing = sorted(c for c in emitted if f"`{c}`" not in doc)
        self.assertEqual(missing, [])

    def test_off_scale_reaches_the_scorecard_once(self):
        lint_json = {"counts": {}, "per_card": [],
                     "defects": [{"code": "OFF_SCALE", "severity": "P2", "detail": f"{p}px is off"}
                                 for p in (13, 17, 23)]}
        cards = [_card(i) for i in range(1, 6)]
        sc = score.score(lint_json, {"cards": cards, "library": {}},
                         {"duplicates": {}, "mean_distance": 3.0, "defects": []}, strict=True)
        off = [d for d in sc["defects"] if d["code"] == "OFF_SCALE"]
        self.assertEqual(len(off), 1)
        self.assertIn("13px", off[0]["detail"])
        self.assertTrue(any("--strict" in r for r in sc["gate_reasons"]))


if __name__ == "__main__":
    unittest.main()
