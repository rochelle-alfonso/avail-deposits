#!/usr/bin/env python3
"""Generate flow/hero.html — the hero's deposit widget as live DOM.

Why this exists
---------------
The hero used to be one flat Figma export: the app, the gradient and the
Deposit modal all baked into a single PNG. Node 152:7057 in the Figma file is
literally named "2 · Deposit — route resolved@2x 1" — a still that was rendered
from the deposit prototype and pasted back in. That makes every content change
(the destination token, the funding mix, the amount) a Figma round trip, and
makes an animated hero impossible.

So the modal comes back out of the picture:

  flow/hero-plate@3x.png   the same Figma frame exported with 152:7057 hidden
  flow/hero.html           that plate + the modal rebuilt as real elements

The modal is not re-styled by hand. Its markup and CSS are the prototype's, so
what renders here is what the film renders. Same trick as build-prediction.py:
this file is the editable source, the .html it writes is a build artefact.

    python3 flow/build-hero.py
"""
import base64, json, os, re, sys

ROOT   = os.path.dirname(os.path.abspath(__file__))
SRC    = os.path.join(ROOT, 'player-prediction.html')
DST    = os.path.join(ROOT, 'hero.html')
ASSETS = os.path.expanduser('~/Documents/fastbridge/assets')

src = open(SRC, encoding='utf-8').read()

# ---- lift the prototype's stylesheet and inlined marks ----------------------
def prototype_styles(s):
    """The prototype splits its CSS across three <style> blocks: the base sheet
    from player.html, the prediction-screen rules that build-prediction.py adds
    (.dep-card, .dep-row, .pcts, .arow, .pw), and the recorder's #vstage
    override. The widget needs the first two; the third is for recording only
    and would drag the stage geometry in with it."""
    blocks = re.findall(r'<style[^>]*>(.*?)</style>', s, re.S)
    if len(blocks) < 2:
        sys.exit('expected at least two prototype style blocks, found %d' % len(blocks))
    if '.dep-card' not in blocks[1]:
        sys.exit('block 1 is not the prediction-screen CSS — check build-prediction.py')
    return blocks[0] + '\n' + blocks[1]

def brace_block(s, opener):
    """Take `const IMG = {` ... through its matching close brace. The values are
    base64, which never contains a brace, but count anyway rather than trust it."""
    i = s.find(opener)
    if i < 0:
        sys.exit(f'could not find {opener!r}')
    i = s.index('{', i)
    depth, j = 0, i
    while j < len(s):
        if s[j] == '{': depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return s[i:j + 1]
        j += 1
    sys.exit(f'unbalanced braces after {opener!r}')

STYLES = prototype_styles(src)
IMG_LITERAL = brace_block(src, 'const IMG =')
SVG_LITERAL = brace_block(src, 'const SVG =')

# ---- the one mark the prototype has never needed ---------------------------
def datauri(path, mime):
    with open(path, 'rb') as fh:
        return f'data:{mime};base64,' + base64.b64encode(fh.read()).decode()

# The prototype only ever needed Ethereum, Optimism, MegaETH and Citrea. The
# hero's funding mixes also name Base and Arbitrum, so those two marks are
# inlined here rather than silently falling back to the Ethereum diamond.
def grab_mark(sheet, key):
    """Pull an inlined token mark out of player.html by key."""
    m = re.search(r'\b%s:"(data:image/[a-z+]+;base64,[^"]+)"' % key, sheet)
    if not m:
        sys.exit(f'player.html has no inlined {key!r} mark')
    return m.group(1)

# build-prediction.py only forwards the marks its own film uses (usdc, eth,
# optimism, citrea, megaeth, ctusd), so the hero's funding mixes have to bring
# the rest. usdt/arbitrum/base come from player.html rather than the raw asset
# folder: those are the same drawn-for-the-design-system marks the prototype
# already renders, so they sit consistently beside usdc. Monad is the one that
# exists nowhere upstream.
# The plate ships at 3x for the interactive page and stills. During a record
# the browser was rescaling 2055px down to the 1370px frame on every single
# frame, which held capture to ~19fps; a plate already at the record size
# removes that work. Generated here so the two can never drift.
from PIL import Image as _Image
_plate3x = os.path.join(ROOT, 'hero-plate@3x.png')
_plate2x = os.path.join(ROOT, 'hero-plate@2x.png')
if os.path.exists(_plate3x):
    _im = _Image.open(_plate3x)
    _w = 685 * 2
    _im.resize((_w, round(_im.height * _w / _im.width)), _Image.LANCZOS).save(
        _plate2x, 'PNG', optimize=True)

player = open(os.path.join(ROOT, 'player.html'), encoding='utf-8').read()
EXTRA_MARKS = {
    'usdt':     grab_mark(player, 'usdt'),
    'arbitrum': grab_mark(player, 'arbitrum'),
    'base':     datauri(os.path.join(ROOT, 'base-mark.png'), 'image/png'),  # official Square
    'monad':    datauri(os.path.join(ASSETS, 'monad-icon.png'), 'image/png'),
}
# Solana has no mark anywhere in the asset set, so it is drawn rather than
# inlined. The gradient lives in one <defs> on the page and both sizes point at
# it, which avoids duplicate ids from rendering the glyph twice.

