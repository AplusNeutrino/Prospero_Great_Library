from copy import deepcopy
from pathlib import Path

from pgl.adapters.bangumi import BangumiAdapter
from pgl.config import DEFAULTS
from pgl.pipeline import run_sync

ROOT = Path(__file__).resolve().parents[1]


def _config():
    cfg = deepcopy(DEFAULTS)
    cfg['sources']['bangumi'].update({'enabled': True, 'username': 'demo'})
    cfg['sources']['neodb']['enabled'] = False
    cfg['sources']['steam']['enabled'] = False
    cfg['association']['enabled'] = False
    return cfg


def test_source_failure_preserves_last_good_snapshot(tmp_path: Path, monkeypatch):
    site = tmp_path / 'site'
    site.mkdir()
    (site / '_config.yml').write_text('title: fallback test\n', encoding='utf-8')
    cfg = _config()

    first = run_sync(site, cfg, ROOT / 'demo/fixtures')
    expected = first['library']['items']
    assert expected

    def fail(_self):
        raise RuntimeError('simulated upstream outage')

    monkeypatch.setattr(BangumiAdapter, 'fetch_collections', fail)
    second = run_sync(site, cfg)

    assert second['sync_status']['overall'] == 'degraded'
    assert second['sync_status']['sources']['bangumi']['status'] == 'stale'
    assert 'simulated upstream outage' in second['sync_status']['sources']['bangumi']['error']
    # A stale last-good source may be observed in a later wall-clock second, so
    # last_seen_at is allowed to advance. The preserved canonical/source
    # semantics must otherwise remain identical and must not emit change events.
    actual = deepcopy(second['library']['items'])
    expected_semantic = deepcopy(expected)
    for rows in (actual, expected_semantic):
        for row in rows:
            (row.get('timestamps') or {}).pop('last_seen_at', None)
    assert actual == expected_semantic
    assert second['events'] == []


def test_steam_privacy_probe_failure_does_not_republish_last_good(tmp_path: Path, monkeypatch):
    from pgl.adapters.steam import SteamAdapter
    from pgl.adapters.base import PrivacyBoundaryUnavailable

    site = tmp_path / 'site'
    site.mkdir()
    (site / '_config.yml').write_text('title: privacy fallback test\n', encoding='utf-8')
    cfg = deepcopy(DEFAULTS)
    cfg['sources']['bangumi']['enabled'] = False
    cfg['sources']['neodb']['enabled'] = False
    cfg['sources']['steam'].update({'enabled': True, 'steam_id': '123', 'filter_private_games': True})
    cfg['association']['enabled'] = False

    first = run_sync(site, cfg, ROOT / 'demo/fixtures')
    assert first['library']['items']
    assert first['sources']['steam']['records']

    def fail(_self):
        raise PrivacyBoundaryUnavailable('public visibility probe unavailable')

    monkeypatch.setattr(SteamAdapter, 'fetch_collections', fail)
    second = run_sync(site, cfg)
    assert second['sync_status']['overall'] == 'degraded'
    assert second['sync_status']['sources']['steam']['status'] == 'privacy_boundary_unavailable'
    assert second['sources']['steam']['records'] == []
    assert second['library']['items'] == []


def test_steam_disappeared_public_record_is_treated_as_private_for_history_scrub(tmp_path: Path, monkeypatch):
    from pgl.adapters.steam import SteamAdapter
    from pgl.models import SourceRecord

    site = tmp_path / 'site'
    site.mkdir()
    (site / '_config.yml').write_text('title: steam privacy transition\n', encoding='utf-8')
    cfg = deepcopy(DEFAULTS)
    cfg['sources']['bangumi']['enabled'] = False
    cfg['sources']['neodb']['enabled'] = False
    cfg['sources']['steam'].update({'enabled': True, 'steam_id': '123', 'filter_private_games': True})
    cfg['association']['enabled'] = False

    first = run_sync(site, cfg, ROOT / 'demo/fixtures')
    first_ids = {row.source_id for row in [SourceRecord.from_dict(x) for x in first['sources']['steam']['records']]}
    assert first_ids
    keep = sorted(first_ids)[0]

    def only_one(_self):
        return [SourceRecord(source='steam', source_id=keep, category_hint='game', title='Still public', identifiers={'steam_appid': int(keep)})]

    monkeypatch.setattr(SteamAdapter, 'fetch_collections', only_one)
    second = run_sync(site, cfg)
    assert [x['source_id'] for x in second['sources']['steam']['records']] == [keep]
    assert len(second['library']['items']) == 1
    assert all((event.get('entity_id') == second['library']['items'][0]['id']) for event in second['history'])
