from pathlib import Path
import shutil,json
from pgl.config import load_config
from pgl.pipeline import run_sync

ROOT=Path(__file__).resolve().parents[1]

def fresh_site(tmp_path):
    site=tmp_path/'site'; shutil.copytree(ROOT/'demo'/'site',site)
    data=site/'_data'/'prospero_great_library'; mapping=(data/'mappings.yml').read_text(encoding='utf-8') if (data/'mappings.yml').exists() else 'entities: []\nclassifications: []\narticles: []\nprivacy: []\n'
    if data.exists(): shutil.rmtree(data)
    data.mkdir(parents=True); (data/'mappings.yml').write_text(mapping,encoding='utf-8')
    assets=site/'assets'/'data'/'prospero_great_library'
    if assets.exists(): shutil.rmtree(assets)
    return site

def test_fixture_pipeline(tmp_path):
    site=fresh_site(tmp_path)
    cfg=load_config(site/'_config.yml')
    result=run_sync(site,cfg,ROOT/'demo'/'fixtures')
    items=result['library']['items']; cats={x['category'] for x in items}
    assert {'book','comic','movie','drama','anime','game','music'} <= cats
    assert len(items)==11
    anime=next(x for x in items if x['category']=='anime')
    assert anime['links']['primary']=='https://bgm.tv/subject/1'
    comic=next(x for x in items if x['category']=='comic')
    assert comic['status']=='in_progress'  # Bangumi beats NeoDB completed
    perf=next(x for x in items if x['category']=='movie')
    assert 'performance' in perf['tags']
    game=next(x for x in items if x['category']=='game')
    assert game['telemetry']['steam']['playtime_minutes']==2556
    assert result['associations']['by_entity'][game['id']]
    assert (site/'_data'/'prospero_great_library'/'library.json').exists()
    assert (site/'assets'/'data'/'prospero_great_library'/'manifest.json').exists()

def test_second_identical_sync_is_idempotent(tmp_path):
    site=fresh_site(tmp_path); cfg=load_config(site/'_config.yml')
    first=run_sync(site,cfg,ROOT/'demo'/'fixtures')
    second=run_sync(site,cfg,ROOT/'demo'/'fixtures')
    assert first['events']
    assert second['events']==[]
