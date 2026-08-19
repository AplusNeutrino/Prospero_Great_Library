from __future__ import annotations
from pathlib import Path
from typing import Any
import json

from . import __version__
from .adapters import BangumiAdapter,NeoDBAdapter,SteamAdapter
from .adapters.base import CapabilityUnavailable
from .config import secret
from .models import SourceRecord
from .resolve.mappings import load_mappings
from .resolve.entities import resolve
from .merge import merge_all
from .privacy.filters import apply_privacy
from .privacy.audit import (
    assert_public_payload_safe,
    audit_public_payload,
    build_privacy_context,
    filter_source_records,
    sanitize_history,
)
from .history.diff import diff_libraries
from .history.stats import build_stats
from .associations import associate
from .output.jekyll import write_current,replace_history,output_paths
from .schema import validate_library
from .util import load_json,now_utc

ADAPTERS={'bangumi':BangumiAdapter,'neodb':NeoDBAdapter,'steam':SteamAdapter}
SECRETS={'bangumi':'BANGUMI_ACCESS_TOKEN','neodb':'NEODB_ACCESS_TOKEN','steam':'STEAM_API_KEY'}


def _publish_privacy_diagnostics(config: dict[str,Any]) -> bool:
    return bool(config.get('privacy',{}).get('publish_diagnostics',False))


def _public_privacy_report(full: dict[str,Any], config: dict[str,Any]) -> dict[str,Any]:
    """Redact counts/reasons that reveal private-library metadata by default."""
    if _publish_privacy_diagnostics(config):
        return full
    return {
        'bangumi_private_filter_enabled': bool(
            config.get('sources',{}).get('bangumi',{}).get('hide_private_collections',True)
        ),
        'history_sanitized': bool(full.get('history_events_scrubbed',0)),
        'public_output_violations': int(full.get('public_output_violations',0)),
    }


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


def _history_from_disk(root: Path) -> list[dict[str,Any]]:
    _,assets=output_paths(root); events=[]; hdir=assets/'history'
    if hdir.exists():
        for p in sorted(hdir.glob('*.json')):
            events.extend(load_json(p,{'events':[]}).get('events',[]))
    return events


