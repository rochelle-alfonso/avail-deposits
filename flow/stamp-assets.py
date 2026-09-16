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
# The configurator is embedded as an iframe and carries its own query string, so
# it needs the stamp appended rather than substituted. It is a build artefact
# that changes as often as the clips do, and a stale iframe is just as
# invisible — it cost a round of "the token still says USDT0".
IFRAME = re.compile(r'((?:\.\./)?flow/[A-Za-z0-9\-]+\.html\?[^"\s]*?)(&amp;v=[0-9]+)?(?=")')


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

        def repl_iframe(m):
            url, old_stamp = m.group(1), (m.group(2) or '')
            path = url.split('?')[0]
            stamp, full = stamp_for(path)
            if stamp is None:
                missing.append(path)
                return m.group(0)
            new_stamp = '&amp;v=' + stamp
            if new_stamp != old_stamp:
                changed.append(os.path.basename(path))
            return url + new_stamp

        out = IFRAME.sub(repl_iframe, PATTERN.sub(repl, src))
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
