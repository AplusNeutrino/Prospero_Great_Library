import json
from copy import deepcopy
from pathlib import Path

from pgl.config import DEFAULTS
from pgl.pipeline import run_sync


def _base_cfg():
    cfg=deepcopy(DEFAULTS)
    cfg['sources']['bangumi'].update({'enabled':True,'username':'demo'})
    cfg['sources']['neodb']['enabled']=False
    cfg['sources']['steam']['enabled']=False
    cfg['association']['enabled']=False
    return cfg


def _write_fixture(path: Path):
    path.mkdir()
    record={
        'source':'bangumi','source_id':'42','category_hint':'anime','title':'Private Later',
        'identifiers':{'bangumi_subject_id':42},'links':{'bangumi':'https://bgm.tv/subject/42'},
        'extra':{'private':False},
    }
    (path/'bangumi.json').write_text(json.dumps({'records':[record]}),encoding='utf-8')


def test_hide_item_scrubs_existing_public_history(tmp_path: Path):
    site=tmp_path/'site'; site.mkdir(); fixtures=tmp_path/'fixtures'; _write_fixture(fixtures)
    cfg=_base_cfg(); first=run_sync(site,cfg,fixtures)
    entity=first['library']['items'][0]['id']
    assert any(e['entity_id']==entity for e in first['history'])

    cfg['privacy']['hide_items']=[entity]
    second=run_sync(site,cfg,fixtures)
    assert second['library']['items']==[]
    assert not any(e['entity_id']==entity for e in second['history'])
    assert second['diagnostics']['privacy']['history_scrub_reasons']['hidden_entity'] >= 1


def test_stats_only_item_does_not_leak_through_timeline(tmp_path: Path):
    site=tmp_path/'site'; site.mkdir(); fixtures=tmp_path/'fixtures'; _write_fixture(fixtures)
    cfg=_base_cfg(); first=run_sync(site,cfg,fixtures)
    entity=first['library']['items'][0]['id']
    cfg['privacy']['stats_only_items']=[entity]
    second=run_sync(site,cfg,fixtures)
    assert second['library']['items']==[]
    assert second['stats']['total_items']==1
    assert not any(e['entity_id']==entity for e in second['history'])
    assert second['diagnostics']['privacy']['history_scrub_reasons']['stats_only_entity'] >= 1


def test_privacy_scrub_runs_even_when_future_history_is_disabled(tmp_path: Path):
    site=tmp_path/'site'; site.mkdir(); fixtures=tmp_path/'fixtures'; _write_fixture(fixtures)
    cfg=_base_cfg(); first=run_sync(site,cfg,fixtures)
    entity=first['library']['items'][0]['id']
    cfg['privacy']['hide_items']=[entity]
    cfg['history']['enabled']=False
    second=run_sync(site,cfg,fixtures)
    assert second['diagnostics']['privacy']['history_events_scrubbed'] >= 1
    history_file=site/'assets/data/prospero_great_library/history/2026.json'
    if history_file.exists():
        persisted=json.loads(history_file.read_text(encoding='utf-8'))
        assert not any(e.get('entity_id')==entity for e in persisted.get('events',[]))

from pgl.privacy.audit import PrivacyContext, sanitize_history


def test_mixed_source_entity_keeps_public_history_but_scrubs_private_source_events():
    context=PrivacyContext(
        private_impacted_entities={'bangumi':{'game:mixed'}},
        private_only_entities=set(),
    )
    events=[
        {'id':'1','entity_id':'game:mixed','event':'entity_first_seen','source':None,'data':{'title':'Mixed'}},
        {'id':'2','entity_id':'game:mixed','event':'rating_changed','source':'bangumi','data':{'title':'Mixed'}},
        {'id':'3','entity_id':'game:mixed','event':'metadata_major_change','source':'neodb','data':{'title':'Mixed'}},
    ]
    kept,report=sanitize_history(events,context)
    assert [e['id'] for e in kept]==['1','3']
    assert report['history_scrub_reasons']['private_source_event']==1


def test_private_only_entity_scrubs_source_neutral_history_too():
    context=PrivacyContext(
        private_impacted_entities={'bangumi':{'anime:private'}},
        private_only_entities={'anime:private'},
    )
    events=[
        {'id':'1','entity_id':'anime:private','event':'entity_first_seen','source':None,'data':{'title':'Private'}},
        {'id':'2','entity_id':'anime:private','event':'status_changed','source':'bangumi','data':{'title':'Private'}},
    ]
    kept,report=sanitize_history(events,context)
    assert kept==[]
    assert report['history_scrub_reasons']['private_source_only_entity']==2