def run_sync(site_root: str|Path, config: dict[str,Any], fixture_dir: str|Path|None=None, dry_run=False):
    root=Path(site_root); observed=now_utc(); mappings=load_mappings(root/'_data'/'prospero_great_library'/'mappings.yml')
    previous=load_json(root/'_data'/'prospero_great_library'/'library.json',{'schema_version':1,'items':[]})
    all_records=[]; source_docs={}; source_status={}; hidden_source_records={}

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
            records,private_hidden=filter_source_records(name,records,scfg)
            hidden_source_records[name]=private_hidden
            all_records.extend(records)
            source_docs[name]={
                'schema_version':1,'source':name,'fetched_at':observed,'last_success_at':observed,
                'adapter_version':__version__,'record_count':len(records),'records':[r.to_dict() for r in records]
            }
            source_status[name]={
                'status':'ok','last_success':observed,'record_count':len(records),
            }
            if name=='bangumi':
                source_status[name]['private_filter_applied']=bool(scfg.get('hide_private_collections',True))
                if _publish_privacy_diagnostics(config):
                    source_status[name]['private_hidden_count']=len(private_hidden)
        except Exception as exc:
            stale=_load_snapshot(root,name) if config.get('sync',{}).get('preserve_last_good',True) else []
            stale,private_hidden=filter_source_records(name,stale,scfg)
            hidden_source_records[name]=private_hidden
            all_records.extend(stale)
            previous_doc=load_json(_snapshot_path(root,name),{'records':[]})
            if previous_doc.get('records'):
                source_docs[name]={**previous_doc,'record_count':len(stale),'records':[r.to_dict() for r in stale]}
            status='capability_unavailable' if isinstance(exc,CapabilityUnavailable) else 'stale'
            source_status[name]={
                'status':status,'last_success':previous_doc.get('last_success_at'),'record_count':len(stale),
                'error':str(exc)
            }
            if name=='bangumi':
                source_status[name]['private_filter_applied']=bool(scfg.get('hide_private_collections',True))
                if _publish_privacy_diagnostics(config):
                    source_status[name]['private_hidden_count']=len(private_hidden)

    rr=resolve(
        all_records,mappings,
        float(config.get('association',{}).get('auto_threshold',.95)),
        float(config.get('association',{}).get('suggest_threshold',.80)),
    )
    merged=merge_all(rr.groups,config,mappings,previous,observed)
    public_items,stat_items=apply_privacy(merged,config,mappings)
    library={'schema_version':1,'generated_at':observed,'items':public_items}

    associations=associate(root,public_items,config,mappings) if config.get('association',{}).get('enabled',True) else {'by_entity':{},'by_post':{},'suggestions':[]}
    for item in public_items:
        item['articles']=associations.get('by_entity',{}).get(item['id'],[])
    validate_library(library)

    events=[]
    if config.get('history',{}).get('enabled',True):
        events=diff_libraries(previous,library,observed,config.get('sync',{}).get('timezone','UTC'))

    existing_events=_history_from_disk(root)
    privacy_context=build_privacy_context(
        config,mappings,previous,public_items,hidden_source_records
    )
    sanitized_existing,scrub_report=sanitize_history(existing_events,privacy_context)
    sanitized_new,new_scrub_report=sanitize_history(events,privacy_context)
    # Newly generated events should already be privacy-safe; still sanitize defensively.
    scrub_report['history_events_scrubbed'] += new_scrub_report['history_events_scrubbed']
    combined_reasons=dict(scrub_report.get('history_scrub_reasons',{}))
    for key,value in new_scrub_report.get('history_scrub_reasons',{}).items():
        combined_reasons[key]=combined_reasons.get(key,0)+value
    scrub_report['history_scrub_reasons']=dict(sorted(combined_reasons.items()))

    known={e.get('id') for e in sanitized_existing}
    all_history=sanitized_existing+[e for e in sanitized_new if e.get('id') not in known]

    violations=audit_public_payload(library,source_docs,all_history,config,privacy_context)
    private_hidden_total=sum(len(v) for v in hidden_source_records.values())
    privacy_report={
        'private_source_records_hidden':private_hidden_total,
        'private_source_records_hidden_by_source':{
            k:len(v) for k,v in hidden_source_records.items() if v
        },
        **scrub_report,
        'public_output_violations':len(violations),
        'violations':violations,
    }
    # Privacy is a publication invariant, not an optional strict-mode behavior.
    assert_public_payload_safe(library,source_docs,all_history,config,privacy_context)

    stats=build_stats(public_items,all_history,aggregate_items=stat_items,config=config)
    overall='ok' if all(v.get('status') in ('ok','disabled') for v in source_status.values()) else 'degraded'
    public_privacy_report=_public_privacy_report(privacy_report,config)
    sync_status={'last_run':observed,'overall':overall,'sources':source_status,'privacy':public_privacy_report}
    diagnostics={'entity_resolution':rr.diagnostics,'privacy':privacy_report,'privacy_public':public_privacy_report}
    result={
        'library':library,'stats':stats,'sync_status':sync_status,'associations':associations,
        'diagnostics':diagnostics,'events':sanitized_new,'history':all_history,'sources':source_docs
    }
    if not dry_run:
        write_current(root,library,stats,sync_status,associations,{**diagnostics,'privacy':public_privacy_report},source_docs)
        if config.get('history',{}).get('enabled',True) or scrub_report.get('history_events_scrubbed',0):
            # Privacy scrub is applied even when future history collection is disabled;
            # disabling history must not leave known-private legacy events published.
            replace_history(root,all_history)
    return result
