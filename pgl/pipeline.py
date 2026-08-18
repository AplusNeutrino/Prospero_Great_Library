from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
from .adapters import BangumiAdapter,NeoDBAdapter,SteamAdapter
from .adapters.base import CapabilityUnavailable
from .config import secret
from .models import SourceRecord
from .resolve.mappings import load_mappings
from .resolve.entities import resolve
from .merge import merge_all
from .privacy.filters import apply_privacy
from .history.diff import diff_libraries
from .history.stats import build_stats
from .associations import associate
from .output.jekyll import write_current,append_history,output_paths
from .schema import validate_library
from .util import load_json,now_utc

ADAPTERS={'bangumi':BangumiAdapter,'neodb':NeoDBAdapter,'steam':SteamAdapter}
SECRETS={'bangumi':'BANGUMI_ACCESS_TOKEN','neodb':'NEODB_ACCESS_TOKEN','steam':'STEAM_API_KEY'}

def _snapshot_path(site_root, name):
    data,_=output_paths(site_root); return data/'sources'/f'{name}.json'

def _load_snapshot(site_root,name):
    doc=load_json(_snapshot_path(site_root,name),{'records':[]})
    return [SourceRecord.from_dict(x) for x in doc.get('records',[])]

def _fixture_records(fixture_dir,name):
    p=Path(fixture_dir)/f'{name}.json'
    if not p.exists(): return []
    doc=json.loads(p.read_text(encoding='utf-8'))
    return [SourceRecord.from_dict(x) for x in doc.get('records',doc if isinstance(doc,list) else [])]

def run_sync(site_root: str|Path, config: dict[str,Any], fixture_dir: str|Path|None=None, dry_run=False):
    root=Path(site_root); observed=now_utc(); mappings=load_mappings(root/'_data'/'prospero_great_library'/'mappings.yml')
    previous=load_json(root/'_data'/'prospero_great_library'/'library.json',{'schema_version':1,'items':[]})
    all_records=[]; source_docs={}; source_status={}
    for name,cls in ADAPTERS.items():
        scfg=config.get('sources',{}).get(name,{})
        if not scfg.get('enabled',False):
            source_status[name]={'status':'disabled'}; continue
        try:
            if fixture_dir:
                records=_fixture_records(fixture_dir,name)
            else:
                adapter=cls(scfg, secret(SECRETS[name]))
                records=adapter.fetch_collections()
            all_records.extend(records)
            source_docs[name]={'schema_version':1,'source':name,'fetched_at':observed,'last_success_at':observed,'adapter_version':'0.1.0-alpha.2','record_count':len(records),'records':[r.to_dict() for r in records]}
            source_status[name]={'status':'ok','last_success':observed,'record_count':len(records)}
        except Exception as exc:
            stale=_load_snapshot(root,name) if config.get('sync',{}).get('preserve_last_good',True) else []
            all_records.extend(stale)
            previous_doc=load_json(_snapshot_path(root,name),{'records':[]})
            if previous_doc.get('records'): source_docs[name]=previous_doc
            status='capability_unavailable' if isinstance(exc,CapabilityUnavailable) else 'stale'
            source_status[name]={'status':status,'last_success':previous_doc.get('last_success_at'),'record_count':len(stale),'error':str(exc)}
    rr=resolve(all_records,mappings,float(config.get('association',{}).get('auto_threshold',.95)),float(config.get('association',{}).get('suggest_threshold',.80)))
    merged=merge_all(rr.groups,config,mappings,previous,observed)
    public_items,stat_items=apply_privacy(merged,config,mappings)
    library={'schema_version':1,'generated_at':observed,'items':public_items}
    # associate against public items only, then embed references into cards
    associations=associate(root,public_items,config,mappings) if config.get('association',{}).get('enabled',True) else {'by_entity':{},'by_post':{},'suggestions':[]}
    for item in public_items: item['articles']=associations.get('by_entity',{}).get(item['id'],[])
    validate_library(library)
    events=[]
    if config.get('history',{}).get('enabled',True):
        events=diff_libraries(previous,library,observed,config.get('sync',{}).get('timezone','UTC'))
    # Include all existing history in yearly aggregate without loading it into initial page output.
    _,assets=output_paths(root); existing_events=[]
    for p in (assets/'history').glob('*.json') if (assets/'history').exists() else []:
        existing_events.extend(load_json(p,{'events':[]}).get('events',[]))
    known={e.get('id') for e in existing_events}; all_history=existing_events+[e for e in events if e.get('id') not in known]
    stats=build_stats(stat_items,all_history)
    overall='ok' if all(v.get('status') in ('ok','disabled') for v in source_status.values()) else 'degraded'
    sync_status={'last_run':observed,'overall':overall,'sources':source_status}
    diagnostics={'entity_resolution':rr.diagnostics}
    result={'library':library,'stats':stats,'sync_status':sync_status,'associations':associations,'diagnostics':diagnostics,'events':events,'sources':source_docs}
    if not dry_run:
        write_current(root,library,stats,sync_status,associations,diagnostics,source_docs)
        if config.get('history',{}).get('enabled',True): append_history(root,events)
    return result
