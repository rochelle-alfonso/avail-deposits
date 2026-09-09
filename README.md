# Avail Trading — Cross-Chain Deposit Infrastructure

Static build of the Figma page
[`Website-Design` → node `74:46`](https://www.figma.com/design/HrZY2cXjkwYMn6OnmEVPuM/Website-Design?node-id=74-46).

```
index.html        markup for all 8 sections
styles.css        tokens, layout, responsive rules
assets/           real exports pulled from Figma (no redrawn approximations)
assets/fonts/     Delight Regular + Medium, self-hosted as woff2
assets/flow/      the four deposit-flow clips + poster frames
flow/player.html            source the deposit clips are recorded from
flow/configurator.html      the Widget Configurator prototype, embedded live
flow/build-configurator.py  regenerates the above from the prototype
flow/config-bg.webp         that panel's gradient plate, from the artboard
```

## Run

```sh
python3 -m http.server 8899   # then open http://127.0.0.1:8899
```

Assets are referenced by relative path, so the folder can be dropped onto any
static host as-is.

## Fidelity notes

* Every icon, logo, illustration and screenshot is an **exported Figma asset**.
  Composite artwork (hero collage, chain diagram, widget configurator, CTA
  gradient) is positioned with percentage coordinates taken from the Figma
  frame, so it scales without redrawing.
* Type: **Delight** (display) self-hosted from the licensed OTFs; **Geist** and
  **Inter** from Google Fonts — matching the three families in the file.
* Layout constants come from Figma: 1355px content width inside the 1375px
  frame, 72px header/hero gutter, 80px section gutter, and the
  1080 / 1195 / 1211 inner grid widths.
* The **10px `#f0f0ef` frame band** from the Figma frame is reproduced: it runs
  along the top, left and right, and between every section block. There is no
  band below the footer, matching the design.
* **Hero image frames — do not re-add them.** `get_design_context` reports
  `border-12 border-[#ebebeb]` on both hero screenshots, but Figma never paints
  it: scanning the render shows the gradient meeting the screenshot directly
  (`(211,218,242)` → `(255,255,255)` on the trading shot). Taking that property
  literally draws a grey band the design does not have.
* **The deposit modal is not clipped.** `hero-deposit-screen.png` carries its own
  rounded corners and soft shadow in the alpha channel. Adding
  `border-radius` + `overflow:hidden` squares those corners off and cuts the
  shadow, which is what produced the hard edge against the gradient. The trading
  shot is opaque and square, so it *is* clipped at 12px, as in the design.

## Merging into availproject.org

This page uses the parent site's class names and tokens, so the chrome drops
straight into `availproject.org` without a rename pass.

**Names adopted from the parent** (`nav.css`, `footer.css`, `common.css`):

| Chrome | Classes |
|---|---|
| header | `.nav-header` `.nav-logo` `.nav-logo__mark` `.nav-logo__wordmark` `.nav-pill` `.nav-links` `.nav-links__item` `.nav-links__trigger` `.nav-dropdown` `.nav-dropdown__menu` `.nav-dropdown__section` `.nav-dropdown__heading` `.nav-dropdown__link` `.nav-header__cta` |
| mobile | `.nav-menu*` `.mobile-menu*` `body.menu-open` (already ported verbatim) |
| footer | `.site-footer` `__top` `__cta` `__headline` `__subcopy` `__btn` `__copyright` `__nav` `__nav-group` `__nav-group--pages` `__nav-heading` `__nav-list` `__nav-list--pages` `__nav-link` `__logo` `__logo-img` |
| buttons | `.btn` `.btn-primary` `.btn-secondary` (`.btn-light` / `.btn-ghost` are page-local; the parent re-tints `.btn-secondary` by context instead) |

**Tokens** are the parent's names where an equivalent exists: `--black` `--white`
`--grey` `--heading` `--btn-dark` `--btn-dark-text` `--border` `--nav-link`
`--display` `--sans` `--content-inset` (72px) `--gutter` (80px) `--section-frame`
(10px). Note `--content-inset` and `--gutter` are deliberately *not* swapped:
the parent's `--gutter` is 80px and its `--content-inset` is 72px, so using the
old local names would have silently rebound `.wrap` site-wide.

**Sections are namespaced** where a bare name would collide with `common.css`:
`.deposit-hero*`, `.deposit-ready*`, `.deposit-stats*`, `.deposit-stat*`.
Everything else (`.trust`, `.flow`, `.fcard`, `.mcard`, `.configure`, `.cta`,
`.faq`, `.container`, `.frame`, `.section__title`) is already unique.

**Delete on merge** — these are duplicated here only so the folder stands alone:

* `.btn` / `.btn-primary` / `.btn-secondary` — `common.css` supplies them
* every `.nav-*`, `.nav-dropdown*`, `.mobile-menu*` rule and `body.menu-open` —
  `nav.css` supplies them, including the `.nav-header__cta` /
  `.mobile-menu__cta` overrides
* the whole `.site-footer*` block — `footer.css` supplies it

**Deliberate deltas left in place**, because the parent's values are worse here:

* `.nav-header` and `.site-footer__top` are capped at `--page`, not the parent's
  `1440px`. `--page` is `clamp(1355px, 100vw - 20px, 1760px)` and every inner
  width in this page is a fraction of it, so clamping to 1440 would rescale the
  whole composition. **This is the one open decision before merge** — the page
  will be wider than every other page on the site.
* `.site-footer__top` keeps `padding-inline: var(--content-inset)` (72px) so the
  footer aligns with the header. The parent uses 48px, which lines up with
  nothing on its own pages.
* The `.frame` wrapper reproduces the 10px band with padding rather than the
  parent's `.page-shell` borders + `.section-gap` divs. Same result; renaming it
  to `.page-shell` would inherit that rule's `max-width: 1440px`.
* Inter stays on body copy (`.deposit-stats__lede`, `.deposit-ready__body`,
  `.fcard__text`, `.faq__q`) — it is one of the three families in the Figma
  file. All *chrome* is Geist, matching the live site.

## Breakpoints

`--page` is the content width. Every inner max-width is written as a fraction
of it (`calc(var(--page) * 0.79705)` etc.), so above the design width the whole
composition scales instead of just gaining empty gutters.

| Width | `--page` | Behaviour |
|---|---|---|
| ≥1780 | 1760px (capped) | design at 1.30×, centred |
| 1375–1779 | `100vw − 20px` | grows fluidly with the viewport |
| 1201–1374 | 1355px | Figma layout 1:1 |
| 1000–1200 | — | tighter gutters, metrics grid 4→2 up |
| 640–999 | — | hamburger nav, hero stacks, feature cards 1-up, stats 2-up |
| <640 | — | single column, scrollable tab strip, stats 1-up |

Display type scales with the page (capped at ~1.15×); body copy stays fixed.
Verified with no horizontal overflow at 2560 / 1920 / 1440 / 1200 / 834 / 500 / 390.

## Interactive

* Mobile nav toggle
* Flow tabs — auto-advance through the four segments on a continuous loop
  (~33s a cycle), then wrap back to the start. Clicking or arrow-keying a tab
  jumps to it and the loop carries on from there.
  * The hand-off starts **0.55s before** a clip ends, so the outgoing and
    incoming clips overlap and cross-dissolve rather than cutting. Every clip
    shares the same gradient plate, so only the card dissolves — the background
    never flickers.
  * A single pill slides between tabs (`.tabs__pill`, added by script) instead
    of the fill jumping. Without JS the active tab keeps its own background.
  * The next clip is preloaded while the current one plays so the hand-off
    can't stall; the loop pauses while the section is off screen, and
    `prefers-reduced-motion` holds each poster and leaves the tabs manual.
* FAQ accordion

## The deposit-flow clips

`flow/player.html` is a build of `nexus-deposit-prototype-fancy.html` with the
prototype's page chrome stripped and a `?seg=` runner added. It drives the
prototype's own cursor through one continuous happy path; the four clips are cut
from that single take, so each ends where the next begins.

| Tab | Segment | Screens | Length |
|---|---|---|---|
| Funding Source | `funding` | funding method → deposit (empty) → typing / routing → resolved | 11.1s |
| Unified Balance | `balance` | resolved → **Edit** tapped → choose tokens → resolved | 8.8s |
| Intent Steps | `steps` | in-flight, the four intent steps completing | 5.6s |
| Funded | `funded` | deposit complete, count-up + confetti | 5.2s |

**Plate and strokes.** The surround around the UI (`.device`) is drawn at 65%
opacity (`?plate=`) so the gradient reads through it instead of the card sitting
on an opaque slab. That opacity covers the whole plate layer — fill, hairline
ring and drop shadow — the way reducing a layer's opacity would in Figma. The
hairline strokes on the UI surfaces are separately at 50% (`?stroke=`, applied
by overriding the prototype's `--border`). Fills stay solid, so nothing loses
legibility.

**Sizing.** The gradient box keeps the Figma panel size (821×537). The widget
inside is fitted per screen: the design's own card scale (393/450) wherever it
fits, easing down only for the taller screens — the token picker is 812px, so it
rides at ~0.60. The device already animates its height, so this reads as a
gentle zoom rather than a jump.

**Resolution.** The player is laid out at 2× (`?zoom=2`) so the browser renders
text and vectors at capture size, while the capture itself stays at dpr 1 —
which is what keeps the screencast fast enough for ~26fps. Clips ship at their
native 1642×1074, and the panel is held at the Figma width (821px) rather than
scaling with `--page`, so on a retina display the video lands at **exactly 2×**
with no upscaling at any breakpoint. Phones get a 1280px rendition. Only the
funding clip loads up front; the rest load the first time their tab is opened,
and `prefers-reduced-motion` holds the poster frame instead of playing.

Three traps, if you touch the recorder:

* `Emulation.setDeviceMetricsOverride` does **not** raise the screencast's
  capture resolution — it silently pins frames to CSS-pixel size. That is why
  the first cut looked soft: frames were 821px and ffmpeg was upscaling them.
* Raising the real DPR (`--force-device-scale-factor`) does work, but the
  compositor throttles hard — 3× drops capture to ~14fps. Laying the page out
  larger at dpr 1 gets the pixels without losing the frames.
* CDP virtual time is not a way out: `setTimeout` follows it, but CSS
  transitions jump straight to their end state, so the cursor teleports.

**To re-record** after editing the prototype, `flow/record.py` drives it:

```sh
python3 -m http.server 8899          # in one shell, from the repo root
python3 flow/record.py steps         # funding | balance | steps | funded
```

It needs `websockets` and `pillow` (Pillow only because this Homebrew ffmpeg has
no libwebp encoder for the poster).

Frames come off the screencast as **jpeg**, not png. Per-frame png encoding is
the bottleneck on the heavier segments — the confetti in `funded` drags png
capture down to ~17fps, where jpeg holds 30+ and ffmpeg is no longer duplicating
frames to reach the output rate. h264 at crf 29 sits well below jpeg 95, so the
extra generation costs nothing visible. The poster is taken separately as a real
png via `Page.captureScreenshot` before the run starts. It writes `<seg>.mp4`, `<seg>-sm.mp4` and
`<seg>.webp` into `assets/flow/`, and kills the debug port itself — but if a
Chrome is already holding 9222, kill it first: attaching to a stale one silently
gives you the old window's DPR.

It runs **headless** by default, and must. A headful window is clamped to the
desktop, so a 1642x1074 viewport does not fit a 1512x982 logical display; Chrome
then scales the emulated viewport down and the screencast captures the scaled
surface, leaving the plate at ~80% inside a correctly-sized frame. `HEADLESS=0`
if you want to watch it run, but do not ship what that produces.

## The Widget Configurator panel

"Configure Your Deposit Flow" runs `avail-configurator-prototype.html` **live in
an iframe** rather than as a video or a screenshot. The artboard's own gradient
plate is the background, unchanged at 1211×581, and only the UI is swapped.

The artboard pins the window at 107,44 at 997 wide and lets it run off the
bottom edge. Here the whole window is wanted instead, with the gradient left
alone, so two things happen:

* it is **scaled** so the prototype's full 764px height clears the top margin —
  `(581 − 44×2) / 764 = 0.645`, giving a 761px-wide window;
* the **frame is then stretched** to `(581 − 44) / 0.645 = 832px` so its bottom
  edge meets the panel's, leaving no gap underneath. That extra height is real
  viewport for the app, not a crop — the sidebar simply shows more before it
  starts scrolling internally.

The window ends up 761px wide against the artboard's 997, which is the cost of
fitting it inside a panel that stays 581 tall. Widening it back means either a
taller panel or a shorter virtual screen.

It is live rather than recorded because the walkthrough is **~53 seconds** long —
one pass through the seven active chapters. At panel resolution that encodes to roughly
12 MB, against ~500 KB for the prototype plus its gradient plate, and the live
version stays sharp at any zoom. To bake it to video instead, the recorder in
this repo works on `flow/configurator.html` the same way it does on
`flow/player.html`.

* Loads only when the section nears the viewport, and pauses whenever it scrolls
  away (`play()` / `pause()` called across the same-origin frame).
* `pointer-events: none` — it is a showcase, and clicking inside would pause the
  prototype's own demo and leave it stranded.
* Scaled from its 1211px artboard width to whatever the panel is. On phones the
  proportional scale lands at 0.31 and is unreadable, so the box goes to 4:3 and
  the frame scales to fill it (≈0.48), cropping from the right and keeping the
  configuration column legible.
* `prefers-reduced-motion` loads it but leaves it on the first chapter.

`flow/configurator.html` is **generated**, not hand-edited — re-run
`python3 flow/build-configurator.py` after changing the prototype. It applies
four patches, and fails loudly if the prototype has moved out from under them.

**Opens on the first real action.** Chapter 0 ("Empty configuration") only
drifts the cursor around for ~3.9s, so the loop starts and wraps at chapter 1,
"Pick a preset" — the walkthrough now opens on the tap that picks a preset. The
chapter is left in `CH` rather than deleted because `snapshot()` keys its state
off the original indices. One pass is ~53s.

**One token, one chain.** The preview's token pill stacked up to two token
icons (`toks.slice(0,2)`); the design shows a single token badged with the
destination chain, so the build renders `toks[0]` plus a `.tokchain` badge.
Before a chain is chosen the badge is simply omitted.

**Cursor maths (patched at build time).** The prototype positions its demo
cursor with `getBoundingClientRect` — painted pixels — but applies the result as
a `translate` *inside* `.frame`, which this build scales to 997/1180 = 0.845.
At 100% (how the prototype normally runs) the two agree, so the bug is invisible
there; scaled, every click landed ~18% short and up-left of its target. The
build divides the ratio back out in `moveTo` and in the hue-drag loop, via a
`__k()` helper. **The same bug exists in the deposit prototype** and is patched
the same way in `player.html`. Leave the original prototypes alone — the
correction belongs in the player builds, since it only applies when scaled.

## Needs product sign-off

* **FAQ answers.** The Figma shows every row collapsed, so no answer copy
  exists in the file. Each answer is currently written from statements already
  on this page (the feature cards and section ledes). Replace with the real
  copy before shipping.
* **Link targets.** Every `href` is `#`.
* **Token-picker scale.** It is the one screen tall enough that fitting it in
  the 821×537 box shrinks the widget noticeably. If that reads too small, the
  fix is a shorter picker in the prototype, not a taller panel.
* **Flow panel width.** Held at 821px so the clips stay pixel-exact. If it
  should grow with the rest of the page on large screens, the clips need
  re-recording at a higher zoom (and will lose some frame rate).
* **Configurator on mobile.** Even cropped it is a dense desktop UI at ~0.48
  scale. If it should read properly on a phone, it wants a purpose-built
  narrow composition rather than a crop.
