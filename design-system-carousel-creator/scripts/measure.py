"""
Design System Carousel Creator -- geometry harness.

Renders a template library in headless Chromium and measures every artboard:
bounds violations, text collisions, ink coverage, inter-row gaps, bottom slack,
type/spacing drift, and text contrast.

Everything here is deliberately mechanical. The lesson that produced this file is
that an early version reported every card as "very tight" because it measured the
footer element instead of the footer's top rule, and flagged card 1 as
overflowing because it measured a motif that bleeds off-frame on purpose. Both
were confident, precise and wrong. So: decoration is excluded explicitly, the
footer rule is found explicitly, and the raw numbers are always emitted alongside
the verdicts so a disagreement can be adjudicated instead of argued.

Usage:
    python measure.py LIBRARY.html [--out measure.json] [--shots DIR]
                                   [--selector .frame] [--rhythm 64]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

PROBE_JS = r"""
(cfg) => {
  const DECOR = '.motif,.sphere,.dot-grid,.bleed,.scrim,.grain';
  const CHROME = '.masthead,.foot,.footer,.signature';

  // ---- locate artboards -----------------------------------------------
  let cards = [];
  if (cfg.selector) {
    cards = Array.from(document.querySelectorAll(cfg.selector));
  }
  if (!cards.length) {
    // Auto-detect: the artboard is the fixed pixel width that repeats most.
    const tally = new Map();
    for (const el of document.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (r.width >= 700 && r.height >= 800) {
        const k = Math.round(r.width);
        tally.set(k, (tally.get(k) || 0) + 1);
      }
    }
    let best = null, bestN = 0;
    for (const [w, n] of tally) if (n > bestN || (n === bestN && w > best)) { best = w; bestN = n; }
    if (best !== null) {
      const all = Array.from(document.querySelectorAll('*')).filter(el => {
        const r = el.getBoundingClientRect();
        return Math.round(r.width) === best && r.height >= 800;
      });
      // keep only outermost candidates
      cards = all.filter(el => !all.some(o => o !== el && o.contains(el)));
    }
  }

  // ---- helpers ---------------------------------------------------------
  const seen = new WeakMap();
  const cs = el => { let v = seen.get(el); if (!v) { v = getComputedStyle(el); seen.set(el, v); } return v; };

  const hasOwnText = el => {
    for (const n of el.childNodes)
      if (n.nodeType === 3 && n.nodeValue.trim().length) return true;
    return false;
  };

  const parseRGB = s => {
    const m = String(s).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = c => {
    const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const contrast = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };
  const effectiveBg = el => {
    let n = el;
    while (n && n !== document.documentElement) {
      const c = parseRGB(cs(n).backgroundColor);
      if (c && c.a > 0.5) return c;
      if (cs(n).backgroundImage !== 'none') return null; // photo / gradient: unscoreable
      n = n.parentElement;
    }
    return parseRGB('rgb(255,255,255)');
  };

  const px = v => { const n = parseFloat(v); return Number.isFinite(n) ? Math.round(n) : 0; };

  // ---- per-card --------------------------------------------------------
  const out = [];
  cards.forEach((card, idx) => {
    const cr = card.getBoundingClientRect();
    const st = cs(card);
    const pad = { t: px(st.paddingTop), r: px(st.paddingRight), b: px(st.paddingBottom), l: px(st.paddingLeft) };

    const content = [];   // real content boxes, card-relative
    const decor = [];
    const fontSizes = [], gaps = [], margins = [];
    let minFont = Infinity, lowContrast = 0, minContrast = Infinity, textCount = 0;

    for (const el of card.querySelectorAll('*')) {
      const s = cs(el);
      if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;

      const box = {
        x: r.left - cr.left, y: r.top - cr.top, w: r.width, h: r.height,
        tag: el.tagName.toLowerCase(),
        cls: (el.getAttribute('class') || '').slice(0, 90)
      };

      const isDecor = el.matches(DECOR) || el.closest(DECOR);
      if (isDecor) { decor.push(box); continue; }

      const isChrome = el.matches(CHROME) || el.closest(CHROME);
      const text = hasOwnText(el);
      const media = ['img', 'img-slot', 'image-slot', 'svg', 'canvas', 'picture', 'video'].includes(box.tag);
      const filled = (() => {
        const c = parseRGB(s.backgroundColor);
        return (c && c.a > 0.02) || s.backgroundImage !== 'none';
      })();

      if (text) {
        const fs = parseFloat(s.fontSize);
        fontSizes.push(Math.round(fs));
        if (fs < minFont) minFont = fs;
        textCount++;
        const fg = parseRGB(s.color), bg = effectiveBg(el);
        if (fg && bg) {
          const ratio = contrast(fg, bg);
          if (ratio < minContrast) minContrast = ratio;
          if (ratio < 4.5 && fs < 30) lowContrast++;
        }
      }
      if (s.display === 'flex' || s.display === 'grid' || s.display === 'inline-flex') {
        const g = px(s.rowGap === 'normal' ? 0 : s.rowGap);
        if (g > 0) gaps.push(g);
      }
      const mt = px(s.marginTop);
      if (mt > 0) margins.push(mt);

      // A filled box that covers essentially the whole artboard is the card's
      // SURFACE, not content. Counting it marks every raster cell and reports
      // 100% coverage on a nearly empty card -- which is how this exact bug was
      // caught, by a reference library scoring a perfect density number.
      const areaFrac = (box.w * box.h) / (cr.width * cr.height);
      const isSurface = filled && !text && !media && areaFrac > 0.85;

      if (!isChrome && !isSurface && (text || media || filled)) {
        box.text = text; box.media = media; box.chrome = false;
        content.push(box);
      } else if (isChrome) {
        box.chrome = true;
      }
    }

    // ---- bounds ---------------------------------------------------------
    const TOL = 1.5;
    const overflow = content.filter(b =>
      b.x < -TOL || b.y < -TOL || b.x + b.w > cr.width + TOL || b.y + b.h > cr.height + TOL
    ).map(b => ({ cls: b.cls, tag: b.tag,
                  over: Math.round(Math.max(0, b.x + b.w - cr.width, b.y + b.h - cr.height, -b.x, -b.y)) }));

    // ---- collisions (text vs text, non-nested, >25% of the smaller) -----
    const tb = content.filter(b => b.text);
    const collisions = [];
    for (let i = 0; i < tb.length; i++) for (let j = i + 1; j < tb.length; j++) {
      const a = tb[i], b = tb[j];
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
      const oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox <= 1 || oy <= 1) continue;
      const area = ox * oy, small = Math.min(a.w * a.h, b.w * b.h);
      // nested boxes legitimately overlap; a parent fully contains its child
      const nested = (a.x <= b.x + 1 && a.y <= b.y + 1 && a.x + a.w >= b.x + b.w - 1 && a.y + a.h >= b.y + b.h - 1) ||
                     (b.x <= a.x + 1 && b.y <= a.y + 1 && b.x + b.w >= a.x + a.w - 1 && b.y + b.h >= a.y + a.h - 1);
      if (nested) continue;
      if (area > small * 0.25) collisions.push({ a: a.cls, b: b.cls, area: Math.round(area) });
    }

    // ---- ink coverage (40x50 raster) ------------------------------------
    const COLS = 40, ROWS = 50, cw = cr.width / COLS, ch = cr.height / ROWS;
    const mark = (boxes, grid) => {
      for (const b of boxes) {
        const c0 = Math.max(0, Math.floor(b.x / cw)), c1 = Math.min(COLS - 1, Math.ceil((b.x + b.w) / cw) - 1);
        const r0 = Math.max(0, Math.floor(b.y / ch)), r1 = Math.min(ROWS - 1, Math.ceil((b.y + b.h) / ch) - 1);
        for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) grid[r * COLS + c] = 1;
      }
    };
    const gc = new Uint8Array(COLS * ROWS), gd = new Uint8Array(COLS * ROWS);
    mark(content, gc); mark(decor, gd);

    // Morphological CLOSE (dilate then erode, Chebyshev radius R) before
    // measuring. A reader perceives a text block as occupied territory,
    // including its internal leading and the hairline between two rows; the
    // raw union of leaf boxes does not, and under-reports what the eye sees by
    // roughly ten points. Closing fills holes smaller than ~2 cells (~54px)
    // and leaves genuine voids intact, which is exactly the distinction the
    // 40% requirement is about.
    const R = 2;
    const close = src => {
      const at = (g, r, c) => g[Math.min(ROWS - 1, Math.max(0, r)) * COLS +
                               Math.min(COLS - 1, Math.max(0, c))];
      const dil = new Uint8Array(COLS * ROWS), ero = new Uint8Array(COLS * ROWS);
      for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
        let v = 0;
        for (let dr = -R; dr <= R && !v; dr++) for (let dc = -R; dc <= R && !v; dc++)
          if (at(src, r + dr, c + dc)) v = 1;
        dil[r * COLS + c] = v;
      }
      for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
        let v = 1;
        for (let dr = -R; dr <= R && v; dr++) for (let dc = -R; dc <= R && v; dc++)
          if (!at(dil, r + dr, c + dc)) v = 0;
        ero[r * COLS + c] = v;
      }
      return ero;
    };
    const gcc = close(gc);
    let nc = 0, nd = 0, rawc = 0;
    for (let i = 0; i < gc.length; i++) {
      if (gc[i]) rawc++;
      if (gcc[i]) nc++; else if (gd[i]) nd++;
    }
    const coverage = (nc + 0.5 * nd) / (COLS * ROWS);
    const coverageRaw = rawc / (COLS * ROWS);

    // ---- inter-row gaps --------------------------------------------------
    // Only containers whose children are content rows. Chrome-bearing
    // containers are skipped: the space above a footer is not a row gap.
    const qualifying = [];
    for (const el of card.querySelectorAll('*')) {
      const s = cs(el);
      if (s.display !== 'flex' && s.display !== 'grid') continue;
      if (s.display === 'flex' && s.flexDirection !== 'column') continue;
      const kids = Array.from(el.children).filter(k => {
        const ks = cs(k);
        return ks.display !== 'none' && k.getBoundingClientRect().height > 2;
      });
      if (kids.length < 3) continue;
      if (kids.some(k => k.matches(CHROME) || k.querySelector(CHROME))) continue;
      if (kids.some(k => k.matches(DECOR))) continue;
      qualifying.push([el, kids]);
    }
    // Only the OUTERMOST qualifying container per branch. Nested containers
    // re-measure the same visual gaps at several depths, which inflates the
    // library-wide variance with readings that describe one rhythm, not many.
    const rowGaps = [];
    for (const [el, kids] of qualifying) {
      if (qualifying.some(([o]) => o !== el && o.contains(el))) continue;
      const rects = kids.map(k => k.getBoundingClientRect()).sort((a, b) => a.top - b.top);
      for (let i = 0; i < rects.length - 1; i++) {
        const g = rects[i + 1].top - rects[i].bottom;
        if (g > 0) rowGaps.push(Math.round(g));
      }
    }

    // ---- bottom slack ----------------------------------------------------
    // Distance from the lowest real content to the FOOTER RULE (its top edge),
    // not to the footer element. Measuring to the element understates slack by
    // the footer's own height and makes every card look crowded.
    const footEl = card.querySelector('.foot, .footer, .signature');
    const floorY = footEl ? footEl.getBoundingClientRect().top - cr.top : cr.height - pad.b;
    const bodyBoxes = content.filter(b => b.y + b.h <= floorY + 200);
    const lowest = bodyBoxes.length ? Math.max(...bodyBoxes.map(b => b.y + b.h)) : 0;
    const bottomSlack = Math.round(floorY - lowest);

    // A `.note` (or anything with margin-top:auto) is DESIGNED to sit on the
    // footer rule -- a concluding line belongs at the end of the card. Reading
    // that as "crowded" flags the intended behaviour as a defect, so the
    // crowding test has to know the difference between jammed and pinned.
    const pinnedBottom = Array.from(card.querySelectorAll('.note, [class*="note"]'))
      .concat(Array.from(card.querySelectorAll('*')).filter(e => cs(e).marginTop === 'auto'))
      .some(e => {
        const r = e.getBoundingClientRect();
        return r.height > 1 && (r.bottom - cr.top) >= floorY - 4;
      });

    const uniq = a => Array.from(new Set(a)).sort((x, y) => x - y);
    out.push({
      index: idx + 1,
      label: (card.getAttribute('data-card') || card.getAttribute('id') ||
              (card.previousElementSibling && card.previousElementSibling.textContent || '').trim().slice(0, 40) || ''),
      layout: card.getAttribute('data-layout') || null,
      intent: card.getAttribute('data-intent') || null,
      license: card.getAttribute('data-license') || null,
      w: Math.round(cr.width), h: Math.round(cr.height),
      content_boxes: content.length,
      text_nodes: textCount,
      media_boxes: content.filter(b => b.media).length,
      tiny_media: content.filter(b => b.media && b.w * b.h < 10000).length,
      overflow, collisions,
      coverage: +coverage.toFixed(4),
      coverage_raw: +coverageRaw.toFixed(4),
      pinned_bottom: pinnedBottom,
      row_gaps: rowGaps,
      max_row_gap: rowGaps.length ? Math.max(...rowGaps) : 0,
      bottom_slack: bottomSlack,
      min_font: Number.isFinite(minFont) ? Math.round(minFont) : null,
      min_contrast: Number.isFinite(minContrast) ? +minContrast.toFixed(2) : null,
      low_contrast_nodes: lowContrast,
      font_sizes: uniq(fontSizes),
      gaps: uniq(gaps),
      margins: uniq(margins)
    });
  });

  return {
    cards: out,
    fonts_ready: document.fonts ? document.fonts.status : 'unknown',
    detected: cards.length
  };
}
"""


def measure(path: pathlib.Path, selector: str | None, shots: pathlib.Path | None,
            rhythm: int = 64) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")

    url = path.resolve().as_uri()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1600},
                                device_scale_factor=1)
        # domcontentloaded, not load: reference libraries reference font CDNs that
        # may be unreachable, and waiting on "load" then hangs for the full timeout.
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass  # offline / no webfonts: metrics shift slightly, reported below
        try:
            page.evaluate("() => document.fonts && document.fonts.ready")
        except Exception:
            pass
        page.wait_for_timeout(400)

        data = page.evaluate(PROBE_JS, {"selector": selector})

        if shots:
            shots.mkdir(parents=True, exist_ok=True)
            sel = selector or ".frame"
            els = page.query_selector_all(sel)
            if not els:
                els = []
            for i, el in enumerate(els, 1):
                try:
                    el.screenshot(path=str(shots / f"card-{i:02d}.png"))
                except Exception as e:
                    print(f"  ! screenshot {i} failed: {e}", file=sys.stderr)
        browser.close()

    data["source"] = str(path)
    data["rhythm"] = rhythm
    data["degraded"] = selector is None
    _summarise(data, rhythm)
    return data


def _summarise(data: dict, rhythm: int) -> None:
    cards = data["cards"]
    if not cards:
        data["library"] = {}
        return
    allgaps = [g for c in cards for g in c["row_gaps"]]
    mean = sum(allgaps) / len(allgaps) if allgaps else 0
    var = sum((g - mean) ** 2 for g in allgaps) / len(allgaps) if allgaps else 0
    cv = (var ** 0.5 / mean) if mean else 0
    fonts = sorted({f for c in cards for f in c["font_sizes"]})
    data["library"] = {
        "cards": len(cards),
        "coverage_mean": round(sum(c["coverage"] for c in cards) / len(cards), 4),
        "coverage_min": min(c["coverage"] for c in cards),
        "gap_mean": round(mean, 1),
        "gap_cv": round(cv, 3),
        "gap_ceiling": int(rhythm * 1.5),
        "distinct_font_sizes": len(fonts),
        "font_sizes": fonts,
        "distinct_gaps": len(sorted({g for c in cards for g in c["gaps"]})),
        "cards_with_media": sum(1 for c in cards if c["media_boxes"]),
        "total_overflow": sum(len(c["overflow"]) for c in cards),
        "total_collisions": sum(len(c["collisions"]) for c in cards),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Measure a carousel template library.")
    ap.add_argument("library")
    ap.add_argument("--out", default="measure.json")
    ap.add_argument("--selector", default=None,
                    help="artboard selector; omitted = auto-detect (degraded mode)")
    ap.add_argument("--shots", default=None, help="directory to write per-card PNGs")
    ap.add_argument("--rhythm", type=int, default=64)
    a = ap.parse_args()

    data = measure(pathlib.Path(a.library), a.selector,
                   pathlib.Path(a.shots) if a.shots else None, a.rhythm)
    pathlib.Path(a.out).write_text(json.dumps(data, indent=2), encoding="utf-8")

    lib = data.get("library", {})
    print(f"measured {lib.get('cards', 0)} cards from {a.library}")
    print(f"  coverage mean {lib.get('coverage_mean', 0):.1%}  min {lib.get('coverage_min', 0):.1%}")
    print(f"  gap mean {lib.get('gap_mean', 0)}px  cv {lib.get('gap_cv', 0)}  ceiling {lib.get('gap_ceiling', 0)}px")
    print(f"  overflow {lib.get('total_overflow', 0)}  collisions {lib.get('total_collisions', 0)}")
    print(f"  distinct font sizes {lib.get('distinct_font_sizes', 0)}")
    if data.get("fonts_ready") != "loaded":
        print(f"  ! webfonts {data.get('fonts_ready')} - metrics may shift when fonts load")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
