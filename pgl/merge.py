from __future__ import annotations
from typing import Any
from .models import SourceRecord
from .normalize.categories import choose_group_category
from .util import short_hash, now_utc, safe_http_url
from .resolve.mappings import explicit_entity_for

DEFAULT_SOURCE_ORDER=['bangumi','neodb','steam']

def _first(records, attr, order):
    by={r.source:r for r in records}
    for s in order:
        r=by.get(s)
        if r:
            v=getattr(r,attr,None)
            if v not in (None,'',[],{}): return v,s
    for r in records:
        v=getattr(r,attr,None)
        if v not in (None,'',[],{}): return v,r.source
    return None,None

def _old_id(records, previous):
    for item in previous.get('items',[]) if previous else []:
        sources=item.get('sources',{})
        for r in records:
            s=sources.get(r.source) or {}
            oldid=s.get('id',s.get('appid'))
            if oldid is not None and str(oldid)==str(r.source_id): return item.get('id')
    return None

def canonical_id(records, category, mappings, previous):
    for r in records:
        eid=explicit_entity_for(r,mappings)
        if eid: return eid
    old=_old_id(records,previous)
    if old: return old
    for source in ('bangumi','neodb','steam'):
        r=next((x for x in records if x.source==source),None)
        if r: return f'{category}:{short_hash(source+":"+str(r.source_id),10)}'
    return f'{category}:{short_hash(records[0].title,10)}'

def _previous_item(previous, cid):
    return next((x for x in (previous.get('items',[]) if previous else []) if x.get('id')==cid),None)

def _canonical_payload(item):
    # Fields whose change should make "recently updated" meaningful. Observational
    # timestamps, article links and private presentation metadata are excluded.
    keys=('category','tags','title','title_original','alternate_titles','year','release_date','cover','summary','status','rating','progress','telemetry','links','identifiers')
    return {k:item.get(k) for k in keys}

def merge_group(records: list[SourceRecord], config: dict[str,Any], mappings, previous, observed_at=None):
    observed_at=observed_at or now_utc()
    category,tags=choose_group_category(records)
    order=(config.get('precedence',{}).get(category) or ['bangumi','neodb']) + ['steam']
    # dedupe order while preserving preference
    order=list(dict.fromkeys(order))
    title,title_src=_first(records,'title',order)
    title_original,_=_first(records,'title_original',order)
    year,_=_first(records,'year',order); release_date,_=_first(records,'release_date',order)
    cover_url,cover_src=_first(records,'cover_url',order); cover_url=safe_http_url(cover_url); summary,_=_first(records,'summary',order)
    status,status_src=_first(records,'status',order); rating,rating_src=_first(records,'rating',order); progress,progress_src=_first(records,'progress',order)
    aliases=[]
    for r in records:
        for x in [r.title,r.title_original,*r.alternate_titles]:
            if x and x!=title and x not in aliases: aliases.append(x)
    identifiers={}; links={}; sources={}; telemetry={}
    for r in records:
        identifiers.update({k:v for k,v in r.identifiers.items() if v not in (None,'')})
        links.update({k:safe_http_url(v) for k,v in r.links.items() if safe_http_url(v)})
        if r.telemetry: telemetry.update(r.telemetry)
        sources[r.source]={
            'present':True,'id':r.source_id,'url':r.links.get(r.source),
            'status':r.status,'rating':r.rating.to_dict() if r.rating else None,
            'updated_at':r.updated_at,'extra':r.extra,
        }
    cid=canonical_id(records,category,mappings,previous)
    preferred='bangumi' if category in ('anime','game') else 'neodb'
    primary=links.get(preferred) or next((links.get(x) for x in ('bangumi','neodb','steam') if links.get(x)),None)
    old_item=_previous_item(previous,cid)
    first_seen=((old_item.get('timestamps') or {}).get('first_seen_at') or observed_at) if old_item else observed_at
    item={
        'id':cid,'schema_version':1,'category':category,'tags':tags,'title':title or '',
        'title_original':title_original,'alternate_titles':aliases,'year':year,'release_date':release_date,
        'cover':{'url':cover_url,'source':cover_src,'cached':False,'local_path':None} if cover_url else None,
        'summary':summary,'status':status,
        'rating':rating.to_dict() | {'source':rating_src} if rating else None,
        'progress':progress.to_dict() | {'source':progress_src} if progress else None,
        'telemetry':telemetry,'links':{'primary':primary,**links},'identifiers':identifiers,'sources':sources,'articles':[],
        'privacy':{'hidden':False,'hide_sources':[],'stats_only':False},
        'timestamps':{'first_seen_at':first_seen,'last_seen_at':observed_at,'canonical_updated_at':observed_at},
        '_provenance':{'title':title_src,'cover.url':cover_src,'status':status_src,'rating':rating_src,'progress':progress_src}
    }
    if old_item and _canonical_payload(old_item)==_canonical_payload(item):
        item['timestamps']['canonical_updated_at']=(old_item.get('timestamps') or {}).get('canonical_updated_at') or observed_at
    return item

def merge_all(groups,config,mappings,previous,observed_at=None):
    return [merge_group(g,config,mappings,previous,observed_at) for g in groups]
