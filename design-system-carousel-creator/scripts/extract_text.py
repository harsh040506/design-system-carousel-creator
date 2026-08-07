"""
Design System Carousel Creator -- input normalisation.

/design-system-carousel-creator:brief and /design-system-carousel-creator:distill accept content and design systems in whatever
format the user has: .md, .txt, .css, .docx, pasted text. The Read tool handles
markdown, plain text and PDF natively; it does NOT parse .docx. This script
closes that gap using only the standard library -- a .docx is a zip of XML, so
no python-docx dependency is needed.

Usage:
    python extract_text.py FILE.docx [--out FILE.txt]
    python extract_text.py FILE.docx --stdout
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _para_text(para) -> tuple[int, str]:
    style = para.find(f"{W}pPr/{W}pStyle")
    level = 0
    if style is not None:
        m = re.match(r"[Hh]eading(\d)", style.get(f"{W}val", ""))
        if m:
            level = int(m.group(1))
    text = "".join(t.text or "" for t in para.iter(f"{W}t")).strip()
    return level, text


def docx_to_text(path: pathlib.Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find(f"{W}body")
    if body is None:
        return ""

    # Single pass over BODY-LEVEL children only, in document order. Walking
    # w:p and w:tbl separately with iter() double-counts every paragraph that
    # lives inside a table cell -- it gets picked up once as a loose paragraph
    # and again as a table cell, and the table content appears twice.
    lines: list[str] = []
    for child in body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            level, text = _para_text(child)
            if text:
                lines.append(("#" * level + " " + text) if level else text)
        elif tag == "tbl":
            for row in child.iter(f"{W}tr"):
                cells = []
                for cell in row.iter(f"{W}tc"):
                    cell_text = "".join(t.text or "" for t in cell.iter(f"{W}t")).strip()
                    cells.append(cell_text)
                if any(cells):
                    lines.append(" | ".join(cells))

    return "\n\n".join(lines)


def normalise(path: pathlib.Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return docx_to_text(path)
    if suffix in (".md", ".txt", ".css", ".json"):
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        sys.exit(f"{path}: use the Read tool directly for PDF (it has native page-range support)")
    if suffix == ".doc":
        sys.exit(f"{path}: legacy .doc binary format is not parseable without external tools; "
                 "re-save as .docx or paste the text directly")
    sys.exit(f"{path}: unrecognised extension '{suffix}' -- supported: .docx .md .txt .css .json .pdf")


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalise a content/design-system file to plain text.")
    ap.add_argument("file")
    ap.add_argument("--out", default=None)
    ap.add_argument("--stdout", action="store_true")
    a = ap.parse_args()

    path = pathlib.Path(a.file)
    if not path.exists():
        sys.exit(f"not found: {path}")
    text = normalise(path)

    if a.stdout or not a.out:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(text)
    if a.out:
        pathlib.Path(a.out).write_text(text, encoding="utf-8")
        print(f"\n-> {a.out} ({len(text)} chars)", file=sys.stderr)


if __name__ == "__main__":
    main()
