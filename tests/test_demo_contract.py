from __future__ import annotations
import json
import shutil
from pathlib import Path

from pgl.config import load_config
from pgl.pipeline import run_sync

ROOT = Path(__file__).resolve().parents[1]


def _lower_steam_fixture(source: Path, destination: Path) -> None:
    doc = json.loads(source.read_text(encoding='utf-8'))
    for record in doc['records']:
        steam = (record.get('telemetry') or {}).get('steam') or {}
        if steam.get('playtime_minutes') is not None:
            steam['playtime_minutes'] = max(0, int(steam['playtime_minutes']) - 120)
        achievements = steam.get('achievements') or {}
        if achievements.get('unlocked'):
            achievements['unlocked'] = max(0, int(achievements['unlocked']) - 1)
    destination.write_text(json.dumps(doc), encoding='utf-8')


def test_demo_exercises_locked_v1_cases(tmp_path: Path):
    site = tmp_path / 'site'
    site.mkdir()
    shutil.copy2(ROOT / 'demo/site/_config.yml', site / '_config.yml')
    posts = site / '_posts'
    posts.mkdir()
    for post in (ROOT / 'demo/site/_posts').glob('*.md'):
        shutil.copy2(post, posts / post.name)

    previous = tmp_path / 'previous'
    previous.mkdir()
    for name in ('bangumi', 'neodb'):
        shutil.copy2(ROOT / f'demo/fixtures/{name}.json', previous / f'{name}.json')
    _lower_steam_fixture(ROOT / 'demo/fixtures/steam.json', previous / 'steam.json')

    cfg = load_config(site / '_config.yml')
    first = run_sync(site, cfg, previous)
    second = run_sync(site, cfg, ROOT / 'demo/fixtures')
    items = second['library']['items']

    assert {item['category'] for item in items} == {'book', 'comic', 'movie', 'drama', 'anime', 'game', 'music'}
    assert {'wishlist', 'in_progress', 'completed', 'on_hold', 'dropped'} <= {item.get('status') for item in items}
    source_sets = {frozenset(item.get('sources', {})) for item in items}
    assert frozenset({'bangumi'}) in source_sets
    assert frozenset({'neodb'}) in source_sets
    assert frozenset({'steam'}) in source_sets
    assert any(item['category'] == 'movie' and 'performance' in item.get('tags', []) for item in items)
    assert any(item['category'] == 'anime' and {'bangumi', 'neodb'} <= set(item.get('sources', {})) for item in items)
    assert any(item['category'] == 'comic' for item in items)
    assert any(item['category'] == 'book' for item in items)
    assert sum(1 for item in items if item['category'] == 'book' and item.get('status') in {'in_progress','completed'}) > 24
    assert second['stats']['navigation']['default_by_category']['book'] > 24
    assert second['stats']['rating_curve_distribution']['scopes']['book']
    assert second['associations']['by_entity']
    assert sum(1 for event in second['events'] if event['event'] == 'steam_playtime_delta') == 2
    assert second['stats']['steam']['observed_playtime_by_year_minutes']
    assert len(first['events']) == len(items)
