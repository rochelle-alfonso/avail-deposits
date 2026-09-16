#!/usr/bin/env python3
"""Derive flow/configurator.html from the Widget Configurator prototype.

The prototype is authored to run standalone at 100%; this build adapts it to
sit inside the site's "Configure Your Deposit Flow" panel. Re-run after editing
the prototype:

    python3 flow/build-configurator.py
"""
import os, re, sys

SRC = os.path.expanduser('~/avail-configurator-prototype.html')
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configurator.html')

src = open(SRC).read()


def sub(old, new, what):
    if old not in src:
        sys.exit('build: could not find %s — has the prototype changed?' % what)
    return src.replace(old, new, 1)


# 0a ── Base's mark ------------------------------------------------------------
# The prototype's chain_base was a blue gradient disc — not Base's logo at all.
# Replaced with the official Square from the brand pack, set on a white circle
# so it sits with the other round chain marks in the dropdown.
import base64 as _b64
_mark = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'base-mark.png'), 'rb').read()
_mark_uri = 'data:image/png;base64,' + _b64.b64encode(_mark).decode()
_before = src
src = re.sub(r'("chain_base"\s*:\s*")data:image/[^"]+(")',
             lambda m: m.group(1) + _mark_uri + m.group(2), src, count=1)
if src == _before:
    sys.exit('build: could not find the chain_base mark to replace')

# 0 ── app identity, switchable per page --------------------------------------
# Both site pages embed this one file, so the Aave branding cannot simply be
# replaced: the trading page still wants it. `?app=prediction` swaps every
# Aave-branded string for the generic prediction-market equivalent, the same way
# `?bg=` swaps the plate. Anything else keeps the prototype's own defaults.
#
# ORDER MATTERS. The literal replacements run FIRST and the APP object is
# injected LAST. Done the other way round, the global replaces rewrite APP's own
# Aave defaults into `ph:APP.ph` — a self-reference that throws in the branch
# that evaluates it, taking the whole script with it. That shipped once; the
# static markup in the page reads the same either way, so it looked fine.
for old, new, what in (
    ("{n:'Aave - Arbitrum', img:IMG.aave}", "{n:APP.presetA, img:IMG[APP.imgA]}", 'preset A'),
    ("{n:'Aave - Ethereum', img:IMG.aave}", "{n:APP.presetB, img:IMG[APP.imgB]}", 'preset B'),
    ("const CHAIN_IDX=9;", "const CHAIN_IDX=APP.chainIdx;", 'the destination chain index'),
):
    src = sub(old, new, what)

for old, new in (
    ("S.appName='Aave'",                    "S.appName=APP.name"),
    ("S.heading='Deposit on Aave Arbitrum'", "S.heading=APP.heading"),
    ("'Deposit on Aave'",                   "APP.ph"),
    ("'Earn yield on Aave'",                "APP.typed"),
    ("S.tokens=[0,1]",                      "S.tokens=APP.tokens.slice()"),
    # the chapter tapped a hardcoded Arbitrum row and ended on a hardcoded
    # three-token list, both of which contradict a Base/USDC preset
    ('[data-chain="9"]',                    '[data-chain="\'+CHAIN_IDX+\'"]'),
    ("S.tokens=[0,1,2]",                    "S.tokens=APP.tokensAfterSearch.slice()"),
):
    if old not in src:
        sys.exit('build: could not find %r — has the prototype changed?' % old)
    src = src.replace(old, new)

# Show the switch itself. The step sets the "before" token, then swaps to the
# real one 820ms later — slow enough to read, and it rides inside the existing
# 140ms-per-step cadence rather than shifting every step after it.
src = sub(
    "()=>{ S.tokens=APP.tokens.slice(); renderPanel(); flash('tokenField'); },",
    """()=>{ const after = APP.tokens.slice();
          if (APP.tokensBefore) {
            S.tokens = APP.tokensBefore.slice(); renderPanel(); flash('tokenField');
            demoTimers.push(setTimeout(()=>{ S.tokens = after; renderPanel();
                                             flash('tokenField'); }, 820));
          } else { S.tokens = after; renderPanel(); flash('tokenField'); } },""",
    'the token step')
src = sub(
    "  return sleep(seq.length*140+240);",
    "  return sleep(seq.length*140+240 + (APP.tokensBefore ? 900 : 0));",
    'the preset-fill dwell')

