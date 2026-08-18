from copy import deepcopy
import json
from pathlib import Path

from pgl.config import DEFAULTS
from pgl.pipeline import run_sync


def _config(hide=True):
    cfg=deepcopy(DEFAULTS)
    cfg['sources']['bangumi'].update({'enabled':True,'username':'demo','hide_private_collections':hide})
    cfg['sources']['neodb']['enabled']=False
    cfg['sources']['steam']['enabled']=False
    cfg['association']['enabled']=False
    return cfg


def _record(source_id: str, private: bool):
    return {
        'source':'bangumi','source_id':source_id,'category_hint':'anime',
        'title':f'Item {source_id}','extra':{'private':private},
        'identifiers':{'bangumi_subject_id':source_id},
        'links':{'bangumi':f'https://bgm.tv/subject/{source_id}'},
    }


def test_private_bangumi_records_are_removed_before_all_outputs(tmp_path: Path):
    site=tmp_path/'site'; site.mkdir()
    fixtures=tmp_path/'fixtures'; fixtures.mkdir()
    payload={'records':[_record('public',False),_record('private',True)]}
    (fixtures/'bangumi.json').write_text(json.dumps(payload),encoding='utf-8')

    result=run_sync(site,_config(True),fixtures)

    assert [x['source_id'] for x in result['sources']['bangumi']['records']]==['public']
    assert result['diagnostics']['privacy']['private_source_records_hidden']==1
    assert 'private_hidden_count' not in result['sync_status']['sources']['bangumi']
    assert result['sync_status']['privacy']['bangumi_private_filter_enabled'] is True
    assert result['sources']['bangumi']['record_count']==1
    assert 'Item private' not in json.dumps(result['library'],ensure_ascii=False)
    written=json.loads((site/'_data/prospero_great_library/sources/bangumi.json').read_text(encoding='utf-8'))
    assert [x['source_id'] for x in written['records']]==['public']


def test_private_bangumi_records_are_removed_from_stale_snapshot(tmp_path: Path,monkeypatch):
    site=tmp_path/'site'; source_dir=site/'_data/prospero_great_library/sources'
    source_dir.mkdir(parents=True)
    old={'records':[_record('public',False),_record('private',True)],'last_success_at':'2026-01-01T00:00:00Z'}
    (source_dir/'bangumi.json').write_text(json.dumps(old),encoding='utf-8')

    from pgl.adapters.bangumi import BangumiAdapter
    def fail(_self):
        raise RuntimeError('offline')
    monkeypatch.setattr(BangumiAdapter,'fetch_collections',fail)
    result=run_sync(site,_config(True))

    assert result['sync_status']['sources']['bangumi']['status']=='stale'
    assert result['diagnostics']['privacy']['private_source_records_hidden']==1
    assert 'private_hidden_count' not in result['sync_status']['sources']['bangumi']
    assert [x['source_id'] for x in result['sources']['bangumi']['records']]==['public']
    written=json.loads((source_dir/'bangumi.json').read_text(encoding='utf-8'))
    assert [x['source_id'] for x in written['records']]==['public']


def test_enabling_private_filter_scrubs_preexisting_history(tmp_path: Path):
    site=tmp_path/'site'; site.mkdir()
    fixtures=tmp_path/'fixtures'; fixtures.mkdir()
    payload={'records':[_record('public',False),_record('private',True)]}
    (fixtures/'bangumi.json').write_text(json.dumps(payload),encoding='utf-8')

    first=run_sync(site,_config(False),fixtures)
    assert any(e.get('data',{}).get('title')=='Item private' for e in first['history'])

    second=run_sync(site,_config(True),fixtures)
    assert second['diagnostics']['privacy']['history_events_scrubbed'] >= 1
    assert not any(e.get('data',{}).get('title')=='Item private' for e in second['history'])
    history_file=site/'assets/data/prospero_great_library/history/2026.json'
    persisted=json.loads(history_file.read_text(encoding='utf-8'))
    assert 'Item private' not in json.dumps(persisted,ensure_ascii=False)
    assert second['sync_status']['privacy']['public_output_violations']==0


def test_bangumi_private_filter_is_safe_by_default():
    from pgl.config import DEFAULTS
    assert DEFAULTS['sources']['bangumi']['hide_private_collections'] is True
    assert DEFAULTS['privacy']['publish_diagnostics'] is False
