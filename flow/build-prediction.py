#!/usr/bin/env python3
"""Generate flow/player-prediction.html — the source the "One Flow to a Funded
Position" clips are recorded from.

Same shape as build-configurator.py: this file is the editable source and the
.html it writes is a build artefact. It reuses player.html's stylesheet, its
machinery (screen router, demo cursor, step engine, count-up, confetti, the
recorder's vstage/plate/zoom/intro hooks) and its inlined brand assets, and
swaps in the prediction-market screens from the Paper page "Prediction Market"
(file 01KRGJMCYD8BQA4GJ4W95K68XS).

    python3 flow/build-prediction.py
"""
import base64, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, 'player.html')
DST  = os.path.join(ROOT, 'player-prediction.html')
ASSETS = os.path.expanduser('~/Documents/fastbridge/assets')

src = open(SRC, encoding='utf-8').read()

# ---- reuse the blobs already inlined in player.html -------------------------
def grab(pattern, what):
    m = re.search(pattern, src)
    if not m:
        sys.exit(f'could not find {what} in player.html')
    return m.group(1)

TEXTURE = grab(r'--paper-texture:url\("(data:image/png;base64,[^"]+)"\)', 'the artboard texture')
HEATVID = grab(r"const HEATVID = '(data:video/mp4;base64,[^']+)'", 'the heatmap clip')
COINS = {}
for key in ('usdc', 'eth', 'optimism'):
    COINS[key] = grab(rf'\b{key}:"(data:image/png;base64,[^"]+)"', f'the {key} mark')

# ---- add the two marks this flow needs that player.html has never used ------
def datauri(path, mime):
    with open(path, 'rb') as fh:
        return f'data:{mime};base64,' + base64.b64encode(fh.read()).decode()

COINS['citrea']  = datauri(os.path.join(ASSETS, 'citrea-icon.png'), 'image/png')
COINS['megaeth'] = datauri(os.path.join(ASSETS, 'megaeth-icon.svg'), 'image/svg+xml')
# ctUSD got a real mark in the Paper file on 2026-09-10 - an orange coin with a
# Citrea badge - so it no longer has to borrow the plain Citrea hexagon.
COINS['ctusd']   = datauri(os.path.join(ASSETS, 'ctusd-icon.png'), 'image/png')
COINS['ctbadge'] = datauri(os.path.join(ASSETS, 'citrea-badge.png'), 'image/png')

# The stylesheet + the recorder's override block, lifted verbatim.
STYLES = re.search(r'<style>\n(.*?)\n</style>', src, re.S).group(1)
OVERRIDE = re.search(r'<style id="player-override">\n(.*?)\n</style>', src, re.S).group(1)
# player.html pins per-screen min-heights by id; ours are different screens.
STYLES = re.sub(r'/\* per-screen heights.*?#s-success\{min-height:0\}\n', '', STYLES, flags=re.S)