src = sub(
    "const PRESETS=[",
    """const APP = ((new URLSearchParams(location.search)).get('app') === 'prediction')
  ? { name:'Prediction Market', heading:'Deposit on Prediction Market',
      ph:'Deposit on Prediction Market', typed:'Fund your next position',
      presetA:'Polymarket (Demo) - Base', presetB:'Polymarket (Demo) - Arbitrum',
      // the preset icon names the app; with no app brand it falls to the chain
      imgA:'chain_base', imgB:'chain_arbitrum',
      // CHAINS[8] is Base (8453); TOKENS[3] is plain USDT, TOKENS[2] is USDC.
      //
      // The preset lands on USDT and the search chapter is where USDC arrives.
      // That ordering is the point: with USDC already selected, the chapter
      // searched for a token that was there and added nothing, which read as a
      // dead step. tokensBefore is null because the switch is no longer a
      // sleight of hand inside the preset fill — it is the gesture the demo is
      // there to show.
      chainIdx:8, tokens:[3], tokensBefore:null,
      tokensAfterSearch:[2] }
  : { name:'Aave', heading:'Deposit on Aave Arbitrum',
      ph:'Deposit on Aave', typed:'Earn yield on Aave',
      presetA:'Aave - Arbitrum', presetB:'Aave - Ethereum',
      imgA:'aave', imgB:'aave',
      // CHAINS[9] is Arbitrum (42161); TOKENS[0,1] are USDT0 and AAVE.
      // No tokensBefore: the trading demo fills the field in one go, as it did.
      chainIdx:9, tokens:[0,1], tokensBefore:null,
      tokensAfterSearch:[0,1,2] };
const PRESETS=[""",
    'the preset table (to seat the app-identity switch)')

# 1 ── scale-correct the demo cursor ------------------------------------------
# The prototype measures targets with getBoundingClientRect (painted pixels) but
# applies the result as a translate *inside* .frame, which this build scales to
# 997/1180. At 100% the two agree, so the bug never shows standalone; scaled,
# every click lands ~18% short and up-left. Divide the ratio back out.
src = sub(
    "function moveTo(el,{dur=760,dx=0,dy=0}={}){",
    "function __k(){ const f=frameEl(); return f.getBoundingClientRect().width / (f.offsetWidth || 1180); }\n"
    "function moveTo(el,{dur=760,dx=0,dy=0}={}){",
    'moveTo')

src = sub(
    """    const f=frameEl().getBoundingClientRect(), r=el.getBoundingClientRect();
    const x=(r.left-f.left)+r.width/2+dx, y=(r.top-f.top)+r.height/2+dy;""",
    """    const k=__k();
    const f=frameEl().getBoundingClientRect(), r=el.getBoundingClientRect();
    const x=(r.left-f.left)/k+(r.width/k)/2+dx, y=(r.top-f.top)/k+(r.height/k)/2+dy;""",
    'moveTo body')

src = sub(
    """      const f=frameEl().getBoundingClientRect(), r=$('huedot').getBoundingClientRect();
      cursorEl().style.transition='transform .42s var(--ease)';
      cursorEl().style.transform=`translate(${(r.left-f.left)+r.width/2-4}px, ${(r.top-f.top)+r.height/2-3}px)`;""",
    """      const k2=__k();
      const f=frameEl().getBoundingClientRect(), r=$('huedot').getBoundingClientRect();
      cursorEl().style.transition='transform .42s var(--ease)';
      cursorEl().style.transform=`translate(${(r.left-f.left)/k2+(r.width/k2)/2-4}px, ${(r.top-f.top)/k2+(r.height/k2)/2-3}px)`;""",
    'hue-drag loop')

# 2 ── open on the first real action ------------------------------------------
# Chapter 0 ("Empty configuration") just drifts the cursor around for ~3.9s.
# Skip it so the loop opens on the tap that picks a preset. The chapter is left
# in CH because snapshot() keys its state off the original indices.
src = sub(
    "    idx=(idx+1)%CH.length;",
    "    idx=(idx+1)%CH.length; if(idx===FIRST_CH) idx=FIRST_CH;\n"
    "    if(idx===0) idx=FIRST_CH;   /* skip the idle intro chapter */",
    'runDemo wrap')

# 3 ── one token + its chain, not a stack of two -------------------------------
# The preview pill stacked up to two token icons; the design shows a single
# token badged with the destination chain.
OLD_TOK = """  $('wTokStack').innerHTML = toks.slice(0,2).map(i=>`<img src="${TOKENS[i].img}"/>`).join('');"""
NEW_TOK = """  $('wTokStack').innerHTML = '<span class="tokone">'
    + `<img src="${TOKENS[toks[0]].img}"/>`
    + (S.chain!=null ? `<img class="tokchain" src="${CHAINS[S.chain].img}"/>` : '')
    + '</span>';"""
src = sub(OLD_TOK, NEW_TOK, 'widget token stack')

OVERRIDE = r'''
<style id="player-override">
/* ===== embeddable player build =====
   Drops the prototype's page chrome and pins the browser frame onto the
   Figma panel's own gradient plate (1211x581, the artboard size). */
html,body{height:auto;margin:0;padding:0;background:transparent!important}
body{display:block!important;min-height:0!important;padding:0!important;gap:0!important;
  background:none!important;overflow:hidden}
.controls,.hint{display:none!important}

#vstage{
  position:relative;
  zoom:var(--zoom,1);
  width:var(--sw); height:var(--sh);
  overflow:hidden;
  background:#c9d3f7;
}
#vbg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
/* the window sits where the artboard puts it: 107,44 at 997 wide, and runs
   off the bottom of the panel exactly as it does in the design */
#vstage .stage{
  position:absolute; left:107px; top:44px;
  transform:scale(var(--winScale));
  transform-origin:top left;
  gap:0;
}
#vstage .frame{ border-radius:12px 12px 0 0 }
/* The panel's last stretch sits behind the stage clip, so on its own it can
   never scroll the final section into view. Extra trailing space gives it the
   room; it is empty, so nothing shows. */
#vstage #panel-deposit, #vstage #panel-bridge{ padding-bottom:190px }

/* the preview's token pill: one token, badged with the destination chain */
#vstage .tokpill .stack .tokone{position:relative;display:block;width:24px;height:24px;flex-shrink:0}
#vstage .tokpill .stack .tokone img{width:24px;height:24px;border-radius:999px;display:block}
#vstage .tokpill .stack .tokone img+img{margin-left:0}
#vstage .tokpill .stack .tokone img.tokchain{
  position:absolute;right:-3px;bottom:-3px;
  width:12px;height:12px;outline:1.5px solid #fff;background:#fff;
}
</style>
'''

