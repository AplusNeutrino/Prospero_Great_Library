from __future__ import annotations
from copy import deepcopy

def apply_privacy(items, config, mappings=None):
    mappings=mappings or {}; cfg=config.get('privacy',{})
    hide=set(str(x) for x in cfg.get('hide_items',[])); stats_only=set(str(x) for x in cfg.get('stats_only_items',[])); global_hide_sources=set(cfg.get('hide_sources',[]))
    per_item_privacy={}
    for row in mappings.get('privacy',[]):
        entity=str(row.get('entity') or '')
        if not entity: continue
        per_item_privacy[entity]=row
        if row.get('hidden'): hide.add(entity)
        if row.get('stats_only'): stats_only.add(entity)
    public=[]; stat_items=[]
    for src in items:
        if src.get('id') in hide: continue
        x=deepcopy(src); priv=x.setdefault('privacy',{})
        override=per_item_privacy.get(str(x.get('id'))) or {}
        if override.get('hide_sources'):
            priv['hide_sources']=list(dict.fromkeys([*(priv.get('hide_sources') or []),*override.get('hide_sources',[])]))
        hidden_sources=set(priv.get('hide_sources') or []) | global_hide_sources
        for s in hidden_sources:
            x.get('sources',{}).pop(s,None); x.get('links',{}).pop(s,None)
        for field in ('rating','progress'):
            if isinstance(x.get(field),dict) and x[field].get('source') in hidden_sources:
                x[field]['source']=None
        if isinstance(x.get('_provenance'),dict):
            x['_provenance']={k:(None if v in hidden_sources else v) for k,v in x['_provenance'].items()}
        preferred='bangumi' if x.get('category') in ('anime','game') else 'neodb'
        links=x.get('links',{}); links['primary']=links.get(preferred) or next((links.get(s) for s in ('bangumi','neodb','steam') if links.get(s)),None)
        stat_items.append(x)
        if x.get('id') not in stats_only: public.append(x)
    return public,stat_items
