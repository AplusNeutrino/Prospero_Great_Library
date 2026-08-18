#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

REQUIRED_VARS = (
    '--main-bg',
    '--main-border-color',
    '--text-color',
    '--text-muted-color',
    '--heading-color',
    '--link-color',
    '--card-bg',
    '--card-shadow',
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('theme_dir')
    ap.add_argument('--adapter-css', default='jekyll/assets/pgl/pgl-chirpy.css')
    args = ap.parse_args()
    theme = Path(args.theme_dir)
    adapter = Path(args.adapter_css)
    light = theme / '_sass' / 'themes' / '_light.scss'
    dark = theme / '_sass' / 'themes' / '_dark.scss'
    if not light.exists() or not dark.exists():
        raise SystemExit(f'Chirpy theme files not found under {theme}')
    adapter_text = adapter.read_text(encoding='utf-8', errors='replace')
    failures = []
    for path in (light, dark):
        text = path.read_text(encoding='utf-8', errors='replace')
        for var in REQUIRED_VARS:
            if var not in text:
                failures.append(f'{path.name} missing {var}')
    for var in REQUIRED_VARS:
        if var not in adapter_text:
            failures.append(f'PGL adapter does not reference {var}')
    if failures:
        raise SystemExit('theme contract failure:\n- ' + '\n- '.join(failures))
    print(f'Chirpy theme-variable contract PASS: {theme}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
