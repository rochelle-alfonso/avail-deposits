#!/usr/bin/env python3
"""Record a segment at an exact, uniform frame rate using CDP virtual time.

    python3 flow/record-smooth.py hero

Why this exists alongside record.py
-----------------------------------
record.py screencasts in real time: Chrome hands over whatever frames its
compositor manages to produce, and the mp4 is assembled from their real
timestamps. That is the right trade for the deposit films, which capture at
31-53fps. The hero does not get near that — its plate is wall-to-wall halftone
and the card carries a large soft shadow, so animation windows were sampling at
14-15fps however they were tuned. Measured, not guessed: pre-scaling the plate,
promoting it to its own layer and dropping JPEG quality all moved the number by
less than 2fps.

So this script stops sampling a clock it cannot keep up with, and drives one
instead. Virtual time is paused, then advanced in exact 1/FPS steps with a
screenshot taken at every step. Wall-clock render cost stops mattering: a frame
that takes 200ms to paint still lands on its exact 33.3ms mark. Output is
uniform by construction, so every frame is distinct and the motion is as smooth
as the CSS describes.

The cost is wall-clock time — a few hundred screenshots, one round trip each —
which is why this is a second script rather than record.py's default.

Env: FPS, PLAYER, OUTDIR, SERVE, CDP_PORT, PANEL_W, PANEL_H, BG, MAX_FRAMES.
"""
import asyncio, base64, json, os, shutil, subprocess, sys, time, urllib.request

SEG      = (sys.argv[1] if len(sys.argv) > 1 else 'hero')
ROOT     = os.path.dirname(os.path.abspath(__file__))
REPO     = os.path.dirname(ROOT)
PORT     = int(os.environ.get('CDP_PORT', '9333'))
SERVE    = os.environ.get('SERVE', 'http://127.0.0.1:8899')
PLAYER   = os.environ.get('PLAYER', 'hero.html')
OUT      = os.environ.get('OUTDIR', os.path.join(REPO, 'assets', 'position'))
PANEL_W  = int(os.environ.get('PANEL_W', '685'))
PANEL_H  = int(os.environ.get('PANEL_H', '593'))
ZOOM     = int(os.environ.get('ZOOM', '2'))
FPS      = int(os.environ.get('FPS', '30'))
BG       = os.environ.get('BG', '')
MAX_FRAMES = int(os.environ.get('MAX_FRAMES', '600'))
CHROME   = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

STEP_MS  = 1000.0 / FPS
# zoom=1: the page lays out at its natural 685x593 and Chrome renders it at
# deviceScaleFactor=ZOOM. Scaling the stage with a CSS transform instead would
# rasterise once at 1x and resample every frame, which shows up as the halftone
# plate shimmering between otherwise identical frames.
# cache-buster: the build artefact is regenerated between takes and a stale
# copy is indistinguishable from a broken page at the far end of a CDP session
URL = (f'{SERVE}/flow/{PLAYER}?rec=1&hold=1&cb={int(time.time())}'
       f'&sw={PANEL_W}&sh={PANEL_H}&zoom=1'
       + (f'&bg={BG}' if BG else ''))


def cdp_targets():
    with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json', timeout=5) as r:
        return json.load(r)


