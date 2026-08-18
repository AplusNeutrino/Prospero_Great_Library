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
        'class="pgl-header"',
        'class="pgl-category-ledger"',
        'id="pgl-rating-chart"',
        'id="pgl-browser-view"',
        '/assets/pgl/pgl.css',
        '/assets/pgl/pgl-chirpy.css',
        '/assets/pgl/pgl.js',
        'data-library-url=',
        'data-stats-url=',
        'data-history-manifest=',
    ]
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit('built library contract missing: ' + ', '.join(missing))
    forbidden = ['id="pgl-load-more"', 'limit: 60', 'Steam lifetime ranking']
    found = [needle for needle in forbidden if needle in text]
    if found:
        raise SystemExit('built library contains deprecated alpha.3 UI: ' + ', '.join(found))
    # alpha.4 deliberately avoids rendering a cross-category fallback card feed.
    if 'class="pgl-card"' in text:
        raise SystemExit('root Library page unexpectedly contains mixed server-rendered catalogue cards')
    for rel in ('assets/pgl/pgl.css', 'assets/pgl/pgl-chirpy.css', 'assets/pgl/pgl.js'):
        if not (site / rel).exists():
            raise SystemExit(f'missing built asset: {rel}')
    print(f'PGL alpha.4 built-page smoke PASS: {page}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
