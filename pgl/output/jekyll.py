from __future__ import annotations
from pathlib import Path
from ..util import atomic_json, load_json


def output_paths(site_root):
    root=Path(site_root)
    data=root/'_data'/'prospero_great_library'
    assets=root/'assets'/'data'/'prospero_great_library'
    return data,assets


def write_current(site_root,library,stats,sync_status,associations,diagnostics,sources):
    data,assets=output_paths(site_root); data.mkdir(parents=True,exist_ok=True); assets.mkdir(parents=True,exist_ok=True)
    atomic_json(data/'library.json',library); atomic_json(data/'stats.json',stats); atomic_json(data/'sync_status.json',sync_status); atomic_json(data/'associations.json',associations)
    (data/'diagnostics').mkdir(exist_ok=True)
    atomic_json(data/'diagnostics'/'entity_resolution.json',diagnostics.get('entity_resolution',{}))
    atomic_json(data/'diagnostics'/'associations.json',{'suggestions':associations.get('suggestions',[])})
    atomic_json(data/'diagnostics'/'privacy.json',diagnostics.get('privacy',{}))
    (data/'sources').mkdir(exist_ok=True)
    for name,doc in sources.items(): atomic_json(data/'sources'/f'{name}.json',doc)
    atomic_json(assets/'library.json',library); atomic_json(assets/'stats.json',stats); atomic_json(assets/'sync_status.json',sync_status)


def _manifest(assets: Path):
    hdir=assets/'history'
    years=sorted([p.stem for p in hdir.glob('*.json') if p.stem.isdigit()],reverse=True) if hdir.exists() else []
    atomic_json(assets/'manifest.json',{'schema_version':1,'history_years':years,'library':'library.json','stats':'stats.json'})


def replace_history(site_root, events):
    """Atomically rewrite yearly history partitions from a sanitized event set."""
    _,assets=output_paths(site_root); hdir=assets/'history'; hdir.mkdir(parents=True,exist_ok=True)
    by_year={}
    seen=set()
    for event in events:
        eid=event.get('id')
        if eid in seen: continue
        seen.add(eid)
        year=str(event.get('local_date','unknown'))[:4]
        by_year.setdefault(year,[]).append(event)
    for rows in by_year.values(): rows.sort(key=lambda e:(e.get('observed_at',''),e.get('id','')))
    desired={str(year) for year in by_year if str(year).isdigit()}
    for p in hdir.glob('*.json'):
        if p.stem.isdigit() and p.stem not in desired:
            p.unlink()
    for year,rows in by_year.items():
        if str(year).isdigit():
            atomic_json(hdir/f'{year}.json',{'schema_version':1,'year':str(year),'events':rows})
    _manifest(assets)


def append_history(site_root,events):
    """Backward-compatible append helper; new pipeline uses replace_history after privacy scrub."""
    _,assets=output_paths(site_root); hdir=assets/'history'; existing=[]
    if hdir.exists():
        for p in hdir.glob('*.json'):
            existing.extend(load_json(p,{'events':[]}).get('events',[]))
    ids={e.get('id') for e in existing}
    existing.extend(e for e in events if e.get('id') not in ids)
    replace_history(site_root,existing)