async def main():
    import websockets

    frames_dir = os.path.join(ROOT, '.frames')
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir)
    profile = os.path.join(ROOT, '.chrome-profile-smooth')
    shutil.rmtree(profile, ignore_errors=True)

    # Kill anything already holding the debug port. sys.exit() inside the CDP
    # session skips this script's own cleanup, so a failed take leaves a live
    # headless Chrome behind — and the next run attaches to THAT, silently
    # recording the previous build. Cost me three takes to spot.
    subprocess.run(['pkill', '-f', f'remote-debugging-port={PORT}'],
                   capture_output=True)
    time.sleep(1.0)

    chrome = subprocess.Popen([
        CHROME, '--headless=new',
        f'--remote-debugging-port={PORT}',
        f'--user-data-dir={profile}',
        f'--window-size={PANEL_W * ZOOM},{PANEL_H * ZOOM}',
        '--no-first-run', '--no-default-browser-check',
        '--disable-features=Translate,MediaRouter',
        '--enable-gpu', '--use-angle=metal',
        '--autoplay-policy=no-user-gesture-required',
        '--hide-scrollbars', URL,
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

    shots = []
    async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
        msg_id = 0
        pending = {}
        budget_expired = asyncio.Event()
        page_errors = []

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
                    fut = pending.pop(m['id'])
                    if not fut.done():
                        fut.set_result(m.get('result', {}))
                elif m.get('method') == 'Runtime.exceptionThrown':
                    d = m['params'].get('exceptionDetails', {})
                    page_errors.append(
                        (d.get('exception', {}) or {}).get('description')
                        or d.get('text') or json.dumps(d)[:300])
                elif m.get('method') == 'Runtime.consoleAPICalled':
                    if m['params'].get('type') in ('error', 'warning'):
                        page_errors.append('console: ' + json.dumps(
                            [a.get('value') for a in m['params'].get('args', [])])[:300])

        pumper = asyncio.create_task(pump())
        await send('Page.enable')
        await send('Runtime.enable')
        # Unlike the screencast, Page.captureScreenshot honours deviceScaleFactor,
        # so the frames come back at PANEL x ZOOM natively rendered rather than
        # upscaled from a 1x raster.
        await send('Emulation.setDeviceMetricsOverride', {
            'width': PANEL_W, 'height': PANEL_H,
            'deviceScaleFactor': ZOOM, 'mobile': False,
        })

        async def evaluate(expr):
            r = await send('Runtime.evaluate',
                           {'expression': expr, 'returnByValue': True})
            return r.get('result', {}).get('value')

        # Let fonts, the plate and the inlined marks land before the first frame,
        # or the opening frames come out half-dressed.
        for _ in range(80):
            ready = await evaluate(
                "(document.readyState==='complete') && "
                "!!document.querySelector('.hero-plate') && "
                "document.querySelector('.hero-plate').complete && "
                "document.fonts.status==='loaded'")
            if ready:
                break
            await asyncio.sleep(.25)
        await asyncio.sleep(1.0)

        async def shoot():
            r = await send('Page.captureScreenshot',
                           {'format': 'png', 'fromSurface': True,
                            'captureBeyondViewport': False})
            shots.append(r['data'])

        # The page renders any instant on demand, so the clock never enters into
        # it: ask for frame n's state, shoot it, ask for the next. Nothing can
        # drop, stutter or race, and re-running produces identical bytes.
        # readyState can report complete while the page's own script is still
        # executing, so wait for the timeline rather than assuming it is there.
        duration = None
        for _ in range(40):
            duration = await evaluate('window.__filmDuration || 0')
            if duration:
                break
            await asyncio.sleep(.25)
        if not duration:
            chrome.terminate()          # do not strand it for the next run
            sys.exit('page exposes no __filmDuration after 10s.\npage errors:\n  '
                     + ('\n  '.join(page_errors) if page_errors else '(none captured)'))
        await evaluate('window.__anchorForFilm && window.__anchorForFilm()')
        total = min(MAX_FRAMES, int(duration * FPS) + 1)
        print('film is %.2fs -> %d frames at %dfps' % (duration, total, FPS))

        for i in range(total):
            await evaluate('window.__renderFrame(%.5f)' % (i / FPS))
            await shoot()
            if i and i % 30 == 0:
                print('  %.1fs captured (%d frames)' % (i / FPS, i))

        pumper.cancel()

    chrome.terminate()
    try:
        chrome.wait(timeout=10)
    except subprocess.TimeoutExpired:
        chrome.kill()
    shutil.rmtree(profile, ignore_errors=True)

    if len(shots) < 10:
        sys.exit(f'only captured {len(shots)} frames — did the segment run?')


    for i, data in enumerate(shots):
        with open(os.path.join(frames_dir, f'f{i:05d}.png'), 'wb') as fh:
            fh.write(base64.b64decode(data))
    print(f'{len(shots)} frames at a uniform {FPS}fps '
          f'({len(shots)/FPS:.2f}s of film)')

    def encode(dst, width=None, crf=28):
        vf = f'scale={width}:-2' if width else 'scale=trunc(iw/2)*2:trunc(ih/2)*2'
        subprocess.run([
            'ffmpeg', '-y', '-loglevel', 'error',
            '-framerate', str(FPS), '-i', os.path.join(frames_dir, 'f%05d.png'),
            '-vf', vf, '-c:v', 'libx264', '-preset', 'slow',
            '-tune', 'stillimage', '-profile:v', 'high',
            '-pix_fmt', 'yuv420p', '-crf', str(crf),
            '-movflags', '+faststart', '-an', dst,
        ], check=True)
        print('wrote', os.path.relpath(dst, REPO),
              f'({os.path.getsize(dst)/1024:.0f} KB)')

    os.makedirs(OUT, exist_ok=True)
    encode(os.path.join(OUT, f'{SEG}.mp4'))
    encode(os.path.join(OUT, f'{SEG}-sm.mp4'), 1280)

    from PIL import Image
    Image.open(os.path.join(frames_dir, 'f00000.png')).convert('RGB').save(
        os.path.join(OUT, f'{SEG}.webp'), 'WEBP', quality=82, method=6)
    print('wrote', os.path.relpath(os.path.join(OUT, f'{SEG}.webp'), REPO))
    shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == '__main__':
    asyncio.run(main())
