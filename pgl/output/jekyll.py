from __future__ import annotations
from pathlib import Path
from ..util import atomic_json

def output_paths(site_root):
    root=Path(site_root)
    data=root/'_data'/'prospero_great_library'
    assets=root/'assets'/'data'/'prospero_great_library'
    return data,assets

def write_current(site_root,library,stats,sync_status,associations,diagnostics,sources):
    data,assets=output_paths(site_root); data.mkdir(parents=True,exist_ok=True); assets.mkdir(parents=True,exist_ok=True)
    atomic_json(data/'library.json',library); atomic_json(data/'stats.json',stats); atomic_json(data/'sync_status.json',sync_status); atomic_json(data/'associations.json',associations)
    (data/'diagnostics').mkdir(exist_ok=True); atomic_json(data/'diagnostics'/'entity_resolution.json',diagnostics.get('entity_resolution',{})); atomic_json(data/'diagnostics'/'associations.json',{'suggestions':associations.get('suggestions',[])})
    (data/'sources').mkdir(exist_ok=True)
    for name,doc in sources.items(): atomic_json(data/'sources'/f'{name}.json',doc)
    atomic_json(assets/'library.json',library); atomic_json(assets/'stats.json',stats); atomic_json(assets/'sync_status.json',sync_status)

def append_history(site_root,events):
    from ..util import load_json
    _,assets=output_paths(site_root); hdir=assets/'history'; hdir.mkdir(parents=True,exist_ok=True)
    by_year={}
    for e in events: by_year.setdefault(e.get('local_date','unknown')[:4],[]).append(e)
    for year,new in by_year.items():
        p=hdir/f'{year}.json'; old=load_json(p,{'schema_version':1,'year':year,'events':[]}); ids={e.get('id') for e in old.get('events',[])}
        old.setdefault('events',[]).extend(e for e in new if e.get('id') not in ids); old['events'].sort(key=lambda e:(e.get('observed_at',''),e.get('id',''))); atomic_json(p,old)
    years=sorted([p.stem for p in hdir.glob('*.json') if p.stem.isdigit()],reverse=True)
    atomic_json(assets/'manifest.json',{'schema_version':1,'history_years':years,'library':'library.json','stats':'stats.json'})
