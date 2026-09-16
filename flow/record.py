#!/usr/bin/env python3
"""Record one player.html segment to an mp4, the way the originals were cut.

    python3 flow/record.py steps

Drives a headful Chrome over CDP: lays the page out at 2x (?zoom=2) while the
capture itself stays at dpr 1, which is what keeps Page.startScreencast fast
enough to hold ~26fps. Frames carry their own timestamps, so the mp4 is built
from a concat list with real per-frame durations rather than an assumed rate.

Traps, all of them learned the hard way:
  * Emulation.setDeviceMetricsOverride does NOT raise the screencast's capture
    resolution - it pins frames to CSS-pixel size. Lay the page out larger.
  * --force-device-scale-factor works but the compositor throttles hard (3x
    drops capture to ~14fps).
  * Kill any Chrome already holding the debug port; attaching to a stale one
    silently gives you the old window's DPR.
"""
import asyncio, base64, json, os, shutil, subprocess, sys, time, urllib.request

SEG      = (sys.argv[1] if len(sys.argv) > 1 else 'steps')
ROOT     = os.path.dirname(os.path.abspath(__file__))
REPO     = os.path.dirname(ROOT)
OUT      = os.path.join(REPO, 'assets', 'flow')
PORT     = int(os.environ.get('CDP_PORT', '9222'))
SERVE    = os.environ.get('SERVE', 'http://127.0.0.1:8899')
# The Figma panel. PANEL_W is overridable because the prediction page runs a
# wider frame (1000) at the same height, so the card keeps its size and only
# the plate around it grows.
PANEL_W  = int(os.environ.get('PANEL_W', '821'))
PANEL_H  = int(os.environ.get('PANEL_H', '537'))
ZOOM     = 2
FPS      = 30
CHROME   = ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
# PLAYER selects which prototype to record: player.html for the deposit film,
# player-prediction.html for the funded-position one. OUTDIR keeps a second
# film's clips out of the first one's folder.
PLAYER   = os.environ.get('PLAYER', 'player.html')
OUT      = os.environ.get('OUTDIR', OUT)
# INTRO=0 records a segment without the opening rise, for a clip that continues
# from the previous one rather than starting the run.
INTRO    = os.environ.get('INTRO', '1')
# BG picks the plate the film is shot against — the player defaults to
# flow-bg@3x.png. The prediction page runs the same illustration as its hero,
# cropped to the panel: position-bg@3x.png.
BG       = os.environ.get('BG', '')
# Screencast JPEG quality. 95 is right for the deposit films; a frame that is
# wall-to-wall halftone costs far more to encode, and dropping this is the
# cheapest way to buy back capture rate there. The frames are re-encoded to
# h264 at crf 29 afterwards, so the intermediate loss barely survives anyway.
SHOT_Q   = int(os.environ.get('SHOT_Q', '95'))

URL = (f'{SERVE}/flow/{PLAYER}?seg={SEG}&hold=1&intro={INTRO}'
       f'&sw={PANEL_W}&sh={PANEL_H}&zoom={ZOOM}'
       + (f'&bg={BG}' if BG else ''))


def cdp_targets():
    with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json', timeout=5) as r:
        return json.load(r)


