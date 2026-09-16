# Avail Trading — Cross-Chain Deposit Infrastructure

Static build of the Figma page
[`Website-Design` → node `74:46`](https://www.figma.com/design/HrZY2cXjkwYMn6OnmEVPuM/Website-Design?node-id=74-46).

```
index.html              the trading page — markup for all 8 sections
prediction-markets.html the prediction-markets page, same 8 sections
css/site.css      everything availproject.org already supplies — DELETE on merge
css/flow.css      clip runner, tab pill, configurator, .container — same name the site uses
css/page.css      the sections both pages share: hero, stats, features, metrics, CTA, FAQ
css/prediction.css  prediction-markets only, every selector scoped .page-position
js/deposits.js    page behaviour: mobile nav, flow tabs, FAQ, scroll observers
assets/           real exports pulled from Figma (no redrawn approximations)
assets/fonts/     Delight Regular + Medium, self-hosted as woff2
assets/flow/      the four deposit-flow clips + poster frames
assets/position/  the three funded-position clips + poster frames
assets/position-cta-gradient.webp   that page's closing-CTA plate
flow/player.html            source the deposit clips are recorded from
flow/player-prediction.html source the funded-position clips are recorded from
flow/build-prediction.py    regenerates the above from player.html
flow/build-hero.py          regenerates flow/hero.html from player-prediction.html
flow/record-smooth.py       deterministic recorder (uniform fps, see below)
flow/stamp-assets.py        re-stamps ?v= on recorded assets from their mtimes
flow/position-bg@3x.png     plate the funded-position clips are shot against
flow/position-config-bg.webp  that page's configurator plate
flow/configurator.html      the Widget Configurator prototype, embedded live
flow/build-configurator.py  regenerates the above from the prototype
flow/config-bg.webp         that panel's gradient plate, from the artboard
flow/record.py              records a player segment to mp4 + poster
```

## Run

```sh
python3 -m http.server 8899   # then open http://127.0.0.1:8899
```

Assets are referenced by relative path, so the folder can be dropped onto any
static host as-is.

## Project conventions

| Item | Value |
|---|---|
| Boilerplate/template page | None — single page. The parent site is the template; derive new pages from `avail-web-kit/template.html`, not from this file. |
| Shared CSS + load order | `css/site.css` → `css/flow.css` → `css/page.css` → `css/prediction.css` (that last one only on the prediction page). **Order is load-bearing** — the split preserved the original single-file order within each bucket, and reordering the links will break specificity-dependent rules. |
| Body class pattern | `page-deposits`, matching the parent's `.page-*` convention (`common.css` already maps `.page-deposits` to a `--hero-base`) |
| Breakpoints | 1200 / 1000 / 640 / 460 (plus a 1201 min-width refinement). See *Breakpoints* below. |
| Cache-busting policy | `?v=N` on every `css/*.css` and `js/deposits.js`, bumped together across **both** pages in the same edit. Never mixed with unversioned links. |
| Dev server | `python3 -m http.server 8899` |
| Deploy target | GitHub Pages, `main` branch, repo root |

A note on the CSS being one file rather than the usual
`variables / base / nav / footer / components` split: this page is destined to
be absorbed into availproject.org, which **already has** files by exactly those
names. Splitting here would produce five files that collide by name with the
parent's, four of which get deleted on merge — so the boundaries are marked
inside the single file instead (`MERGE: DROP` / `MERGE: KEEP`). One file with
clear boundaries is less work to merge than five files with a name clash.

## Fidelity notes

* Every icon, logo, illustration and screenshot is an **exported Figma asset**.
  Composite artwork (hero collage, chain diagram, widget configurator, CTA
  gradient) is positioned with percentage coordinates taken from the Figma
  frame, so it scales without redrawing.
* Type: two families only — **Delight** (headings) self-hosted from the
  licensed OTFs, and **Geist** (everything else) from Google Fonts. The Figma
  file also used Inter for body copy; that was dropped so the page runs the same
  two families as availproject.org.
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

The stylesheet is split so the merge boundary is a file, not a comment:
**`css/site.css` is the delete-on-merge file** — every rule in it is supplied by
`variables.css`, `base.css`, `nav.css`, `footer.css` or `common.css`.
`css/flow.css` maps 1:1 onto the site's file of the same name. `css/page.css`
is what folds into the page's own stylesheet, and `css/prediction.css` is
scoped entirely under `.page-position`. Blocks inside still carry their
`MERGE: DROP` banners, and parent-owned tokens are tagged `/* (parent) */`. `js/deposits.js` moves into the parent's `js/` as-is
— it already matches the one-file-per-page-behaviour convention there, and the
page loads it with `defer`.

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
* Type is Delight for headings and Geist for everything else, matching the
  parent. Inter is gone: the Figma file specified it for body copy, but running
  a third family here and not on the rest of the site was not worth it.

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

## The prediction-markets page

`prediction-markets.html` is the Figma page
[node `142:6298`](https://www.figma.com/design/HrZY2cXjkwYMn6OnmEVPuM/Website-Design?node-id=142-6298).
It is the same eight sections in the same order as `index.html`, sharing
`styles.css` and `js/deposits.js` verbatim — the design changes copy and two
pieces of art, not structure, so the page is built by transforming `index.html`
rather than re-authored. What actually differs:

| Section | Change |
|---|---|
| Hero | "Make predictions easier to fund" + new lede; new export (`assets/hero-position*.webp`) |
| One Flow… | "One Flow to a Funded Position" + new lede; four tabs become **Fund / Predict / Trade** on `assets/position/` |
| Built for Trading Metrics | QR and Embedded UI copy |
| Closing CTA | "Help Every Trader Fund and Trade"; the second button (Talk to Sales) is gone |

Everything else — nav, chains marquee, deposit stats, "Ready to Trade", the four
feature cards, the configurator panel, the FAQs and the footer — is identical to
the trading page, as the design has it.

**Hero loop.** The deposits hero bakes a four-row funding picker, so its cursor
walks rows and finishes on a Continue button. This modal has neither: it has a
live amount field and a row of amount chips. The overlays change with it — the
caret blinks (a white patch over the baked bar) and the tint hops
25 → 50 → 75 → MAX on the same 8s timeline. Coordinates are percentages off the
2055×1779 export, written out above the rules in `styles.css`.

**One illustration behind four panels.** Where the deposits page uses a
separate gradient per panel, this design runs a single halftone landscape —
road, hills, a yellow car — cropped four ways: the hero, the flow panel, the
configurator and the closing CTA. Each crop is exported from its own Figma slot
at the scale of the asset it replaces:

| Slot | Asset | Source node | Size |
|---|---|---|---|
| Hero | `assets/hero-position*.webp` | `142:7029` | 2055×1779 (3×) |
| Flow panel | `flow/position-bg@3x.png` | `142:6521` | 2463×1611 (3×) |†
| Configurator | `flow/position-config-bg.webp` | `142:7052` | 2422×1162 (2×) |*
| Closing CTA | `assets/position-cta-gradient.webp` | `142:7051` | 1800×830 |

\* passed to the iframe as `?bg=`, not set in CSS — see below.  
† Figma clips that group to its 821-wide slot, so this is the only crop that is
not 1:1 with its frame: the player's `#vbg` is `object-fit: cover`, and in the
1000-wide panel it fills the width and crops ~58px off the top and bottom. The
dot pitch is unchanged; the composition just sits tighter. Asking Figma for a
wider window is not an option — it re-clips the group to the same slot, and the
unclipped `rawImages` are the smooth illustration without the halftone.

Written at q72 rather than the hero's q82 — these crops are wall-to-wall
halftone, which lossy webp spends a lot of bits on, and the dots survive the
drop. The CTA crop is also framed differently from the deposits one: the Figma
starts the gradient 30px down a 655-tall block and runs it 625px, against the
deposits plate's `top: 15.1% / height: 92.5%`, so `.page-position` restates
both. The configurator crop is exactly the panel's 1211×581, so `cover` lands
1:1 with no reframing.

Two of those four are not CSS layers. **The configurator's plate is drawn by
the iframe**, not by the page: `configurator.html` creates its own `#vbg` from
`?bg=` (defaulting to `config-bg.webp`), and it paints over whatever the page
put behind it — so the page's `.configurator.is-live` background only shows in
the moment before the iframe loads. The plate is switched on the iframe's own
URL; the CSS rule stays so the two match during that moment rather than
flashing the deposits plate.

**The flow panel's plate is baked into the clips.** It gets there through
`record.py`'s new `BG` env var, which the player reads as `?bg=`; unset, the
player keeps its own `flow-bg@3x.png`. The three clips were shot as:

```sh
SERVE=http://127.0.0.1:8899 PLAYER=player-prediction.html \
OUTDIR="$PWD/assets/position" BG=position-bg@3x.png PANEL_W=1000 PANEL_H=537 \
  INTRO=1 python3 flow/record.py fund
  INTRO=1 python3 flow/record.py predict
  INTRO=0 python3 flow/record.py trade     # continues the card Predict ends on
```

After any re-record, re-stamp the pages that reference the clips:

```sh
python3 flow/stamp-assets.py
```

The browser caches clips by URL, and a hand-maintained `?v=2` goes stale the
moment the next take lands — at which point a stale clip is indistinguishable
from a change that silently did not apply. This derives each stamp from the
file's own mtime, so it cannot disagree with what is on disk. It leaves
`styles.css` and `js/deposits.js` alone: those stamps are a deliberate decision
about breaking cache for visitors, not a build artefact.

`PANEL_W`/`PANEL_H` are the panel this film is shot for — 1000×537 rather than
the deposits page's 821×537, matching `.page-position .flow__panel`. Only the
width moved: the card is sized off `SH`, so it comes out identical and the plate
around it grows.

Frame size costs capture rate, and it is worth watching the number the recorder
prints. A 1195-wide cut (2390×1074) fell to ~24fps and, because frames carry
their own timestamps, that starvation stretched Fund from 8.2s to 10.2s of real
playback. At 1000 (2000×1074) capture holds 39–53fps and the clips come back to
their true length.

They come out heavier than the pastel plate they replaced — 1.9MB for the three
full cuts against 1.4MB — because dense halftone is expensive for x264. Still
comfortably under the deposits page's four clips (2.7MB), with the `-sm` cuts at
0.9MB, but do not add a fourth chapter without re-checking the total.

**The card is sized per screen, not per film.** `player.html` picks one scale
for the whole deposit film so the card never zooms between cuts. This film does
not: its Deposit screen is 661px tall, and one shared scale pinned every other
screen to 0.75 — the Wallet card, 450×304, came out at 41% of the panel's width.
Each screen now fits its own height, capped at 1 so the widget is never drawn
above its design size: Wallet and Placed land at 1, Bet at .84, Deposit at .75.
The resize is not a separate move — `.stage` carries `transition: transform
.44s`, which runs on the same beat as the screen swap's blur and scale, so the
card changes size as part of the cut.

**Two flow sections on one page.** `js/deposits.js` runs its tab loop once per
`.flow` section and takes the segment order from that section's own tabs, so a
three-clip run and a four-clip run drive independently. The mobile `.tabs` grid
flows columns rather than pinning four, so three tabs split the row in thirds.

## Needs product sign-off

* **FAQ answers.** The Figma shows every row collapsed, so no answer copy
  exists in the file. Each answer is currently written from statements already
  on this page (the feature cards and section ledes). Replace with the real
  copy before shipping.
* **Link targets.** Every `href` is `#`.
* **Embedded UI copy on the prediction page.** The Figma gives that card the
  QR card's sentence ("Let users fund their account by scanning a QR code from
  a wallet or exchange") while the QR card carries a longer variant. Built as
  drawn, but it reads as a paste that was never finished — the trading page
  says "The deposit remains inside the trading app experience." Confirm which
  is intended.
* **Prediction-page framing.** The design keeps the trading page's wording in
  several places — the stats section, "Ready to Trade. Not Ready to Deposit.",
  "Get Traders to Their First Trade", "Built for Trading Metrics", "Trading App
  Deposit FAQs" and "Help Every Trader Fund and Trade" — while the hero and the
  flow section speak about predictions and positions. Built as drawn; confirm
  the mixed voice is deliberate.
* **Token-picker scale.** It is the one screen tall enough that fitting it in
  the 821×537 box shrinks the widget noticeably. If that reads too small, the
  fix is a shorter picker in the prototype, not a taller panel.
* **Flow panel width.** Held at 821px on the trading page so the clips stay
  pixel-exact (the prediction page runs 1000, with its clips re-shot to suit). If it
  should grow with the rest of the page on large screens, the clips need
  re-recording at a higher zoom (and will lose some frame rate).
* **Configurator on mobile.** Even cropped it is a dense desktop UI at ~0.48
  scale. If it should read properly on a phone, it wants a purpose-built
  narrow composition rather than a crop.
