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
PANEL_W, PANEL_H = 821, 537
ZOOM     = 2
FPS      = 30
CHROME   = ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

URL = (f'{SERVE}/flow/player.html?seg={SEG}&hold=1'
       f'&sw={PANEL_W}&sh={PANEL_H}&zoom={ZOOM}')


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
        '--autoplay-policy=no-user-gesture-required',
        '--hide-scrollbars',
        URL,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws_url = None
    for _ in range(80):
        try:
            for t in cdp_targets():
                if t.get('type') == 'page' and 'player.html' in t.get('url', ''):
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
            'format': 'png', 'everyNthFrame': 1,
            'maxWidth': PANEL_W * ZOOM, 'maxHeight': PANEL_H * ZOOM,
        })
        await asyncio.sleep(.4)
        await evaluate('window.__startSegment()')
        start_ts = frames[-1][0] if frames else 0

        t0 = time.time()
        while time.time() - t0 < 30:
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
        with open(os.path.join(frames_dir, f'f{i:05d}.png'), 'wb') as fh:
            fh.write(base64.b64decode(data))
    span = frames[-1][0] - base
    listing = []
    for i, (ts, _) in enumerate(frames):
        nxt = frames[i + 1][0] if i + 1 < len(frames) else ts + 1 / FPS
        listing.append(f"file 'f{i:05d}.png'\nduration {max(nxt - ts, 1/120):.4f}")
    listing.append(f"file 'f{len(frames)-1:05d}.png'")
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

    # poster: frame 0, so the still under prefers-reduced-motion is the state
    # the clip opens on rather than its end. Homebrew ffmpeg here has no
    # libwebp, so Pillow writes it.
    from PIL import Image
    Image.open(os.path.join(frames_dir, 'f00000.png')).convert('RGB').save(
        os.path.join(OUT, f'{SEG}.webp'), 'WEBP', quality=82, method=6)
    print('wrote', f'assets/flow/{SEG}.webp')
    shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == '__main__':
    asyncio.run(main())