# ---------------------------------------------------------------- prediction CSS
PRED_CSS = """
#s-wallet,#s-deposit,#s-bet,#s-placed{min-height:0}
.hair{height:1px;background:#F0F0EF;flex-shrink:0}
.tnum{font-variant-numeric:tabular-nums}

/* ===== 1 · Wallet ===== */
.wal-card{padding:20px 16px 22px;display:flex;flex-direction:column;gap:6px}
.wal-cap{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:500;
  letter-spacing:.08em;line-height:20px;text-transform:uppercase;color:var(--muted)}
.wal-big{font-family:var(--display);font-size:56px;font-weight:500;line-height:60px;
  letter-spacing:-.01em;color:var(--ink);font-variant-numeric:tabular-nums}
.wal-sub{font-size:14px;line-height:20px;color:var(--muted);font-variant-numeric:tabular-nums}

/* ===== 2 · Deposit ===== */
.dep-head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.dep-label{font-size:12px;font-weight:500;letter-spacing:.08em;line-height:20px;
  text-transform:uppercase;color:var(--muted)}
.dep-cap{font-size:14px;line-height:20px;color:var(--muted)}
.dep-cap b{font-weight:600;color:var(--ink);font-variant-numeric:tabular-nums}
.dep-card{padding:16px;display:flex;flex-direction:column;gap:14px}
.dep-row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.dep-hero{display:flex;align-items:center;flex:1;min-width:0}
.dep-hero .n{font-family:var(--display);font-size:40px;font-weight:500;line-height:44px;
  letter-spacing:.01em;color:var(--ink);font-variant-numeric:tabular-nums;flex-shrink:0}
.dep-caret{width:2px;height:36px;border-radius:2px;background:var(--blue);flex-shrink:0;
  animation:blink 1.05s steps(1) infinite}
.dep-pill{display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);
  border-radius:999px;padding:5px 10px 5px 5px;box-shadow:0 1px 2px rgba(22,22,21,.04);flex-shrink:0}
.dep-pill .sym{font-size:16px;font-weight:500;line-height:24px;color:var(--ink)}
.dep-approx{display:flex;align-items:center;gap:7px;font-size:14px;line-height:16px;
  color:var(--muted);font-variant-numeric:tabular-nums;margin-top:-4px}
.pcts{display:flex;align-items:center;gap:6px}
.pct-chip{flex:1;text-align:center;background:#F4F4F3;border-radius:8px;padding:5px 10px;
  font-size:12px;font-weight:500;line-height:20px;color:#363635;transition:.25s var(--ease)}
.pct-chip.on{background:#E5F0FE;color:var(--blue)}

/* pay-with card */
.pw{padding:16px;display:flex;flex-direction:column;gap:14px}
.pw-top{display:flex;align-items:flex-start;justify-content:space-between}
.pw-l{display:flex;flex-direction:column;gap:6px}
.pw-tr{display:flex;align-items:center;gap:8px}
.pw-t{font-size:15px;font-weight:500;line-height:18px;color:var(--ink)}
.pw-count{background:#F5F9FD;border:1px solid #C0D5FB;border-radius:100px;padding:1px 6px;
  font-size:9px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#006BF3;line-height:12px}
.pw-sub{font-size:12px;line-height:16px;color:#9A9A99}
.pw-edit{font-size:14px;font-weight:500;line-height:18px;color:#006BF3}
.pw-rows{display:flex;flex-direction:column;gap:10px}
.arow{display:flex;align-items:center;justify-content:space-between;gap:10px}
.arow .l{display:flex;align-items:center;gap:10px}
.arow .nm{font-size:16px;font-weight:600;line-height:24px;color:var(--ink)}
.arow .on{font-size:14px;line-height:20px;color:var(--muted)}
.arow .r{display:flex;flex-direction:column;align-items:flex-end;gap:1px;flex-shrink:0}
.arow .amt{font-size:16px;font-weight:600;line-height:24px;color:var(--ink);font-variant-numeric:tabular-nums}
.arow .usd{font-size:14px;line-height:20px;color:var(--muted);font-variant-numeric:tabular-nums}
.screen.active .arow{animation:rise .44s var(--ease) both}
.screen.active .arow:nth-child(1){animation-delay:.24s}
.screen.active .arow:nth-child(2){animation-delay:.33s}
.screen.active .arow:nth-child(3){animation-delay:.42s}
.av34{position:relative;width:34px;height:34px;flex-shrink:0}
.av34>img{width:34px;height:34px;border-radius:999px;display:block}
.av34 .bd{position:absolute;left:22px;top:22px;width:14px;height:14px;border-radius:999px;
  outline:1px solid #FFFFFE;overflow:hidden;background:#F4F4F3;display:flex;align-items:center;justify-content:center}
.av34 .bd img{width:14px;height:14px;display:block}
/* the token pill's mark is its own size - reusing .av34 forced it to 34px
   and pushed the symbol under the coin */
.av22{position:relative;width:22px;height:22px;flex-shrink:0}
.av22>img{width:22px;height:22px;border-radius:999px;display:block}
.av22 .bd{position:absolute;left:13px;top:13px;width:11px;height:11px;border-radius:999px;
  outline:1px solid #FFFFFE;overflow:hidden;background:#F0F0EF;display:flex;
  align-items:center;justify-content:center}
.av22 .bd img{width:9px;height:9px;display:block;border-radius:0}
.fees{padding:15px 16px;display:flex;align-items:center;justify-content:space-between}
.fees .k{font-size:16px;font-weight:500;line-height:24px;color:var(--ink)}
.fees .k i{font-style:normal;color:var(--muted);font-weight:400}
.fees .v{display:flex;align-items:center;gap:8px;font-size:16px;font-weight:600;
  line-height:24px;color:var(--ink);font-variant-numeric:tabular-nums}

/* ===== 3/4 · Bet card ===== */
.ocard{background:var(--surface);border:1px solid var(--border);border-radius:14px;
  box-shadow:0 1px 12px rgba(91,91,91,.05);display:flex;flex-direction:column;overflow:hidden}
.mkt{display:flex;align-items:center;gap:12px;padding:14px 20px 13px}
.mkt-tile{width:42px;height:42px;flex-shrink:0}
.mkt-tile img{width:100%;height:100%;display:block}
.mkt-q{font-size:14px;font-weight:600;line-height:18px;color:var(--ink);letter-spacing:-.005em}
.mkt-meta{font-size:12px;color:var(--muted);line-height:16px;margin-top:3px}
.obtabs{display:flex;align-items:flex-end;gap:20px;padding:0 20px}
.ot{display:flex;flex-direction:column;align-items:center;gap:9px;padding-top:14px}
.ot .t{font-size:15px;font-weight:500;line-height:20px;color:var(--muted)}
.ot .u{height:2px;width:100%;border-radius:2px;background:transparent}
.ot.sel .t{font-weight:600;color:var(--ink)}
.ot.sel .u{background:var(--ink)}
.trade{display:flex;flex-direction:column;gap:20px;padding:16px 20px}
.yn{display:flex;gap:10px}
.tile{flex:1;height:46px;border-radius:10px;background:#F4F4F3;display:flex;align-items:center;
  justify-content:center;gap:7px;transition:background .3s var(--ease),box-shadow .3s var(--ease),transform .22s var(--ease-spring)}
.tile .nm{font-size:15px;font-weight:600;line-height:20px;color:#5B5B5A;transition:color .3s var(--ease)}
.tile .pr{font-size:15px;font-weight:500;line-height:20px;color:#848483;
  font-variant-numeric:tabular-nums;transition:color .3s var(--ease)}
.tile.on{background:#12AD59;box-shadow:0 8px 20px -10px rgba(18,173,89,.85)}
.tile.on .nm{color:#FFFFFF}
.tile.on .pr{color:#F4F4F3}
.tile.pick{transform:scale(.96)}
.amtgrp{display:flex;flex-direction:column;align-items:center;gap:12px;padding-top:2px}
.amt-head{display:flex;align-items:center;justify-content:space-between;width:376px}
.amt-lbl{font-size:15px;font-weight:500;line-height:20px;color:var(--ink)}
.bal{font-size:13px;line-height:16px;color:var(--muted);font-variant-numeric:tabular-nums}
.stepper{width:376px;height:60px;background:var(--surface);border:1px solid var(--border);
  border-radius:10px;box-shadow:0 1px 2px rgba(22,22,21,.04);display:flex;align-items:center;
  justify-content:space-between;padding:0 6px;gap:2px}
.st-btn{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center}
.st-val{width:116px;text-align:center;font-family:var(--display);font-size:32px;font-weight:500;
  line-height:28px;color:var(--ink);font-variant-numeric:tabular-nums}
.qa{display:flex;align-items:center;gap:6px}
.qchip{flex:1;text-align:center;background:#F4F4F3;border-radius:8px;padding:5px 10px;
  font-size:12px;font-weight:500;line-height:20px;color:#363635;transition:.25s var(--ease)}
.qchip.on{background:#E5F0FE;color:var(--blue)}
.summary{background:#FCFCFB;display:flex;flex-direction:column;gap:11px;padding:16px 20px 18px}
.srow{display:flex;align-items:center;justify-content:space-between}
.slbl{font-size:14px;line-height:20px;color:var(--muted)}
.sv{font-size:14px;font-weight:500;line-height:20px;color:#363635;font-variant-numeric:tabular-nums}
.srow.total .sv{font-size:15px;font-weight:600;color:var(--ink)}
.srow.win{padding-top:3px}
.srow.win .slbl{display:flex;align-items:center;gap:7px;font-size:15px;font-weight:500;color:#363635}
.pct{background:#E7F4EB;border-radius:999px;padding:2px 7px;font-size:11px;font-weight:500;
  line-height:14px;color:#1E7A42;font-variant-numeric:tabular-nums;font-style:normal}
.srow.win .sv{font-family:var(--display);font-size:28px;font-weight:500;line-height:30px;color:#009F50}
.dim .sv,.dim .slbl{color:#C4C4C2}
.dim .pct{opacity:0}
/* no padding-bottom: .screen already carries 16px all round, and the extra
   20px here put the CTA 36px off the card's bottom edge - deeper than
   every other inset on the screen. */
.pfoot{display:flex;flex-direction:column;gap:14px;padding-top:4px}
/* the placing state: the button stays blue but goes light and inert */
.cta.placing{background:#8FB6F8;color:#FFFFFE;cursor:default;box-shadow:none}
.cta.placing::after{display:none}
.spin.w{width:18px;height:18px;border:2.2px solid rgba(255,255,255,.45);border-top-color:#fff}

/* ===== 5 · Bet placed ===== */
.ok-card{display:flex;flex-direction:column;align-items:center;gap:14px;padding:30px 16px 20px}
.ok-mark{width:64px;height:64px;border-radius:999px;background:#12AD59;display:flex;
  align-items:center;justify-content:center;outline:11px solid #13AD5936;flex-shrink:0;
  transform:scale(.3);opacity:0}
.screen.active .ok-mark{animation:coinIn .6s var(--ease-spring) .05s forwards}
.ok-t{display:flex;flex-direction:column;align-items:center;gap:5px}
.ok-h{font-family:var(--display);font-size:26px;font-weight:500;line-height:30px;
  letter-spacing:.01em;color:var(--ink)}
.ok-s{font-size:14px;line-height:20px;color:var(--muted)}
.pos{display:flex;flex-direction:column;gap:11px;padding:16px}
.pos .srow .slbl{color:var(--muted)}
.pos-pill{display:inline-flex;align-items:center;background:#12AD59;border-radius:999px;
  padding:2px 8px;font-size:11px;font-weight:600;line-height:16px;color:#fff}
.pos-val{display:flex;align-items:center;gap:7px;font-size:14px;font-weight:500;
  line-height:20px;color:var(--ink);font-variant-numeric:tabular-nums}
"""

