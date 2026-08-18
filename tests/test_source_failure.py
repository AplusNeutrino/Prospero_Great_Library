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
    assert second['library']['items'] == expected
    assert second['events'] == []
