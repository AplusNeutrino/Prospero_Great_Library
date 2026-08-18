#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'pgl' / 'resources' / 'chirpy'


def copy_tree_files(source: Path, dest: Path, pattern: str = '*') -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob('*'):
        if old.is_file():
            old.unlink()
    for src in sorted(source.glob(pattern)):
        if src.is_file():
            shutil.copy2(src, dest / src.name)


def main() -> int:
    copy_tree_files(ROOT / 'jekyll' / '_includes' / 'pgl', DEST / 'includes', '*.html')
    copy_tree_files(ROOT / 'jekyll' / 'assets' / 'pgl', DEST / 'assets')
    copy_tree_files(ROOT / 'jekyll' / 'locales', DEST / 'locales', '*.yml')
    shutil.copy2(ROOT / 'jekyll' / '_plugins' / 'prospero_great_library.rb', DEST / 'prospero_great_library.rb')
    shutil.copy2(ROOT / 'adapters' / 'chirpy' / 'library-page.md', DEST / 'library-page.md')
    print('Chirpy package resources synchronized.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