BODY = """
<div class="stage">
  <div class="device" id="device">

    <!-- ================= 1 · WALLET ================= -->
    <section class="screen" data-name="Wallet" id="s-wallet">
      <div class="topbar"><div class="title">Wallet</div>
        <div class="icon-btns"><div class="iconbtn">@refresh@</div></div></div>
      <div class="card soft">
        <div class="wal-card">
          <div class="wal-cap">Available balance @eye@</div>
          <div class="wal-big tnum" id="wal-big">$0.00</div>
          <div class="wal-sub tnum" id="wal-sub">0.00 ctUSD on Citrea</div>
        </div>
      </div>
      <div class="pfoot"><button class="cta primary" id="wallet-cta">Deposit</button></div>
    </section>

    <!-- ================= 2 · DEPOSIT ================= -->
    <section class="screen" data-name="Deposit &middot; route resolved" id="s-deposit">
      <div class="topbar"><div class="title">Deposit</div>
        <div class="icon-btns"><div class="iconbtn">@refresh@</div><div class="iconbtn">@close@</div></div></div>

      <div class="card soft">
        <div class="dep-card">
          <div class="dep-head">
            <div class="dep-label">Deposit</div>
            <div class="dep-cap">You can deposit up to <b>$1,240.55</b></div>
          </div>
          <div class="dep-row">
            <div class="dep-hero"><span class="n tnum" id="dep-n">20</span><span class="dep-caret"></span></div>
            <div class="dep-pill">@ctusdPill@<span class="sym">ctUSD</span></div>
          </div>
          <div class="dep-approx"><span class="tnum" id="dep-usd">&asymp; $20.00</span>@swap@</div>
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
              <div class="pw-tr"><span class="pw-t">Pay with</span><span class="pw-count">3 assets</span></div>
              <div class="pw-sub">Auto-selected to cover your $20 deposit</div>
            </div>
            <div class="pw-edit">Edit Tokens</div>
          </div>
          <div class="pw-rows">
            <div class="arow">
              <div class="l">@avUSDC@<div><div class="nm">USDC</div><div class="on">on Ethereum</div></div></div>
              <div class="r"><div class="amt">6.74 USDC</div><div class="usd">$6.74</div></div>
            </div>
            <div class="arow">
              <div class="l">@avOP@<div><div class="nm">ETH</div><div class="on">on Optimism</div></div></div>
              <div class="r"><div class="amt">0.0048 ETH</div><div class="usd">$11.90</div></div>
            </div>
            <div class="arow">
              <div class="l">@avMEGA@<div><div class="nm">ETH</div><div class="on">on MegaETH</div></div></div>
              <div class="r"><div class="amt">0.00055 ETH</div><div class="usd">$1.36</div></div>
            </div>
          </div>
        </div>
      </div>

      <div class="card soft">
        <div class="fees"><div class="k">Fees <i>(Estimated)</i></div>
          <div class="v"><span class="tnum">$0.10</span>@chevDsm@</div></div>
      </div>

      <div class="pfoot"><button class="cta primary" id="deposit-cta">Deposit Now</button></div>
    </section>

    <!-- ================= 3 + 4 · BET CARD (review / placing) ================= -->
    <section class="screen" data-name="Bet" id="s-bet">
      <div class="ocard">
        <div class="mkt">
          <div class="mkt-tile">@citreaTile@</div>
          <div>
            <div class="mkt-q">Will BTC close above $120,000 in 2026?</div>
            <div class="mkt-meta">Citrea Markets &middot; $2.4M Vol.</div>
          </div>
        </div>
        <div class="hair"></div>
        <div class="obtabs">
          <div class="ot sel"><div class="t">Buy</div><div class="u"></div></div>
          <div class="ot"><div class="t">Sell</div><div class="u"></div></div>
        </div>
        <div class="hair"></div>
        <div class="trade">
          <div class="yn">
            <div class="tile" id="tile-yes"><span class="nm">Yes</span><span class="pr">20&cent;</span></div>
            <div class="tile" id="tile-no"><span class="nm">No</span><span class="pr">83&cent;</span></div>
          </div>
          <div class="amtgrp">
            <div class="amt-head">
              <div class="amt-lbl">Amount</div>
              <div class="bal" id="bet-bal">Balance 20.00 ctUSD</div>
            </div>
            <div class="stepper">
              <div class="st-btn">@minusSm@</div>
              <div class="st-val tnum" id="stake">0</div>
              <div class="st-btn">@plusSm@</div>
            </div>
          </div>
          <div class="qa">
            <div class="qchip" id="q10">$10</div><div class="qchip" id="q25">$25</div>
            <div class="qchip" id="q50">$50</div><div class="qchip" id="qmax">MAX</div>
          </div>
        </div>
        <div class="hair"></div>
        <div class="summary dim" id="summary">
          <div class="srow"><div class="slbl" id="sh-lbl">Shares</div><div class="sv" id="sh-val">&mdash;</div></div>
          <div class="srow total"><div class="slbl">Total cost</div><div class="sv" id="tc-val">&mdash;</div></div>
          <div class="srow win"><div class="slbl">To win <i class="pct" id="pct">+16%</i></div><div class="sv" id="win-val">&mdash;</div></div>
        </div>
      </div>
      <div class="pfoot"><button class="cta disabled" id="bet-cta">Select an outcome</button></div>
    </section>

    <!-- ================= 5 · BET PLACED ================= -->
    <section class="screen" data-name="Bet placed" id="s-placed">
      <div class="stagger" style="display:flex;flex-direction:column;gap:16px;padding-top:4px">
        <div class="card soft">
          <div class="ok-card">
            <div class="ok-mark">@bigTick@</div>
            <div class="ok-t">
              <div class="ok-h">Bet placed</div>
              <div class="ok-s">BTC above $120k &middot; Dec 2026</div>
            </div>
          </div>
        </div>
        <div class="card soft">
          <div class="pos">
            <div class="srow"><div class="slbl">Position</div>
              <div class="pos-val"><span class="pos-pill">No</span><span class="tnum" id="pos-sh">24.09</span>&nbsp;shares</div></div>
            <div class="srow"><div class="slbl">Avg price</div><div class="sv">83&cent;</div></div>
            <div class="srow total"><div class="slbl">Total cost</div><div class="sv tnum">20.00 ctUSD</div></div>
            <div class="hair" style="margin-top:2px"></div>
            <div class="srow win"><div class="slbl">To win <i class="pct">+16%</i></div>
              <div class="sv tnum" style="color:#1E7A42">$23.26</div></div>
          </div>
        </div>
      </div>
      <div class="pfoot"><button class="cta primary" id="placed-cta">View my position</button></div>
    </section>

    <div class="fake-cursor" id="democursor"><div class="cur-inner">
      <svg width="26" height="26" viewBox="0 0 24 24"><path d="M5 2.5L18.5 9.8L12.2 11.6L9.2 17.8L5 2.5Z" fill="#1c1c1c" stroke="#fff" stroke-width="1.3" stroke-linejoin="round"/></svg>
    </div></div>

  </div>
</div>
"""

