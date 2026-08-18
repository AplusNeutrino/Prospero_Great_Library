#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('site_dir')
    args = ap.parse_args()
    site = Path(args.site_dir)
    page = site / 'library' / 'index.html'
    if not page.exists():
        raise SystemExit(f'missing built library page: {page}')
    text = page.read_text(encoding='utf-8', errors='replace')
    required = [
        'id="prospero-great-library"',
        'class="pgl-card"',
        '/assets/pgl/pgl.css',
        '/assets/pgl/pgl-chirpy.css',
        '/assets/pgl/pgl.js',
        'data-library-url=',
        'data-history-manifest=',
    ]
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit('built library contract missing: ' + ', '.join(missing))
    count = text.count('class="pgl-card"')
    if count < 1:
        raise SystemExit('built library contains no server-rendered fallback cards')
    if count > 60:
        raise SystemExit(f'lazy-render fallback unexpectedly contains {count} cards (>60)')
    for rel in ('assets/pgl/pgl.css', 'assets/pgl/pgl-chirpy.css', 'assets/pgl/pgl.js'):
        if not (site / rel).exists():
            raise SystemExit(f'missing built asset: {rel}')
    print(f'PGL built-page smoke PASS: {page} ({count} fallback cards)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
