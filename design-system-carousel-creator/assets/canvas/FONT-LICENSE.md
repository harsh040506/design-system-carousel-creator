# JetBrains Mono

`JetBrainsMono-latin.woff2.base64` is the latin subset of the JetBrains Mono
variable font, base64-encoded, vendored so the canvas host has no network
dependency of any kind.

- **Font:** JetBrains Mono
- **Copyright:** © 2020 The JetBrains Mono Project Authors
- **License:** SIL Open Font License 1.1 — <https://scripts.sil.org/OFL>
- **Upstream:** <https://github.com/JetBrains/JetBrainsMono>

The OFL permits bundling and redistribution with or without modification,
provided the font is not sold on its own and the copyright and license notice
travel with it. This file is that notice.

`scaffold.py` splices the encoded font into `canvas.html` as a `data:` URI at
install time, so a built bundle is one self-contained HTML file with zero
external requests. Nothing else in the plugin loads a webfont.

## Why it is vendored rather than linked

The canvas is the one part of the toolchain a designer looks at. Linking a
webfont makes its typography a function of network conditions: on a plane, on a
locked-down corporate network, or behind a proxy that blocks `fonts.gstatic.com`,
the interface silently falls back to whatever monospace the OS supplies and the
labels reflow. That is a small failure with an outsized effect — it makes the
tool look broken at the exact moment you are judging whether the work looks good.

40 KB, once, removes the question.