RUNNER = r'''
<script id="player-runner">
/* Loops the walkthrough from the first real action and reports a completed
   pass, so a recorder knows where to cut. */
(function(){
  const P = new URLSearchParams(location.search);
  const SW = +(P.get('sw') || 1211), SH = +(P.get('sh') || 581);
  const ZOOM = +(P.get('zoom') || 1);
  const WIN = +(P.get('win') || 997);          // window width in the artboard

  const r = document.documentElement.style;
  r.setProperty('--sw', SW + 'px');
  r.setProperty('--sh', SH + 'px');
  r.setProperty('--zoom', String(ZOOM));
  r.setProperty('--winScale', String(WIN / 1180));    // .frame is 1180px wide

  const stage = document.querySelector('.stage');
  const vs = document.createElement('div'); vs.id = 'vstage';
  const bg = document.createElement('img'); bg.id = 'vbg';
  bg.src = P.get('bg') || 'config-bg.webp'; bg.alt = '';
  stage.parentNode.insertBefore(vs, stage);
  vs.appendChild(bg); vs.appendChild(stage);


  /* The window runs off the bottom of the panel, so the lower part of the
     sidebar is cut off by the stage rather than by the app. Before the cursor
     goes anywhere, scroll that column so the target is actually on screen. */
  const PANELS = ['panel-deposit', 'panel-bridge'];
  function scrollerFor(el){
    for (let i = 0; i < PANELS.length; i++){
      const p = document.getElementById(PANELS[i]);
      if (p && p.contains(el) && p.scrollHeight - p.clientHeight > 2) return p;
    }
    return null;
  }
  function scrollPanel(p, to, dur){
    return new Promise(res => {
      const from = p.scrollTop, t0 = performance.now();
      (function step(now){
        const q = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - q, 3);
        p.scrollTop = from + (to - from) * e;
        if (q < 1) requestAnimationFrame(step); else res();
      })(t0);
    });
  }
  async function ensureVisible(el){
    const p = scrollerFor(el);
    if (!p) return;
    const k = __k();
    const pr = p.getBoundingClientRect();
    const sr = document.getElementById('vstage').getBoundingClientRect();
    const visTop = Math.max(pr.top, sr.top);        // the band actually on screen
    const visBot = Math.min(pr.bottom, sr.bottom);
    const r = el.getBoundingClientRect();
    const PAD = 40 * k;
    let need = 0;
    if (r.top < visTop + PAD) need = r.top - (visTop + PAD);
    else if (r.bottom > visBot - PAD) need = r.bottom - (visBot - PAD);
    if (Math.abs(need) < 2) return;
    let to = p.scrollTop + need / k;
    to = Math.max(0, Math.min(to, p.scrollHeight - p.clientHeight));
    if (Math.abs(to - p.scrollTop) < 2) return;
    await scrollPanel(p, to, 520);
    await sleep(180);                               // let it settle, then point
  }
  // every cursor move goes through moveTo, including tap()
  const __moveTo = moveTo;
  moveTo = async function(el, opts){
    await ensureVisible(el);
    return __moveTo(el, opts);
  };

  window.__cycle = 0;
  let prev = -1;
  setInterval(function(){
    if (typeof idx === 'undefined' || idx === prev) return;
    if (prev === CH.length - 1 && idx === FIRST_CH) window.__cycle++;
    prev = idx;
  }, 80);
  window.__chapter  = () => (typeof idx === 'undefined' ? -1 : idx);
  window.__chapters = () => CH.length;
  window.__scale    = () => __k();

  window.__startSegment = () => {
    window.__cycle = 0;
    idx = FIRST_CH;            // open on "pick a preset", not the idle intro
    snapshot(idx); paintNav();
    play();
  };
  if (!P.has('hold')) window.__startSegment();
})();
</script>
'''

# FIRST_CH has to exist before runDemo and the runner reference it
src = sub("const CH=[", "const FIRST_CH=1;   /* chapter 0 is the idle intro — never entered */\nconst CH=[", 'CH table')

out = src.replace('</head>', OVERRIDE + '</head>', 1)
out = out.replace('</body>', RUNNER + '</body>', 1)
for marker in ('player-override', 'player-runner', '__k()', 'FIRST_CH'):
    assert marker in out, marker
open(DST, 'w').write(out)
print('wrote %s (%d bytes)' % (DST, len(out)))