async def main():
    import websockets

    frames_dir = os.path.join(ROOT, '.frames')
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir)

    profile = os.path.join(ROOT, '.chrome-profile')
    shutil.rmtree(profile, ignore_errors=True)
    # Headless by default: a headful window is clamped to the desktop, and a
    # 1642x1074 viewport does not fit a 1512x982 logical display - Chrome then
    # scales the emulated viewport down and the screencast captures the scaled
    # surface, so the plate lands at ~80% inside a correctly-sized frame.
    # HEADLESS=0 to watch it run, but expect a smaller plate in the output.
    chrome = subprocess.Popen([
        CHROME,
        *(['--headless=new'] if os.environ.get('HEADLESS', '1') != '0' else []),
        f'--remote-debugging-port={PORT}',
        f'--user-data-dir={profile}',
        f'--window-size={PANEL_W * ZOOM},{PANEL_H * ZOOM}',
        '--window-position=0,0',
        '--no-first-run', '--no-default-browser-check',
        '--disable-features=Translate,MediaRouter',
        '--enable-gpu', '--use-angle=metal',
        '--autoplay-policy=no-user-gesture-required',
        '--hide-scrollbars',
        URL,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws_url = None
    for _ in range(80):
        try:
            for t in cdp_targets():
                if t.get('type') == 'page' and PLAYER in t.get('url', ''):
                    ws_url = t['webSocketDebuggerUrl']
                    break
        except Exception:
            pass
        if ws_url:
            break
        await asyncio.sleep(.25)
    if not ws_url:
        chrome.terminate()
        sys.exit('could not attach to the player tab')

    frames = []
    async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
        msg_id = 0
        pending = {}

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            fut = asyncio.get_running_loop().create_future()
            pending[msg_id] = fut
            await ws.send(json.dumps({'id': msg_id, 'method': method,
                                      'params': params or {}}))
            return await fut

        async def pump():
            async for raw in ws:
                m = json.loads(raw)
                if 'id' in m and m['id'] in pending:
                    pending.pop(m['id']).set_result(m.get('result', {}))
                elif m.get('method') == 'Page.screencastFrame':
                    p = m['params']
                    frames.append((p['metadata']['timestamp'], p['data']))
                    asyncio.create_task(send('Page.screencastFrameAck',
                                             {'sessionId': p['sessionId']}))

        pumper = asyncio.create_task(pump())
        await send('Page.enable')
        await send('Runtime.enable')

        # Pin the viewport to the panel's own pixel size at dpr 1. The trap is
        # reaching for this to get MORE pixels than CSS size - it will not do
        # that. Used to set the CSS viewport exactly, it is the reliable way to
        # get 1642x1074 frames without a window taller than the display.
        await send('Emulation.setDeviceMetricsOverride', {
            'width': PANEL_W * ZOOM, 'height': PANEL_H * ZOOM,
            'deviceScaleFactor': 1, 'mobile': False,
        })

        # let fonts, the heatmap clip and the artboard textures settle
        await asyncio.sleep(3.0)

        async def evaluate(expr):
            r = await send('Runtime.evaluate',
                           {'expression': expr, 'returnByValue': True})
            return r.get('result', {}).get('value')

        await send('Page.startScreencast', {
            'format': 'jpeg', 'quality': SHOT_Q, 'everyNthFrame': 1,
            'maxWidth': PANEL_W * ZOOM, 'maxHeight': PANEL_H * ZOOM,
        })
        await asyncio.sleep(.4)

        # The poster is the parked opening frame as a real png. The screen is
        # parked mid-entrance, so drop the from-state for the shot and put it
        # back - otherwise the poster is an empty plate.
        # Dropping .intro does not teleport the stage: #vstage .stage carries
        # `transition: transform .44s`, so it RIDES back up, and shooting on
        # the next round trip catches the card still below frame. Wait the
        # transition out (plus a beat) or the poster is a plate and a gradient.
        was_armed = await evaluate(
            "(() => { const v = document.getElementById('vstage');"
            "  const a = v.classList.contains('intro');"
            "  v.classList.remove('intro'); return a; })()")
        if was_armed:
            await asyncio.sleep(.65)
        poster = (await send('Page.captureScreenshot',
                             {'format': 'png'}))['data']
        # Only put it back if the page armed it in the first place. The four tab
        # clips have no entrance; re-arming unconditionally handed one to
        # whichever segment happened to be recording.
        if was_armed:
            await evaluate('window.__armIntro && window.__armIntro()')
        await asyncio.sleep(.15)
        # Stamp the trim point BEFORE starting, not after: evaluate() awaits a
        # CDP round trip, so by the time it returns the opening animation is
        # already underway and trimming to that instant eats the entrance.
        start_ts = frames[-1][0] if frames else 0
        await evaluate('window.__startSegment()')

        t0 = time.time()
        while time.time() - t0 < 120:   # `full` runs ~31s
            if await evaluate('window.__cycle || 0'):
                break
            await asyncio.sleep(.05)
        await asyncio.sleep(.15)
        await send('Page.stopScreencast')
        pumper.cancel()

    chrome.terminate()
    try:
        chrome.wait(timeout=10)
    except subprocess.TimeoutExpired:
        chrome.kill()
    shutil.rmtree(profile, ignore_errors=True)

    if len(frames) < 10:
        sys.exit(f'only captured {len(frames)} frames - is the segment running?')

    # drop the pre-roll frames of the parked first screen, then write the
    # concat list with each frame's real on-screen duration
    frames = [f for f in frames if f[0] >= start_ts] or frames
    base = frames[0][0]
    for i, (_, data) in enumerate(frames):
        with open(os.path.join(frames_dir, f'f{i:05d}.jpg'), 'wb') as fh:
            fh.write(base64.b64decode(data))
    with open(os.path.join(frames_dir, 'poster.png'), 'wb') as fh:
        fh.write(base64.b64decode(poster))
    span = frames[-1][0] - base
    listing = []
    for i, (ts, _) in enumerate(frames):
        nxt = frames[i + 1][0] if i + 1 < len(frames) else ts + 1 / FPS
        listing.append(f"file 'f{i:05d}.jpg'\nduration {max(nxt - ts, 1/120):.4f}")
    listing.append(f"file 'f{len(frames)-1:05d}.jpg'")
    with open(os.path.join(frames_dir, 'list.txt'), 'w') as fh:
        fh.write('\n'.join(listing) + '\n')

    print(f'{len(frames)} frames over {span:.2f}s '
          f'({len(frames)/span:.1f} fps captured)')

    # crf 29 with tune=stillimage lands on ~580 kbps for this content, which is
    # what the original cut shipped at. The page has a 1MB budget; do not drop
    # the crf without re-checking the total.
    def encode(dst, width=None, crf=29):
        vf = (f'fps={FPS},scale={width}:-2' if width
              else f'fps={FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2')
        subprocess.run([
            'ffmpeg', '-y', '-loglevel', 'error',
            '-f', 'concat', '-safe', '0',
            '-i', os.path.join(frames_dir, 'list.txt'),
            '-vf', vf, '-c:v', 'libx264', '-preset', 'slow',
            '-tune', 'stillimage', '-profile:v', 'high',
            '-pix_fmt', 'yuv420p', '-crf', str(crf),
            '-movflags', '+faststart', '-an', dst,
        ], check=True)
        print('wrote', os.path.relpath(dst, REPO),
              f'({os.path.getsize(dst)/1024:.0f} KB)')

    encode(os.path.join(OUT, f'{SEG}.mp4'))
    encode(os.path.join(OUT, f'{SEG}-sm.mp4'), 1280)

    # poster: the opening frame, so the still under prefers-reduced-motion is
    # the state the clip starts on rather than its end. Homebrew ffmpeg here
    # has no libwebp, so Pillow writes it.
    from PIL import Image
    Image.open(os.path.join(frames_dir, 'poster.png')).convert('RGB').save(
        os.path.join(OUT, f'{SEG}.webp'), 'WEBP', quality=82, method=6)
    print('wrote', os.path.relpath(os.path.join(OUT, f'{SEG}.webp'), REPO))
    shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == '__main__':
    asyncio.run(main())
