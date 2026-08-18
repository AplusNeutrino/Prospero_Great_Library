#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

# When run from a source checkout, ensure the project package is importable.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pgl.install import format_actions, install_chirpy


def main(argv=None):
    ap = argparse.ArgumentParser(description="Install PGL Jekyll/Chirpy integration into a site")
    ap.add_argument("site_root", nargs="?", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-backup", action="store_true", help="Do not back up conflicting files replaced with --force")
    args = ap.parse_args(argv)
    actions = install_chirpy(args.site_root, dry_run=args.dry_run, force=args.force, backup=not args.no_backup)
    print(format_actions(actions))
    conflicts = [x for x in actions if x.action == "conflict"]
    if conflicts:
        print(f"\n{len(conflicts)} conflict(s) preserved. Re-run with --force only after reviewing them.")
        return 2
    print("\nDone. Merge config.example.yml into _config.yml and add required GitHub Secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