SCRIPT = r"""
/* ---------- inline SVG assets ---------- */
const SVG = {
  close:`<svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 4L12 12M12 4L4 12" fill="none" stroke="#161615" stroke-width="1.4" stroke-linecap="round"/></svg>`,
  refresh:`<svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 4V8L10.5 9.5" fill="none" stroke="#161615" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 8C14 11.314 11.314 14 8 14C4.686 14 2 11.314 2 8C2 4.686 4.686 2 8 2C10.196 2 12.117 3.179 13.163 4.936" fill="none" stroke="#161615" stroke-width="1.4" stroke-linecap="round"/><path d="M13.5 2V5H10.5" fill="none" stroke="#161615" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  eye:`<svg width="15" height="15" viewBox="0 0 16 16"><path d="M1.8 8C1.8 8 4.3 3.8 8 3.8C11.7 3.8 14.2 8 14.2 8C14.2 8 11.7 12.2 8 12.2C4.3 12.2 1.8 8 1.8 8Z" fill="none" stroke="#848483" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 9.9C9.05 9.9 9.9 9.05 9.9 8C9.9 6.95 9.05 6.1 8 6.1C6.95 6.1 6.1 6.95 6.1 8C6.1 9.05 6.95 9.9 8 9.9Z" fill="none" stroke="#848483" stroke-width="1.3"/></svg>`,
  swap:`<svg width="14" height="14" viewBox="0 0 16 16"><path d="M4.5 2.5V13M4.5 2.5L2.2 5M4.5 2.5L6.8 5M11.5 13.5V3M11.5 13.5L9.2 11M11.5 13.5L13.8 11" fill="none" stroke="#848483" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  chevDsm:`<svg width="14" height="14" viewBox="0 0 14 14"><path d="M4 5.5L7 8.5L10 5.5" fill="none" stroke="#848483" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  minusSm:`<svg width="12" height="12" viewBox="0 0 12 12"><path d="M1.2 6H10.8" fill="none" stroke="#5B5B5A" stroke-width="1.6" stroke-linecap="round"/></svg>`,
  plusSm:`<svg width="12" height="12" viewBox="0 0 12 12"><path d="M6 1.2V10.8M1.2 6H10.8" fill="none" stroke="#5B5B5A" stroke-width="1.6" stroke-linecap="round"/></svg>`,
  bigTick:`<svg width="30" height="30" viewBox="0 0 30 30"><path d="M8 15.5L13 20.5L22 10.5" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  megaeth:`<svg width="11" height="11" viewBox="0 0 32 32"><path d="M19.125 24.878C20.108 24.878 20.901 24.085 20.901 23.107C20.901 22.129 20.108 21.335 19.125 21.335C18.15 21.335 17.356 22.129 17.356 23.107C17.356 24.085 18.15 24.878 19.125 24.878Z" fill="#19191A"/><path d="M12.759 24.931C13.742 24.931 14.528 24.138 14.528 23.16C14.528 22.181 13.742 21.388 12.759 21.388C11.784 21.388 10.99 22.181 10.99 23.16C10.99 24.138 11.784 24.931 12.759 24.931Z" fill="#19191A"/><path d="M8.88 6.424H13.1C13.895 8.573 15.967 14.66 16.118 14.999C16.156 14.829 18.243 8.196 18.833 6.462H23.22V21.595C22.675 21.293 22.131 20.992 21.541 20.653C21.132 20.445 20.754 20.219 20.338 20.049C20.3 17.11 20.263 14.188 20.172 11.136C19.582 12.888 17.547 19.07 17.381 19.239H14.666C14.666 19.239 12.026 11.739 11.898 11.399C11.86 14.283 11.822 17.166 11.724 20.144C10.105 20.973 9.145 21.444 8.842 21.557V6.424H8.88Z" fill="#19191A"/><path d="M16.004 2.544C23.408 2.544 29.459 8.575 29.459 16C29.459 23.425 23.431 29.456 16.004 29.456C8.577 29.456 2.549 23.425 2.549 16C2.549 8.575 8.577 2.544 16.004 2.544ZM16.004 0C7.162 0 0 7.161 0 16C0 24.839 7.162 32 16.004 32C24.838 32 32 24.839 32 16C32 7.161 24.838 0 16.004 0Z" fill="#19191A"/></svg>`,
};

/* real brand assets, inlined base64 (see build-prediction.py) */
const IMG = {__IMG__};
const mark = (k,sz) => `<img src="${IMG[k]}" width="${sz}" height="${sz}" style="display:block;border-radius:999px" alt=""/>`;
const av34 = (coin, badge) => `<div class="av34">${mark(coin,34)}<span class="bd">${badge}</span></div>`;

const MAP = {
  close:SVG.close, refresh:SVG.refresh, eye:SVG.eye, swap:SVG.swap, chevDsm:SVG.chevDsm,
  minusSm:SVG.minusSm, plusSm:SVG.plusSm, bigTick:SVG.bigTick,
  citreaTile:`<img src="${IMG.citrea}" alt=""/>`,
  ctusdPill:`<div class="av22">${mark('ctusd',22)}<span class="bd"><img src="${IMG.ctbadge}" alt=""/></span></div>`,
  avUSDC: av34('usdc', mark('eth',14)),
  avOP:   av34('eth',  mark('optimism',14)),
  avMEGA: av34('eth',  SVG.megaeth),
};
document.querySelectorAll('.screen').forEach(scope=>{
  scope.innerHTML = scope.innerHTML.replace(/@(\w+)@/g, (m,k)=> MAP[k] ?? m);
});

/* ============================================================
   Bet-card state.
   The three tabs are chapters, not three DOM screens: the card recalculates
   in place when an outcome is tapped, because that is a decision resolving,
   not a cut to somewhere else.
   ============================================================ */
const PRICE = { yes:0.20, no:0.83 };
/* The artboards put 24.09 shares against a $23.26 payout - the 0.83 gap is the
   market fee, and it is the same rate at any stake. Deriving the payout from
   it keeps every amount agreeing with the $20 card the flow actually runs on. */
const NET   = 23.26 / 24.09;
const BAL   = 20.00;                      // ctUSD, after the deposit in Fund
const CARD  = { side:null, amt:0 };
const trunc2 = x => Math.floor(x*100)/100;   // shares: 24.09, not 24.10
const round2 = x => Math.round(x*100)/100;   // payout: same rate at every stake
const f2 = x => x.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const el = id => document.getElementById(id);

/* Each number remembers what it last showed so a change is counted, not cut. */
const LAST = {};
function anim(id,to,dur,fmt){
  const node = el(id); if(!node) return;
  const from = (id in LAST) ? LAST[id] : null;
  LAST[id] = to;
  if(!dur || from===null || from===to){ node.textContent = fmt(to); return; }
  const t0 = performance.now();
  (function tick(now){
    const p = Math.min(1,(now-t0)/dur), e = 1-Math.pow(1-p,3);
    node.textContent = fmt(from+(to-from)*e);
    if(p<1) requestAnimationFrame(tick);
  })(t0);
}
const asMoney = suf => v => f2(v)+suf;
const asInt   = () => v => String(Math.round(v));

function calc(){
  const p  = PRICE[CARD.side] || 1;
  const sh = trunc2(CARD.amt / p);
  const win = round2(sh * NET);
  return { sh, win, pct:Math.round((win/CARD.amt-1)*100) };
}
function renderNumbers(dur){
  const sum = el('summary');
  el('tile-yes').classList.toggle('on', CARD.side==='yes');
  el('tile-no').classList.toggle('on', CARD.side==='no');
  if(!CARD.side || !CARD.amt){
    sum.classList.add('dim');
    ['sh-val','tc-val','win-val'].forEach(id=>{ delete LAST[id]; el(id).textContent='—'; });
    el('sh-lbl').textContent = 'Shares';
    return;
  }
  sum.classList.remove('dim');
  const c = calc();
  el('sh-lbl').textContent = 'Shares at ' + Math.round(PRICE[CARD.side]*100) + '¢';
  anim('sh-val',  c.sh,       dur, asMoney(''));
  anim('tc-val',  CARD.amt,   dur, asMoney(' ctUSD'));
  anim('win-val', c.win,      dur, v => '$'+f2(v));
  el('pct').textContent = '+' + c.pct + '%';
}
function renderCta(){
  const cta = el('bet-cta');
  if(!CARD.side){ cta.className='cta disabled'; cta.textContent='Select an outcome'; return; }
  if(!CARD.amt){ cta.className='cta disabled'; cta.textContent='Enter an amount'; return; }
  cta.className='cta primary'; cta.textContent='Cast bet';
}
function setPlacing(on){
  const cta = el('bet-cta');
  if(on){ cta.className='cta placing'; cta.innerHTML='<span class="spin w"></span>Placing bet…'; }
  else renderCta();
}
function setChip(id){
  document.querySelectorAll('.qchip').forEach(c=>c.classList.toggle('on', c.id===id));
}
function pickSide(side,instant){
  CARD.side = side;
  const t = el('tile-'+side);
  if(!instant){ t.classList.add('pick'); setTimeout(()=>t.classList.remove('pick'),190); }
  renderNumbers(instant ? 0 : 620);
}
function setAmt(n,dur){
  CARD.amt = n;
  anim('stake', n, dur, asInt());
  renderNumbers(dur);
}
function resetBet(){
  CARD.side=null; CARD.amt=0;
  Object.keys(LAST).forEach(k=>delete LAST[k]);
  setChip(null); el('stake').textContent='0'; LAST['stake']=0;
  el('bet-bal').textContent = 'Balance ' + f2(BAL) + ' ctUSD';
  renderNumbers(0); renderCta();
}
/* the wallet balance, which Fund fills in */
function setWallet(v,dur){
  anim('wal-big', v, dur, x => '$'+f2(x));
  anim('wal-sub', v, dur, x => f2(x)+' ctUSD on Citrea');
}

/* ---------- confetti (bet placed) ---------- */
let confettiTimers=[];
function burstConfetti(){
  confettiTimers.forEach(clearTimeout);confettiTimers=[];
  const host=document.getElementById('device');
  const colors=['#12AD59','#006BF4','#1f82ff','#8FD6A9','#FFC94D','#ffffff'];
  const N=46;
  for(let i=0;i<N;i++){
    const p=document.createElement('div');
    p.className='confetti-piece';
    const ang=(i/N)*Math.PI*2+(i%3)*0.5, dist=70+((i*53)%160);
    const tx=Math.cos(ang)*dist, ty=120+((i*37)%280), rot=360+((i*97)%1000), dur=1100+((i%5)*130);
    p.style.background=colors[i%colors.length];
    if(i%2) p.style.borderRadius='999px';
    host.appendChild(p);
    p.animate([{opacity:1,transform:'translate(-50%,-50%) rotate(0deg)'},
               {opacity:1,offset:0.75},
               {opacity:0,transform:`translate(${tx.toFixed(0)}px, ${ty}px) rotate(${rot}deg)`}],
              {duration:dur,delay:(i%6)*24,easing:'cubic-bezier(.2,.6,.5,1)',fill:'forwards'});
    confettiTimers.push(setTimeout(()=>p.remove(),dur+500));
  }
}

/* ============ router ============ */
const ORDER=['s-wallet','s-deposit','s-bet','s-placed'];
let idx=0;
function setScreen(i){
  const cur=document.querySelector('.screen.active');
  const nextEl=document.getElementById(ORDER[i]);
  if(cur===nextEl){enter(nextEl,i);return;}
  if(cur){cur.classList.add('leaving');cur.classList.remove('active');
    setTimeout(()=>cur.classList.remove('leaving'),380);}
  requestAnimationFrame(()=>{
    document.querySelectorAll('.screen.active').forEach(s=>{ if(s!==nextEl) s.classList.remove('active'); });
    nextEl.classList.remove('leaving'); nextEl.classList.add('active');
    enter(nextEl,i);
  });
}
function sizeDevice(){
  const active=document.querySelector('.screen.active');
  if(active) document.getElementById('device').style.height = active.offsetHeight+'px';
}
const screenRO=new ResizeObserver(()=>requestAnimationFrame(sizeDevice));
document.querySelectorAll('.screen').forEach(e=>screenRO.observe(e));
function enter(node,i){
  requestAnimationFrame(sizeDevice);
  if(node.id==='s-placed'){ anim('pos-sh',24.09,900,f2); burstConfetti(); }
}
function navTo(id){ idx=ORDER.indexOf(id); setScreen(idx); }

/* ============ demo cursor ============ */
let demoTimers=[];
const cursorEl=()=>document.getElementById('democursor');
const deviceEl=()=>document.getElementById('device');
function clearDemoTimers(){ demoTimers.forEach(clearTimeout); demoTimers=[]; }
function hideCursor(){ const c=cursorEl(); if(c) c.style.opacity='0'; }
function sleep(ms){ return new Promise(res=>{ demoTimers.push(setTimeout(res,ms)); }); }
function snapCursor(x,y){ const c=cursorEl(); c.style.transition='none'; c.style.transform=`translate(${x}px,${y}px)`; c.style.opacity='0'; void c.offsetHeight; }
function moveCursorTo(node,opts){
  opts=opts||{};
  const dur=opts.dur||950;
  return new Promise(res=>{
    const c=cursorEl(); if(!c||!node){res();return;}
    /* Offsets, not rects: the stage is translated and scaled mid-transition. */
    const dev0=deviceEl(); let x=0,y=0;
    for(let n=node;n&&n!==dev0;n=n.offsetParent){ x+=n.offsetLeft; y+=n.offsetTop; }
    x+=node.offsetWidth/2; y+=node.offsetHeight/2;
    c.style.opacity='1';
    c.style.transition=`opacity .3s ease, transform ${dur}ms cubic-bezier(.5,1.35,.5,1)`;
    c.style.transform=`translate(${x-4}px, ${y-3}px)`;
    demoTimers.push(setTimeout(res,dur));
  });
}
function cursorTapFx(){
  const c=cursorEl(), inner=c.querySelector('.cur-inner');
  inner.classList.add('click'); setTimeout(()=>inner.classList.remove('click'),320);
  const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(c.style.transform);
  if(m){ const rip=document.createElement('div'); rip.className='tap-ripple';
    rip.style.left=(+m[1]+4)+'px'; rip.style.top=(+m[2]+3)+'px'; deviceEl().appendChild(rip);
    requestAnimationFrame(()=>rip.classList.add('go')); setTimeout(()=>rip.remove(),550); }
}
"""