# ---- geometry, measured off the Figma frame --------------------------------
# 142:7029 is 685x593; 152:7057 sat at 66,161 and was 336x381. The prototype's
# card is 450 wide, so the hero renders it at 336/450.
STAGE_W, STAGE_H = 685, 593
MODAL_X, MODAL_Y = 66, 161
MODAL_W          = 336
CARD_W           = 450
SCALE            = MODAL_W / CARD_W
# The widget is top-anchored in the Figma, which was fine for a still: the baked
# modal was 381 tall and cleared the stage bottom by 51. Live, its height tracks
# the funding mix - 348 at two rows, 430 at four - and the $40 mix ran to within
# 1.9 of the bottom edge. So it is centred on the vertical middle the signed-off
# $20 layout already had (161 + 348/2), which leaves that case exactly where it
# was drawn and lifts the taller ones instead of letting them overflow.
MODAL_CY         = 335

# ---- the three funding scenarios the hero cycles ---------------------------
# Editable here or, live, in the panel on the page.
SCENARIOS = [
    {"id": "s20", "label": "$20 · 2 stablecoins", "amount": "20", "usd": "20.00",
     "rows": [
        {"sym": "USDC", "chain": "on Ethereum", "amt": "12.40 USDC", "usd": "$12.40", "coin": "usdc", "badge": "eth"},
        {"sym": "USDT", "chain": "on Arbitrum", "amt": "7.60 USDT",  "usd": "$7.60",  "coin": "usdt", "badge": "arb"},
     ]},
    {"id": "s30", "label": "$30 · 2 stable + 1 native", "amount": "30", "usd": "30.00",
     "rows": [
        {"sym": "USDC", "chain": "on Ethereum", "amt": "12.40 USDC",  "usd": "$12.40", "coin": "usdc", "badge": "eth"},
        {"sym": "USDT", "chain": "on Arbitrum", "amt": "7.60 USDT",   "usd": "$7.60",  "coin": "usdt", "badge": "arb"},
        {"sym": "ETH",  "chain": "on Optimism", "amt": "0.0040 ETH",  "usd": "$10.00", "coin": "eth",  "badge": "optimism"},
     ]},
    # 2 stablecoins + one native + one longtail. The native was SOL, dropped
    # because Solana is not supported — ETH on Optimism keeps the shape.
    {"id": "s40", "label": "$40 · 2 stable + native + longtail", "amount": "40", "usd": "40.00",
     "rows": [
        {"sym": "USDC", "chain": "on Ethereum", "amt": "12.40 USDC", "usd": "$12.40", "coin": "usdc",   "badge": "eth"},
        {"sym": "USDT", "chain": "on Arbitrum", "amt": "7.60 USDT",  "usd": "$7.60",  "coin": "usdt",   "badge": "arb"},
        {"sym": "ETH",  "chain": "on Optimism", "amt": "0.0048 ETH", "usd": "$12.00", "coin": "eth",   "badge": "optimism"},
        {"sym": "MON",  "chain": "on Monad",    "amt": "241.9 MON",  "usd": "$8.00",  "coin": "monad", "badge": "monad"},
     ]},
]

# Which scenarios the film actually plays, and in order. The $30 mix stays in
# SCENARIOS — it is still a preset in the panel, and the original feedback had
# it as "(optional)" — but it is out of the film, which now runs 20 -> 40 so the
# jump from two stablecoins to a four-asset mix lands in one step.
FILM = ["s20", "s40"]

DEST = {"sym": "USDC", "chain": "Base", "cap": "$1,240.55"}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hero — live deposit widget</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
__STYLES__
</style>
<style id="hero-override">
/* ---------------------------------------------------------------------------
   The page around the stage. Everything inside .hero-stage is in Figma units
   (685x593) and scaled as a block, so positions here are the frame's own
   numbers and can be read straight off the design.
--------------------------------------------------------------------------- */
* { box-sizing: border-box; }
/* The prototype sheet above is a whole page's CSS, not a component's: it sets
   html,body{height:100%} and body{display:flex;flex-direction:column;
   align-items:center;justify-content:center} to centre the film in the
   viewport. Inherited here that stacks the panel under the stage and centres
   the pair out of view, so every page-level property it sets is restated —
   same specificity, later in the cascade. */
html, body { height: auto; }
body {
  --hz: 1.1;
  margin: 0; padding: 28px;
  background: #F4F4F3; color: #161615;
  font-family: Geist, system-ui, -apple-system, sans-serif;
  display: flex; flex-direction: row;
  align-items: flex-start; justify-content: flex-start;
  gap: 28px; min-height: 100vh;
}
.hero-wrap {
  flex: 0 0 auto;
  /* transform:scale() paints larger but reserves nothing, so the wrapper
     carries the scaled box or the panel slides under the stage */
  width:  calc(__STAGE_W__px * var(--hz));
  height: calc(__STAGE_H__px * var(--hz));
}
.hero-stage {
  position: relative;
  width: __STAGE_W__px; height: __STAGE_H__px;
  transform: scale(var(--hz)); transform-origin: top left;
  border-radius: 10px; overflow: hidden;
  box-shadow: 0 24px 70px -30px rgba(20,20,20,.45);
}
/* Two pieces of Polymarket branding are baked into the plate. Both sit on flat
   fills, so they are masked in place rather than needing the artwork re-cut:
   the chart footer's "Polymarket" credit (x 69.29%-75.77%, on white) is simply
   covered, and the search placeholder (x 29.83%-41.41%, on the #F6F7F9 pill) is
   covered and re-set. Coordinates measured off the 2055x1779 plate. */
