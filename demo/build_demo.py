#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pgl.config import load_config
from pgl.install import install_chirpy
from pgl.pipeline import run_sync

SITE = ROOT / 'demo' / 'site'
FIXTURES = ROOT / 'demo' / 'fixtures'


def _reset_demo_site() -> None:
    for path in [
        SITE / '_data' / 'prospero_great_library',
        SITE / '_data' / 'pgl_locales',
        SITE / 'assets' / 'data' / 'prospero_great_library',
        SITE / '_includes' / 'pgl',
        SITE / 'assets' / 'pgl',
    ]:
        shutil.rmtree(path, ignore_errors=True)
    for path in [SITE / '_plugins' / 'prospero_great_library.rb', SITE / '_tabs' / 'library.md', SITE / '.pgl-install.json']:
        path.unlink(missing_ok=True)
    shutil.rmtree(SITE / '.pgl-backups', ignore_errors=True)


def _make_previous_fixture_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix='pgl-demo-fixtures-'))
    for name in ('bangumi', 'neodb'):
        shutil.copy2(FIXTURES / f'{name}.json', tmp / f'{name}.json')
    steam = json.loads((FIXTURES / 'steam.json').read_text(encoding='utf-8'))
    for record in steam.get('records', []):
        telemetry = (record.get('telemetry') or {}).get('steam') or {}
        if telemetry.get('playtime_minutes') is not None:
            telemetry['playtime_minutes'] = max(0, int(telemetry['playtime_minutes']) - 120)
        achievements = telemetry.get('achievements') or {}
        if achievements.get('unlocked'):
            achievements['unlocked'] = max(0, int(achievements['unlocked']) - 1)
    (tmp / 'steam.json').write_text(json.dumps(steam, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return tmp


def main() -> int:
    _reset_demo_site()
    install_actions = install_chirpy(SITE)
    conflicts = [item for item in install_actions if item.action == 'conflict']
    if conflicts:
        details = ', '.join(item.path for item in conflicts)
        raise RuntimeError(f'Demo Chirpy install produced conflicts: {details}')
    cfg = load_config(SITE / '_config.yml')
    previous_dir = _make_previous_fixture_dir()
    try:
        first = run_sync(SITE, cfg, previous_dir)
        second = run_sync(SITE, cfg, FIXTURES)
    finally:
        shutil.rmtree(previous_dir, ignore_errors=True)

    print(json.dumps({
        'items': len(second['library']['items']),
        'first_sync_events': len(first['events']),
        'second_sync_events': len(second['events']),
        'steam_delta_events': sum(1 for event in second['events'] if event.get('event') == 'steam_playtime_delta'),
        'linked_entities': len(second['associations'].get('by_entity', {})),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
