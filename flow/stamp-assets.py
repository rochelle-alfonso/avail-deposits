#!/usr/bin/env python3
"""Re-stamp the ?v= on every recorded asset a page references, from its mtime.

    python3 flow/stamp-assets.py

Why: the clips under assets/position/ are re-recorded constantly, and the
browser caches them by URL. A hand-maintained ?v=2 goes stale the moment the
next take lands, and a stale clip is indistinguishable from a change that
silently did not apply — which has now cost time twice. Deriving the stamp from
the file's own mtime means it can never disagree with what is on disk.

Run it after any re-record. Safe to run repeatedly; it rewrites in place and
reports only what actually moved.
"""
import os, re, sys

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ['index.html', os.path.join('prediction-markets', 'index.html')]
# only the recorded assets: styles.css and js are versioned by hand on purpose,
# since their stamp is a deliberate cache-break for visitors
PATTERN = re.compile(r'((?:\.\./)?assets/position/[A-Za-z0-9\-@]+\.(?:mp4|webp))(\?v=[0-9]+)?')


def stamp_for(url_path):
    rel = url_path.lstrip('./')
    while rel.startswith('../'):
        rel = rel[3:]
    full = os.path.join(ROOT, rel)
    if not os.path.exists(full):
        return None, full
    return str(int(os.path.getmtime(full))), full


def main():
    total, missing = 0, []
    for page in PAGES:
        p = os.path.join(ROOT, page)
        if not os.path.exists(p):
            continue
        src = open(p, encoding='utf-8').read()
        changed = []

        def repl(m):
            url, old = m.group(1), (m.group(2) or '')
            stamp, full = stamp_for(url)
            if stamp is None:
                missing.append(url)
                return m.group(0)
            new = '?v=' + stamp
            if new != old:
                changed.append(os.path.basename(url))
            return url + new

        out = PATTERN.sub(repl, src)
        if out != src:
            open(p, 'w', encoding='utf-8').write(out)
        total += len(changed)
        print('%-30s %s' % (page, ', '.join(sorted(set(changed))) or 'already current'))

    if missing:
        print('\nreferenced but not on disk:')
        for m in sorted(set(missing)):
            print('  ' + m)
        return 1
    print('\n%d reference(s) re-stamped' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main())