.plate-mask { position: absolute; pointer-events: none; }
.plate-mask--credit {
  left: 68.1%; width: 8.1%; top: 56.0%; height: 2.1%;
  background: #fff;
}
.plate-mask--search {
  left: 29.5%; width: 12.6%; top: 13.6%; height: 1.8%;
  background: #F6F7F9;
  display: flex; align-items: center;
  font-family: var(--sans); font-size: 7.4px; line-height: 1;
  letter-spacing: -.005em; color: #C5C6C9; white-space: nowrap;
}

/* No layer promotion here. It bought under 2fps, and pinning the plate's raster
   scale made it resample against the stage transform — every frame came out
   fractionally different, which reads as the halftone shimmering. */
.hero-plate { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }

/* ---- record mode (?rec=1) -------------------------------------------------
   record.py lays the page out at sw x sh and screencasts it, so everything
   except the stage goes away and the stage fills the frame exactly. #vstage
   exists because the recorder reaches for it by id to clear the intro state;
   the hero has no rise to play (the plate IS the background), so arming it is
   a no-op and the element is just the handle. */
body.rec { display: block; padding: 0; background: #fff; min-height: 0; }
body.rec .panel { display: none; }
body.rec .hero-wrap { width: auto; height: auto; }
body.rec #vstage { position: relative; overflow: hidden; }
body.rec .hero-stage { transform-origin: top left; border-radius: 0; box-shadow: none; }

/* The card resizes as rows come and go, so it slides rather than jumps. The
   slide is a transform, never `top`: animating `top` repaints the card's large
   soft shadow against the halftone plate on every frame, which is the single
   most expensive thing on this page. Transform stays on the compositor. */
/* The card hugs its content and is anchored by its TOP, so adding rows extends
   it downward and nothing already on screen moves. That is what keeps the film
   smooth: the earlier version centred the card, so every row changed its height
   AND shifted it, and a 420ms shift only ever caught ~6 frames on this plate.
   Nothing moves now, so nothing transitions. */
.hero-modal { }
/* No @keyframes for the entrance — it is tweened from JS instead. record-smooth
   drives the page on CDP virtual time, which advances setTimeout and rAF but
   NOT the compositor's animation clock, so a CSS animation snaps to its end
   state and every fade lands in a single frame. A rAF tween advances with the
   virtual clock and therefore renders properly at every step. */
.hero-caret-blink { animation: heroCaret 1.06s steps(1,end) infinite; }
@keyframes heroCaret { 0%,50% { opacity: 1 } 50.01%,100% { opacity: 0 } }

/* the widget, sitting exactly where the baked one used to */
.hero-modal {
  position: absolute;
  left: __MODAL_X__px; top: __MODAL_Y__px;   /* start; JS re-centres on MODAL_CY */
  width: __CARD_W__px;
  transform: scale(__SCALE__); transform-origin: top left;
}
/* The plate around the UI, at the same 0.65 the deposit film is shot at. The
   opacity covers the whole plate layer — fill, hairline ring and drop shadow —
   the way reducing a layer's opacity would in Figma, so the gradient reads
   through the band around the cards. The cards inside keep their solid fills
   and their own crisp hairlines. Radius is the prototype's 30px; it reads as
   ~22 once the hero scales the card down. */
.hero-modal .device {
  background: rgba(249,249,248,.65);
  border-radius: 30px;
  /* The translucent ring OUTSIDE the card. Measured off the original export
     rather than guessed: comparing the baked render against the modal-free
     plate, the gradient is washed for 12 units beyond the card edge at a flat
     ~0.74 alpha — flat, so a hard ring rather than a soft glow. 16px here
     because the hero scales the card to 0.7467, and 16 x 0.7467 = 12.
     It goes first in the list so it sits under the drop shadows. */
  /* The drop shadow runs at full strength, unlike the plate fill. Tying it to
     the 0.65 plate opacity (as the prototype's recorder does) left the card
     sitting flat on the gradient — the trading page's hero has a clearly
     readable shadow and this now matches it. The translucent ring stays first
     in the list so it sits under the shadows. */
  box-shadow: 0 0 0 16px rgba(255,255,255,.74),
              0 40px 80px -30px rgba(20,20,20,.35),
              0 8px 30px -12px rgba(20,20,20,.22),
              0 0 0 1px rgba(20,20,20,.04);
  padding: 0;
}
.hero-modal .screen { position: relative; opacity: 1; visibility: visible;
  transform: none; filter: none; padding: 16px; gap: 16px; display: flex;
  flex-direction: column; }

/* The prototype sweeps a sheen across .cta.primary on a 3.4s CSS loop. It has
   no place here twice over: the hero is a still-ish product shot, and the film
   is recorded on a driven clock that CSS animations do not follow — so it would
   freeze at whatever phase it happened to be in and read as a stray diagonal
   band rather than a sweep. */
.hero-modal .cta.primary::after { display: none; }

/* ---- the control panel --------------------------------------------------- */
.panel {
  flex: 1 1 340px; max-width: 460px; position: sticky; top: 28px;
  background: #fff; border: 1px solid #E8E8E7; border-radius: 12px; padding: 18px 18px 22px;
  font-size: 13px; line-height: 1.5;
}
.panel h1 { margin: 0 0 2px; font-size: 15px; font-weight: 600; }
.panel .sub { margin: 0 0 16px; color: #6B6B6A; font-size: 12px; }
.panel h2 { margin: 18px 0 8px; font-size: 11px; font-weight: 600; letter-spacing: .07em;
  text-transform: uppercase; color: #8A8A88; }
.row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.row label { flex: 0 0 108px; color: #6B6B6A; }
.panel input, .panel select {
  flex: 1 1 auto; min-width: 0; height: 32px; padding: 0 9px;
  border: 1px solid #E0E0DF; border-radius: 6px; background: #fff;
  font-family: inherit; font-size: 13px; color: #161615;
}
.panel input:focus, .panel select:focus { outline: 2px solid #2D69EB33; border-color: #2D69EB; }
.segs { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.seg { padding: 7px 11px; border: 1px solid #E0E0DF; border-radius: 6px; background: #fff;
  cursor: pointer; font: inherit; font-size: 12px; }
.seg[aria-pressed="true"] { background: #161615; color: #fff; border-color: #161615; }
.assets { display: flex; flex-direction: column; gap: 6px; }
.asset { display: grid; grid-template-columns: 68px 1fr 92px 62px 26px; gap: 5px; align-items: center; }
.asset input, .asset select { height: 29px; font-size: 12px; padding: 0 7px; }
.asset .del { height: 29px; border: 1px solid #E0E0DF; border-radius: 6px; background: #fff;
  cursor: pointer; color: #B4342B; font-size: 14px; line-height: 1; }
.addrow { margin-top: 8px; }
.note { margin-top: 16px; padding-top: 14px; border-top: 1px solid #EFEFEE;
  color: #6B6B6A; font-size: 12px; }
.note code { background: #F4F4F3; padding: 1px 4px; border-radius: 3px; font-size: 11px; }
.zoomrow { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.zoomrow input[type=range] { flex: 1; }
</style>
</head>
<body>

<svg width="0" height="0" aria-hidden="true" style="position:absolute">
  <defs><linearGradient id="solg" x1="0" y1="1" x2="1" y2="0">
    <stop offset="0" stop-color="#9945FF"/><stop offset="1" stop-color="#14F195"/>
  </linearGradient></defs>
</svg>

<div class="hero-wrap">
 <div id="vstage">
  <div class="hero-stage" id="stage">
    <img class="hero-plate" src="hero-plate@3x.png" alt="">
    <span class="plate-mask plate-mask--credit" aria-hidden="true"></span>
    <span class="plate-mask plate-mask--search" aria-hidden="true">Search markets&hellip;</span>
    <div class="hero-modal">
      <div class="device">
        <section class="screen" id="s-deposit">
          <div class="topbar"><div class="title">Deposit</div>
            <div class="icon-btns"><div class="iconbtn">@refresh@</div><div class="iconbtn">@close@</div></div></div>

          <div class="card soft">
            <div class="dep-card">
              <div class="dep-head">
                <div class="dep-label">Deposit</div>
                <div class="dep-cap">You can deposit up to <b id="h-cap">__CAP__</b></div>
              </div>
              <div class="dep-row">
                <div class="dep-hero"><span class="n tnum" id="h-amt">__AMT__</span><span class="dep-caret"></span></div>
                <div class="dep-pill" id="h-pill"></div>
              </div>
              <div class="dep-approx"><span class="tnum" id="h-usd">&asymp; $__USD__</span>@swap@</div>
              <div class="pcts">
                <div class="pct-chip">25%</div><div class="pct-chip">50%</div>
                <div class="pct-chip">75%</div><div class="pct-chip">MAX</div>
              </div>
            </div>
          </div>

          <div class="card soft">
            <div class="pw">
              <div class="pw-top">
                <div class="pw-l">
                  <div class="pw-tr"><span class="pw-t">Pay with</span><span class="pw-count" id="h-count">2 assets</span></div>
                  <div class="pw-sub" id="h-sub">Auto-selected to cover your $20 deposit</div>
                </div>
                <div class="pw-edit">Edit Tokens</div>
              </div>
              <div class="pw-rows" id="h-rows"></div>
            </div>
          </div>

          <div class="pfoot"><button class="cta disabled" id="h-cta">Enter an Amount</button></div>
        </section>
      </div>
    </div>
  </div>
 </div>
</div>

<div class="panel">
  <h1>Hero deposit widget</h1>
  <p class="sub">Live DOM over the Figma plate. Everything below writes straight into the
     widget — no Figma round trip.</p>

  <h2>Scenario</h2>
  <div class="segs" id="p-scenarios"></div>

  <h2>Destination</h2>
  <div class="row"><label>Token</label><input id="p-sym" value="__DEST_SYM__"></div>
  <div class="row"><label>Chain</label><input id="p-chain" value="__DEST_CHAIN__"></div>
  <div class="row"><label>Amount</label><input id="p-amt" value="__AMT__"></div>
  <div class="row"><label>USD</label><input id="p-usd" value="__USD__"></div>
  <div class="row"><label>Deposit cap</label><input id="p-cap" value="__CAP__"></div>

  <h2>Pay with</h2>
  <div class="assets" id="p-assets"></div>
  <button class="seg addrow" id="p-add" type="button">+ add asset</button>

  <div class="zoomrow"><label style="color:#6B6B6A">Zoom</label>
    <input type="range" id="p-zoom" min="0.6" max="2.2" step="0.05" value="1.1">
    <span id="p-zoomv" style="color:#6B6B6A">1.10x</span></div>

  <p class="note">Markup and CSS are the deposit prototype's, so this matches what the
     film renders. Geometry is the Figma frame's own: stage <code>__STAGE_W__x__STAGE_H__</code>,
     widget at <code>__MODAL_X__,__MODAL_Y__</code> scaled <code>__SCALE_PCT__%</code>.
     Regenerate with <code>python3 flow/build-hero.py</code>.</p>
</div>

<script>
const SVG = __SVG__;
const IMG = __IMG__;
Object.assign(IMG, __EXTRA_MARKS__);

// Solana ships as vector because there is no bitmap for it anywhere in the
// asset set. Both instances point at the one <defs> gradient above.
const DRAWN = {
  solana: sz => `<svg width="${sz}" height="${sz}" viewBox="0 0 400 400" style="display:block;border-radius:999px">
    <rect width="400" height="400" rx="200" fill="#131313"/>
    <g transform="translate(76 128) scale(0.62)">
      <path d="M64.6 237.9c2.4-2.4 5.7-3.8 9.2-3.8h317.4c5.8 0 8.7 7 4.6 11.1l-62.7 62.7c-2.4 2.4-5.7 3.8-9.2 3.8H6.5c-5.8 0-8.7-7-4.6-11.1l62.7-62.7z" fill="url(#solg)"/>
      <path d="M64.6 3.8C67.1 1.4 70.4 0 73.8 0h317.4c5.8 0 8.7 7 4.6 11.1l-62.7 62.7c-2.4 2.4-5.7 3.8-9.2 3.8H6.5c-5.8 0-8.7-7-4.6-11.1L64.6 3.8z" fill="url(#solg)"/>
      <path d="M333.1 120.1c-2.4-2.4-5.7-3.8-9.2-3.8H6.5c-5.8 0-8.7 7-4.6 11.1l62.7 62.7c2.4 2.4 5.7 3.8 9.2 3.8h317.4c5.8 0 8.7-7 4.6-11.1l-62.7-62.7z" fill="url(#solg)"/>
    </g></svg>`,
};
const mark = (k, sz) => DRAWN[k] ? DRAWN[k](sz)
  : IMG[k] ? `<img src="${IMG[k]}" width="${sz}" height="${sz}" style="display:block;border-radius:999px" alt="">`
  : '';
// badge key -> mark key; megaeth is the one that ships as an inline SVG
const BADGE = { eth: 'eth', arb: 'arbitrum', optimism: 'optimism', base: 'base',
                usdc: 'usdc', usdt: 'usdt', solana: 'solana', monad: 'monad' };
const badgeOf = (k, sz) => k === 'megaeth' ? SVG.megaeth : mark(BADGE[k] || k, sz);
const av34 = (coin, badge) => `<div class="av34">${mark(coin,34)}<span class="bd">${badge}</span></div>`;

// the static icons the markup asks for by name
const MAP = { close: SVG.close, refresh: SVG.refresh, swap: SVG.swap };
document.querySelectorAll('.screen').forEach(scope => {
  scope.innerHTML = scope.innerHTML.replace(/@(\\w+)@/g, (m, k) => MAP[k] ?? m);
});

const SCENARIOS = __SCENARIOS__;
let state = {
  sym: "__DEST_SYM__", chain: "__DEST_CHAIN__",
  amount: "__AMT__", usd: "__USD__", cap: "__CAP__",
  rows: JSON.parse(JSON.stringify(SCENARIOS[0].rows))
};

const MODAL_CY = __MODAL_CY__, MODAL_SCALE = __SCALE__, MODAL_Y0 = __MODAL_Y__;
// Keep the card's middle pinned so extra rows grow into the space above it
// rather than off the bottom of the stage.
//
// Called synchronously, not off requestAnimationFrame: rAF is throttled in a
// background tab, which is exactly where this page gets loaded when the hero is
// recorded, and the centring would silently never apply. Reading offsetHeight
// forces the layout we need anyway. The observer covers anything that reflows
// later — a webfont landing, a row edited from the panel.
// The card's top, chosen so the TALLEST layout still clears the stage bottom by
// BOTTOM_GAP. Fixed for the whole film: shorter mixes simply end higher up.
const BOTTOM_GAP = 43, STAGE_H = __STAGE_H__;
let anchorY = null;

function setAnchor(tallestStageH) {
  const el = document.querySelector('.hero-modal');
  anchorY = STAGE_H - tallestStageH - BOTTOM_GAP;
  el.style.transform =
    `translateY(${(anchorY - MODAL_Y0).toFixed(1)}px) scale(${MODAL_SCALE})`;
}

// Measure the tallest mix once, off-camera, then anchor to it.
function anchorToTallest(ids) {
  const dev = document.querySelector('.hero-modal .device');
  const widest = ids.map(id => SCENARIOS.find(x => x.id === id))
                    .reduce((a, b) => (b.rows.length > a.rows.length ? b : a));
  const keep = state.rows;
  state.rows = widest.rows;
  renderWidget();
  const tallest = dev.offsetHeight * MODAL_SCALE;
  state.rows = keep;
  renderWidget();
  setAnchor(tallest);
}

// Interactive use only: if the panel pushes past the film's tallest mix, let the
// anchor follow so the card cannot run off the bottom of the stage.
function recentre() {
  const dev = document.querySelector('.hero-modal .device');
  if (!dev || anchorY === null) return;
  const h = dev.offsetHeight * MODAL_SCALE;
  if (anchorY + h > STAGE_H - 8) setAnchor(h);
}
if (window.ResizeObserver) {
  new ResizeObserver(recentre).observe(document.querySelector('.hero-modal .device'));
}
if (document.fonts && document.fonts.ready) document.fonts.ready.then(recentre);

function renderWidget() {
  document.getElementById('h-amt').textContent = state.amount;
  document.getElementById('h-usd').innerHTML = '&asymp; $' + state.usd;
  document.getElementById('h-cap').textContent = state.cap;
  document.getElementById('h-pill').innerHTML =
    `<div class="av22">${mark(state.sym.toLowerCase(), 22)}` +
    `<span class="bd">${mark('base', 12) || ''}</span></div>` +
    `<span class="sym">${state.sym}</span>`;
  const n = state.rows.length;
  document.getElementById('h-count').textContent = n + (n === 1 ? ' asset' : ' assets');
  document.getElementById('h-sub').textContent =
    `Auto-selected to cover your $${state.amount} deposit`;
  document.getElementById('h-rows').innerHTML = state.rows.map(r => `
    <div class="arow">
      <div class="l">${av34(r.coin, badgeOf(r.badge, 14))}<div>
        <div class="nm">${r.sym}</div><div class="on">${r.chain}</div></div></div>
      <div class="r"><div class="amt">${r.amt}</div><div class="usd">${r.usd}</div></div>
    </div>`).join('');
  recentre();
}

function renderAssets() {
  const box = document.getElementById('p-assets');
  box.innerHTML = state.rows.map((r, i) => `
    <div class="asset">
      <input value="${r.sym}"   data-i="${i}" data-k="sym"   aria-label="symbol">
      <input value="${r.chain}" data-i="${i}" data-k="chain" aria-label="chain">
      <input value="${r.amt}"   data-i="${i}" data-k="amt"   aria-label="amount">
      <input value="${r.usd}"   data-i="${i}" data-k="usd"   aria-label="usd">
      <button class="del" data-del="${i}" type="button" aria-label="remove">&times;</button>
    </div>`).join('');
}

function renderScenarios() {
  document.getElementById('p-scenarios').innerHTML = SCENARIOS.map(s =>
    `<button class="seg" type="button" data-sc="${s.id}" aria-pressed="false">${s.label}</button>`
  ).join('');
}

function applyScenario(id) {
  const s = SCENARIOS.find(x => x.id === id); if (!s) return;
  state.amount = s.amount; state.usd = s.usd;
  state.rows = JSON.parse(JSON.stringify(s.rows));
  document.getElementById('p-amt').value = s.amount;
  document.getElementById('p-usd').value = s.usd;
  document.querySelectorAll('[data-sc]').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.sc === id)));
  renderAssets(); renderWidget();
}

// ---- wiring ----------------------------------------------------------------
document.getElementById('p-scenarios').addEventListener('click', e => {
  const b = e.target.closest('[data-sc]'); if (b) applyScenario(b.dataset.sc);
});
[['p-sym','sym'],['p-chain','chain'],['p-amt','amount'],['p-usd','usd'],['p-cap','cap']]
  .forEach(([id, key]) => document.getElementById(id).addEventListener('input', e => {
    state[key] = e.target.value; renderWidget();
  }));
document.getElementById('p-assets').addEventListener('input', e => {
  const t = e.target; if (t.dataset.k == null) return;
  state.rows[+t.dataset.i][t.dataset.k] = t.value; renderWidget();
});
document.getElementById('p-assets').addEventListener('click', e => {
  const b = e.target.closest('[data-del]'); if (!b) return;
  state.rows.splice(+b.dataset.del, 1); renderAssets(); renderWidget();
});
document.getElementById('p-add').addEventListener('click', () => {
  state.rows.push({ sym: 'USDC', chain: 'on Base', amt: '0.00 USDC', usd: '$0.00',
                    coin: 'usdc', badge: 'base' });
  renderAssets(); renderWidget();
});
document.getElementById('p-zoom').addEventListener('input', e => {
  document.body.style.setProperty('--hz', e.target.value);
  document.getElementById('p-zoomv').textContent = (+e.target.value).toFixed(2) + 'x';
});

renderScenarios(); applyScenario('s20');

/* ===========================================================================
   The film: the user types an amount, the flow resolves a funding mix for it,
   three times over — 20 -> 2 stablecoins, 30 -> +1 native, 40 -> +1 longtail.
   Each amount is cleared and retyped rather than edited in place, because the
   digit that changes is the leading one and there is no way to backspace that
   without taking the trailing digit with it.

   record.py's contract: park on ?hold=1, expose __startSegment to begin and
   bump __cycle when the run is done, so the recorder knows when to stop.
   =========================================================================== */
const P = new URLSearchParams(location.search);
// record.py never passes ?rec — but it always passes ?sw, so that is the tell.
// Keying off it means the recorder needs no special-casing for this page.
const REC = P.has('rec') || P.has('sw');

if (REC) {
  document.body.classList.add('rec');
  // swap in the plate that matches the capture size — see build-hero.py
  document.querySelector('.hero-plate').src = 'hero-plate@2x.png';
  const SW = +(P.get('sw') || __STAGE_W__), SH = +(P.get('sh') || __STAGE_H__);
  const ZOOM = +(P.get('zoom') || 1);
  const vs = document.getElementById('vstage');
  const st = document.getElementById('stage');
  // fill the recorder's frame exactly: lay out at sw x sh, scaled by zoom
  const k = Math.min(SW / __STAGE_W__, SH / __STAGE_H__) * ZOOM;
  document.body.style.setProperty('--hz', String(k));
  vs.style.width = (SW * ZOOM) + 'px';
  vs.style.height = (SH * ZOOM) + 'px';
}

const sleep = ms => new Promise(r => setTimeout(r, ms));
const easeOutQuint = p => 1 - Math.pow(1 - p, 5);
const clamp01 = p => p < 0 ? 0 : p > 1 ? 1 : p;

/* ---------------------------------------------------------------------------
   The film as a pure function of time.

   Nothing here is driven by a clock the renderer owns — no CSS animation, no
   transition, no rAF tween. __renderFrame(t) computes the exact visual state at
   t seconds and paints it, so the recorder can walk t in perfect 1/FPS steps
   and every frame is correct by construction.

   That indirection is the whole point. CSS animations do not advance under CDP
   virtual time, and rAF timestamps jump when the virtual clock is fast-
   forwarded, so both snapped to their end state in a single frame. Driving the
   timeline explicitly sidesteps the question entirely and makes the output
   deterministic: the same t always renders the same pixels.
--------------------------------------------------------------------------- */
const FILM = __FILM__;
const TYPE_MS = 175, CLEAR_MS = 110, RESOLVE_MS = 420,
      CHAR_IN_MS = 150, CHAR_OUT_MS = 110, USD_MS = 320, CARET_MS = 1100,
      ROW_OUT_MS = 380, ROW_OUT_STAGGER = 70, LOOP_TAIL_MS = 420,
      ROW_MS = 700, ROW_STAGGER = 110, HOLD_MS = 1650, LEAD_MS = 500;

function buildTimeline() {
  const amounts = [];            // {t, value}
  const rows    = [];            // {row, t0}
  let t = LEAD_MS, shown = 0, cur = '';

  amounts.push({ t: 0, value: '', kind: 'idle' });
  FILM.forEach(id => {
    const sc = SCENARIOS.find(x => x.id === id);
    // `was` carries the character a delete removed, so it can be animated out
    while (cur.length) {
      const was = cur; cur = cur.slice(0, -1); t += CLEAR_MS;
      amounts.push({ t, value: cur, kind: 'del', from: was });
    }
    for (const ch of sc.amount) { cur += ch; amounts.push({ t, value: cur, kind: 'add' }); t += TYPE_MS; }
    t += RESOLVE_MS;
    const target = sc.rows;
    for (let i = shown; i < target.length; i++) {
      rows.push({ row: target[i], t0: t + (i - shown) * ROW_STAGGER });
    }
    const lastStart = t + Math.max(0, target.length - shown - 1) * ROW_STAGGER;
    shown = target.length;
    t = lastStart + ROW_MS + HOLD_MS;
  });

  // Wind-down. The film has to end on the state it began in — empty field, no
  // rows — or looping it cuts hard from a full card back to a blank one. The
  // amount is deleted first and the mix then falls away behind it, which reads
  // as cause and effect rather than two things clearing at once.
  rows.forEach(r => { r.t1 = null; });
  while (cur.length) {
    const was = cur; cur = cur.slice(0, -1); t += CLEAR_MS;
    amounts.push({ t, value: cur, kind: 'del', from: was });
  }
  rows.forEach((r, idx) => { r.t1 = t + (rows.length - 1 - idx) * ROW_OUT_STAGGER; });
  t += (rows.length - 1) * ROW_OUT_STAGGER + ROW_OUT_MS + LOOP_TAIL_MS;

  return { amounts, rows, end: t };
}

const TL = buildTimeline();

// The caret blinks on a sine, so its phase at the loop point has to match its
// phase at t=0 or the seam shows — it was the one element still differing
// between the first and last frame. Snapping the period to a whole number of
// cycles across the film makes the loop exact.
const CARET_PERIOD = TL.end / Math.max(1, Math.round(TL.end / CARET_MS));

function __renderFrame(tSec) {
  const t = tSec * 1000;

  let i = 0;
  while (i + 1 < TL.amounts.length && TL.amounts[i + 1].t <= t) i++;
  const ev = TL.amounts[i], prev = TL.amounts[i - 1] || { value: '' };
  const since = t - ev.t;

  // The character being typed, or the one being deleted, carries its own
  // progress — so a keystroke reads as a soft landing rather than a hard pop.
  let shown = ev.value, headP = 1, dying = false;
  if (ev.kind === 'add') {
    headP = clamp01(since / CHAR_IN_MS);
  } else if (ev.kind === 'del' && since < CHAR_OUT_MS) {
    shown = ev.from; dying = true;
    headP = 1 - clamp01(since / CHAR_OUT_MS);
  }

  // the quote eases toward the typed figure instead of snapping to it
  const target = +(ev.value || 0), before = +(prev.value || 0);
  const usdNum = before + (target - before) * easeOutQuint(clamp01(since / USD_MS));

  const live = TL.rows.filter(r =>
    t >= r.t0 && (r.t1 == null || t < r.t1 + ROW_OUT_MS));
  state.amount = shown;
  state.usd = usdNum.toFixed(2);
  state.rows = live.map(r => r.row);
  renderWidget();

  // re-render the amount with the head character wrapped so it can be eased
  const amtEl = document.getElementById('h-amt');
  if (shown.length) {
    const e = easeOutQuint(headP);
    const dy = dying ? (1 - e) * -4 : (1 - e) * 8;
    amtEl.innerHTML = shown.slice(0, -1) +
      `<span style="display:inline-block;opacity:${e.toFixed(3)};` +
      `transform:translateY(${dy.toFixed(2)}px)">${shown.slice(-1)}</span>`;
  }

  // the action button follows the form: nothing typed, nothing to deposit
  const cta = document.getElementById('h-cta');
  if (cta) {
    const ready = !!shown && +shown > 0 && live.length > 0;
    cta.className = ready ? 'cta primary' : 'cta disabled';
    cta.textContent = ready ? 'Deposit Now' : 'Enter an Amount';
  }

  // a soft sine blink rather than a hard on/off
  const caret = document.querySelector('.hero-modal .dep-caret');
  if (caret) {
    const phase = (t % CARET_PERIOD) / CARET_PERIOD;
    caret.style.opacity = (0.18 + 0.82 * (0.5 + 0.5 * Math.cos(phase * 2 * Math.PI))).toFixed(3);
  }

  // each row carries its own progress, so a stagger is just four different t0s
  const els = [...document.querySelectorAll('#h-rows .arow')];
  live.forEach((r, i) => {
    const el = els[i]; if (!el) return;
    const inP  = easeOutQuint(clamp01((t - r.t0) / ROW_MS));
    const outP = r.t1 == null ? 0 : clamp01((t - r.t1) / ROW_OUT_MS);
    const e = inP * (1 - outP);                       // whichever is limiting
    el.style.opacity = e;
    el.style.transform = `translateY(${((1 - inP) * 10 + outP * 4).toFixed(2)}px)`;
  });
  return t >= TL.end;
}
window.__renderFrame = __renderFrame;
window.__filmDuration = TL.end / 1000;

// Browser preview drives the same timeline off the wall clock.
async function runFilm() {
  anchorToTallest(FILM);
  const t0 = performance.now();
  return new Promise(res => {
    (function tick(now) {
      const done = __renderFrame(((now || performance.now()) - t0) / 1000);
      if (done) { window.__cycle = (window.__cycle || 0) + 1; res(); }
      else requestAnimationFrame(tick);
    })(performance.now());
  });
}

window.__anchorForFilm = () => anchorToTallest(FILM);
window.__armIntro = () => {};                     // the hero has no rise to play
window.__startSegment = () => { window.__cycle = 0; runFilm(); };
if (REC && !P.has('hold')) window.__startSegment();

// off-camera, let it loop so the sequence can be reviewed in the browser
if (!REC) {
  document.getElementById('p-scenarios').insertAdjacentHTML('afterend',
    '<button class="seg" id="p-play" type="button" style="margin-top:6px">▶ play the sequence</button>');
  document.getElementById('p-play').addEventListener('click', () => runFilm());
}
</script>
</body>
</html>
"""

out = (PAGE
       .replace('__STYLES__',     STYLES)
       .replace('__SVG__',        SVG_LITERAL)
       .replace('__IMG__',        IMG_LITERAL)
       .replace('__EXTRA_MARKS__', json.dumps(EXTRA_MARKS))
       .replace('__SCENARIOS__',  json.dumps(SCENARIOS, indent=2))
       .replace('__FILM__',       json.dumps(FILM))
       .replace('__STAGE_W__',    str(STAGE_W))
       .replace('__STAGE_H__',    str(STAGE_H))
       .replace('__MODAL_X__',    str(MODAL_X))
       .replace('__MODAL_Y__',    str(MODAL_Y))
       .replace('__MODAL_CY__',   str(MODAL_CY))
       .replace('__STAGE_H__',    str(STAGE_H))
       .replace('__CARD_W__',     str(CARD_W))
       .replace('__SCALE_PCT__',  '%.1f' % (SCALE * 100))
       .replace('__SCALE__',      '%.5f' % SCALE)
       .replace('__DEST_SYM__',   DEST['sym'])
       .replace('__DEST_CHAIN__', DEST['chain'])
       .replace('__CAP__',        DEST['cap'])
       .replace('__AMT__',        SCENARIOS[0]['amount'])
       .replace('__USD__',        SCENARIOS[0]['usd']))

open(DST, 'w', encoding='utf-8').write(out)
print('wrote %s (%.0f KB)' % (os.path.relpath(DST, os.path.dirname(ROOT)), len(out) / 1024))
