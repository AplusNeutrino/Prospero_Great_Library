import json
from pathlib import Path

from pgl.cli import main


def test_privacy_audit_reports_hidden_private_records(tmp_path: Path, capsys):
    site=tmp_path/'site'; site.mkdir()
    (site/'_config.yml').write_text('''prospero_great_library:\n  sources:\n    bangumi:\n      enabled: true\n      username: demo\n      hide_private_collections: true\n    neodb:\n      enabled: false\n    steam:\n      enabled: false\n  association:\n    enabled: false\n''',encoding='utf-8')
    fixtures=tmp_path/'fixtures'; fixtures.mkdir()
    (fixtures/'bangumi.json').write_text(json.dumps({'records':[
        {'source':'bangumi','source_id':'1','category_hint':'anime','title':'Visible','extra':{'private':False}},
        {'source':'bangumi','source_id':'2','category_hint':'anime','title':'Secret','extra':{'private':True}},
    ]}),encoding='utf-8')
    rc=main(['privacy-audit','--site-root',str(site),'--fixtures',str(fixtures)])
    out=json.loads(capsys.readouterr().out)
    assert rc==0
    assert out['private_source_records_hidden']==1
    assert out['public_output_violations']==0
    assert not (site/'_data/prospero_great_library/library.json').exists()


def test_public_persisted_privacy_diagnostics_are_redacted_by_default(tmp_path: Path):
    from copy import deepcopy
    from pgl.config import DEFAULTS
    from pgl.pipeline import run_sync

    site=tmp_path/'site2'; site.mkdir()
    fixtures=tmp_path/'fixtures2'; fixtures.mkdir()
    (fixtures/'bangumi.json').write_text(json.dumps({'records':[
        {'source':'bangumi','source_id':'1','category_hint':'anime','title':'Visible','extra':{'private':False}},
        {'source':'bangumi','source_id':'2','category_hint':'anime','title':'Secret','extra':{'private':True}},
    ]}),encoding='utf-8')
    cfg=deepcopy(DEFAULTS)
    cfg['sources']['bangumi'].update({'enabled':True,'username':'demo'})
    cfg['sources']['neodb']['enabled']=False; cfg['sources']['steam']['enabled']=False
    cfg['association']['enabled']=False
    result=run_sync(site,cfg,fixtures)
    assert result['diagnostics']['privacy']['private_source_records_hidden']==1
    persisted=json.loads((site/'_data/prospero_great_library/diagnostics/privacy.json').read_text(encoding='utf-8'))
    assert 'private_source_records_hidden' not in persisted
    assert persisted['bangumi_private_filter_enabled'] is True
    status=json.loads((site/'_data/prospero_great_library/sync_status.json').read_text(encoding='utf-8'))
    assert 'private_hidden_count' not in status['sources']['bangumi']


def test_publish_privacy_diagnostics_opt_in_exposes_counts(tmp_path: Path):
    from copy import deepcopy
    from pgl.config import DEFAULTS
    from pgl.pipeline import run_sync

    site=tmp_path/'site3'; site.mkdir()
    fixtures=tmp_path/'fixtures3'; fixtures.mkdir()
    (fixtures/'bangumi.json').write_text(json.dumps({'records':[
        {'source':'bangumi','source_id':'2','category_hint':'anime','title':'Secret','extra':{'private':True}},
    ]}),encoding='utf-8')
    cfg=deepcopy(DEFAULTS)
    cfg['sources']['bangumi'].update({'enabled':True,'username':'demo'})
    cfg['sources']['neodb']['enabled']=False; cfg['sources']['steam']['enabled']=False
    cfg['association']['enabled']=False
    cfg['privacy']['publish_diagnostics']=True
    result=run_sync(site,cfg,fixtures)
    assert result['sync_status']['sources']['bangumi']['private_hidden_count']==1
    persisted=json.loads((site/'_data/prospero_great_library/diagnostics/privacy.json').read_text(encoding='utf-8'))
    assert persisted['private_source_records_hidden']==1
