# Documentation

A complete guide to the Design System Carousel Creator, in reading order.

| | | |
|---|---|---|
| 1 | [**Getting started**](01-getting-started.md) | Install, check the toolchain, build your first library in about ten minutes |
| 2 | [**Concepts**](02-concepts.md) | Projects, the six-dimension score, mechanic tuples, the density law, named surfaces. Read this once and the rest of the tool explains itself |
| 3 | [**The pipeline**](03-pipeline.md) | Every stage from brand document to shipped bundle, what each one writes, and when to re-run it |
| 4 | [**Command reference**](04-commands.md) | All twelve slash commands and their main flags (full flag tables in the CLI reference) |
| 5 | [**CLI reference**](05-cli.md) | The Python scripts, usable without Claude at all — in CI, in a Makefile, on someone else's library |
| 6 | [**The canvas**](06-canvas.md) | Pan, zoom, dark mode, card index, audit overlay, live reload, presenter mode |
| 7 | [**Constraints**](07-constraints.md) | Turning "each card must stand alone" and "don't mention the source" into checks that run every time |
| 8 | [**Authoring cards**](08-authoring.md) | Writing the builder: the rules that keep fifty cards looking like one library |
| 9 | [**Defect reference**](09-defects.md) | Every code the auditor emits, what causes it, and the one legal fix |
| 10 | [**Troubleshooting**](10-troubleshooting.md) | Symptoms, causes, fixes — including the ones that look like bugs and aren't |
| 11 | [**Extending**](11-extending.md) | New mechanics, new checks, new artboard sizes, adapting the plugin to your own house style |
| — | [**Changelog**](../CHANGELOG.md) | What changed in each version, and which changes make scores incomparable |

## The short version

```bash
pip install playwright && playwright install chromium

# in Claude Code
/design-system-carousel-creator:run DESIGN.md source.pdf
```

That one command runs the whole pipeline and ends with the library open on a canvas
in your browser. Everything else in these docs is either a stage you can run on its
own, or an explanation of a decision the pipeline already made for you.

## What this tool is

It takes a **brand design system** (a style guide, a CSS file, a Tailwind theme, a
PDF brand book) and a **pile of source documents**, and produces a library of fifty
social-carousel slide templates — one self-contained HTML file, both themes, ready to
hand to a designer or a content team.

The generation is the easy half. The reason this exists is the other half: eighty of
the hundred quality points are **measured, not judged**. Overflow, text collisions, ink
coverage, gap regularity, token conformance, layout uniqueness, claim provenance. All
computed by a headless browser and some arithmetic, identical on every run, diffable
across versions, and arguable with evidence rather than taste.

## What it is not

- Not a slide *content* generator. It builds templates and fills them from claims it can
  trace back to your sources. It will not invent a statistic.
- Not an image editor. Media slots take local files; it never hotlinks.
- Not a publishing tool. It stops at the design; export and scheduling are yours.