RUNNER = r"""
/* ============================================================
   Segment player — three chapters, Fund / Predict / Trade.
     fund    : empty wallet -> deposit, route resolved -> wallet funded
     predict : pick No, size the bet off the balance, review it
     trade   : cast it, watch it place, own the position
   Predict continues straight out of a screen Fund never showed, and Trade
   continues the very card Predict ends on - so Trade is recorded without an
   opening rise (intro=0) and the other two keep theirs.
   ============================================================ */
(function(){
  const P = new URLSearchParams(location.search);
  const SEG = P.get('seg') || 'fund';

  const SW = +(P.get('sw') || 821), SH = +(P.get('sh') || 537);
  const ZOOM = +(P.get('zoom') || 1);
  const r = document.documentElement.style;
  r.setProperty('--sw', SW+'px'); r.setProperty('--sh', SH+'px');
  r.setProperty('--zoom', String(ZOOM));
  const PA = Math.max(0, Math.min(1, parseFloat(P.get('plate') || '1')));
  r.setProperty('--plate', String(PA));
  const sa = v => (v*PA).toFixed(3);
  r.setProperty('--strokeA', P.get('stroke') || String(PA));
  r.setProperty('--plateShadow',
    `0 40px 80px -30px rgba(20,20,20,${sa(0.35)}),`+
    `0 8px 30px -12px rgba(20,20,20,${sa(0.22)}),`+
    `0 0 0 1px rgba(20,20,20,${sa(0.04)})`);

  const stage = document.querySelector('.stage');
  const vs = document.createElement('div'); vs.id='vstage';
  const bg = document.createElement('img'); bg.id='vbg';
  bg.src = P.get('bg') || 'flow-bg@3x.png'; bg.alt='';
  stage.parentNode.insertBefore(vs, stage);
  vs.appendChild(bg); vs.appendChild(stage);

  const ALL = ['s-wallet','s-deposit','s-bet','s-placed'];
  function measure(){
    const h={};
    ALL.forEach(id=>{
      const node=document.getElementById(id), prev=node.className;
      node.className='screen active'; node.style.visibility='hidden';
      h[id]=node.offsetHeight;
      node.style.visibility=''; node.className=prev;
    });
    return h;
  }
  const H = measure();
  window.__screenHeights = H;

  /* Each screen is sized to its own height, not to the film's tallest.
     One shared scale meant the 661px Deposit screen pinned every other screen
     to 0.75, and the Wallet card - 450x304 - read small against an 821x537
     panel: 41% of its width. Per screen it lands at Wallet/Placed 1, Bet .84,
     Deposit .75 (the one screen that genuinely cannot fit any larger).
     The cap is 1 rather than the old 393/450: the widget is drawn at its
     design size and never above it.
     The resize is not a separate move - .stage carries its own
     `transition: transform .44s`, which runs on the same beat as the screen
     swap's blur and scale, so the card changes size as part of the cut. */
  const PAD  = 22;
  const fit  = h => Math.min(1, (SH-PAD*2)/(h||1));
  let curScale = fit(H['s-wallet']);
  function applyScale(h){ curScale = fit(h); r.setProperty('--devScale', String(curScale)); }
  applyScale(H['s-wallet']);
  window.__devScale = () => curScale;

  const _sizeDevice = sizeDevice;
  sizeDevice = function(){
    _sizeDevice();
    const a = document.querySelector('.screen.active');
    if(a) applyScale(a.offsetHeight);
  };

  const q = s => document.querySelector(s);
  let run = 0;
  const alive = t => t === run;
  async function tap(node,opts){
    if(!node) return;
    await moveCursorTo(node,opts);
    cursorTapFx();
    await sleep(300);
  }

  async function segFund(t){
    resetBet(); setWallet(0,0); navTo('s-wallet');
    snapCursor(300,430); await sleep(900); if(!alive(t))return;
    await tap(q('#wallet-cta')); if(!alive(t))return;
    hideCursor(); navTo('s-deposit'); await sleep(2600); if(!alive(t))return;
    await tap(q('#deposit-cta'),{dur:800}); if(!alive(t))return;
    hideCursor(); navTo('s-wallet'); await sleep(260);
    setWallet(20,1100); await sleep(3000);
  }

  async function segPredict(t){
    resetBet(); navTo('s-bet');
    snapCursor(300,470); await sleep(820); if(!alive(t))return;
    await tap(q('#tile-no')); if(!alive(t))return;
    pickSide('no'); renderCta(); await sleep(900); if(!alive(t))return;
    await tap(q('#qmax'),{dur:800}); if(!alive(t))return;
    setChip('qmax'); setAmt(20,620); renderCta(); await sleep(1500); if(!alive(t))return;
    hideCursor(); await sleep(2200);
  }

  async function segTrade(t){
    resetBet(); pickSide('no',true); setChip('qmax'); setAmt(20,0); renderCta();
    navTo('s-bet');
    snapCursor(300,470); await sleep(760); if(!alive(t))return;
    await tap(q('#bet-cta'),{dur:780}); if(!alive(t))return;
    hideCursor(); setPlacing(true); await sleep(2300); if(!alive(t))return;
    setPlacing(false);
    navTo('s-placed'); await sleep(4200);
  }

  async function segFull(t){
    await segFund(t);    if(!alive(t)) return;
    await segPredict(t); if(!alive(t)) return;
    await segTrade(t);
  }

  const SCRIPTS = { fund:segFund, predict:segPredict, trade:segTrade, full:segFull };

  /* The opening rise belongs to a chapter that starts somewhere new. Trade
     continues the exact card Predict ends on, so it is recorded with intro=0
     and that join stays invisible. */
  const WANT_INTRO = P.get('intro') !== '0';
  function armIntro(){
    if(!WANT_INTRO) return;
    const v=document.getElementById('vstage'); if(v) v.classList.add('intro');
  }
  window.__armIntro = armIntro;
  function playIntro(){
    const v=document.getElementById('vstage');
    if(!v || !v.classList.contains('intro')) return Promise.resolve();
    const st=v.querySelector('.stage');
    return new Promise(res=>{
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        st.style.transition='transform .8s var(--ease-spring)';
        v.classList.remove('intro');
        demoTimers.push(setTimeout(()=>{ st.style.transition=''; res(); },860));
      }));
    });
  }

  async function loop(){
    const t = ++run;
    while(alive(t)){
      await playIntro(); if(!alive(t)) break;
      await (SCRIPTS[SEG] || segFund)(t);
      if(!alive(t)) break;
      window.__cycle = (window.__cycle||0)+1;
      await sleep(260);
    }
  }

  // Park on the chapter's opening screen, in its opening state.
  const FIRST = { fund:'s-wallet', predict:'s-bet', trade:'s-bet', full:'s-wallet' };
  hideCursor();
  resetBet();
  if(SEG==='fund'||SEG==='full') setWallet(0,0);
  if(SEG==='trade'){ pickSide('no',true); setChip('qmax'); setAmt(20,0); renderCta(); }
  navTo(FIRST[SEG] || 's-wallet');
  if(P.has('hold')) requestAnimationFrame(armIntro);

  window.__startSegment = () => { window.__cycle = 0; loop(); };
  if(!P.has('hold')) window.__startSegment();
})();
"""

# ---- assemble ---------------------------------------------------------------
IMG_JS = ',\n'.join(f'{k}:"{v}"' for k, v in COINS.items())

OUT = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Nexus One &middot; Fund / Predict / Trade &mdash; Prototype</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
<!-- GENERATED FILE - edit flow/build-prediction.py, not this. -->
<style>
{STYLES}
</style>
<style id="prediction">
{PRED_CSS}
</style>
<style id="player-override">
{OVERRIDE}
</style>
</head>
<body>
{BODY}
<script>
{SCRIPT.replace('__IMG__', IMG_JS)}
</script>
<script id="player-runner">
{RUNNER}
</script>
</body>
</html>
"""

with open(DST, 'w', encoding='utf-8') as fh:
    fh.write(OUT)
print(f'wrote {os.path.relpath(DST, os.path.dirname(ROOT))} '
      f'({os.path.getsize(DST)/1024:.0f} KB)')
