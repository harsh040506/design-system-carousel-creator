# Theming a library

One document, two themes, one `applyTheme()`. This file is short because the rule is short and the
failure it prevents is expensive.

---

## The mechanism

`applyTheme()` builds one object literal per theme and writes every key as a custom property on
`:root`:

```js
applyTheme() {
  const dark = (this.props.theme ?? 'Black') === 'Black';
  const r = document.documentElement.style;
  const v = dark
    ? { surface:'#0F0D0D', ink:'#F4F2F0', 'motif-fill':'radial-gradient(…dark…)' }
    : { surface:'#F4F2F0', ink:'#0F0D0D', 'motif-fill':'radial-gradient(…light…)' };
  for (const k in v) r.setProperty('--' + k, v[k]);
  r.setProperty('--label-vis', (this.props.showLabels ?? true) ? 'block' : 'none');
}
```

Never emit separate light and dark documents. They drift apart within a day and double the
maintenance surface for a benefit nobody asked for.

---

## The law

> **Every colour used in card markup belongs in BOTH theme maps.**

A colour declared once in `:root` and referenced from a card cannot respond to the theme. On a
two-theme document that means it is not "theme-neutral" — it is **provably wrong in one of them**.

`lint.py` emits `MONO_THEME_TOKEN` (P1) for exactly this: a property that is colour-valued, declared
in `:root`, used inside card markup, and present in neither branch of `applyTheme()`.

### Where this came from

A brand motif — one cropped circle, used on about a third of the cards — had its fill declared once.
It was made *ground-aware*, so it took a different value on `paper` than on `ink`, and that felt like
the hard part.

It was not theme-aware. In dark mode, on the light `paper` ground, it rendered as a dark disc under
dark type. Flipping to light mode mirrored the bug precisely: a light disc under white type on the
inverted ground. Both illegible; each one invisible while you were looking at the other theme.

The fix was to make all five motif fills theme tokens swapped by `applyTheme()`. The lesson is that
ground-awareness and theme-awareness are two different axes and satisfying one feels like satisfying
both.

### The illegal fix

Picking a single colour that is *acceptable* on both themes. It clears the check, it takes a minute,
and it is how you get a library where nothing is quite right anywhere. The motif is supposed to be
tonal against whatever it sits on; a compromise value is tonal against nothing.

---

## Ground-awareness is separate, and still required

A named surface set means one card markup shape renders on `paper`, `panel`, `ink`, `accent-1`,
`accent-2` and `grey`. Ground classes remap the role tokens on `.frame`:

```css
.frame.g-panel { --surface: var(--panel-bg); --ink: var(--panel-fg); --rule: var(--panel-rule) }
```

So the two axes multiply: **six grounds × two themes = twelve states every card-level colour must
survive.** The token indirection is what makes that tractable — a card that names a role rather than
a colour is correct in all twelve by construction, and a card carrying a raw hex is correct in one.

That is the real reason `RAW_HEX` in card markup is a defect rather than a preference.

---

## Check it by looking

```
dscc.py preview      # then press D
```

The canvas toggle drives both the canvas ground and the library's own `theme` prop through
`__dcSetProps`, so it is the same code path the real host uses. Flip it on a card carrying the motif,
a card on an inverted ground, and a card with an image slot. Thirty seconds, and it is the only way
to catch the compromise-colour version of this bug — which passes every check by design.

---

## When light is a courtesy variant

Some brands specify one mode. A derived opposite is legitimate work, but it is derived, and saying so
is the honest move: set `theme.light_is_derived` in `project.json` and repeat it at ship time.
Presenting a derived role map as though the brand specified it is a small claim that quietly becomes
someone else's problem.
