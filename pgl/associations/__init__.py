from __future__ import annotations
from .posts import scan_posts
from .exact import find_exact
from .fuzzy import best_fuzzy

def associate(site_root, items, config, mappings=None):
    mappings=mappings or {}; assoc_cfg=config.get('association',{})
    by_entity={}; by_post={}; suggestions=[]
    manual={m.get('post'):m.get('entity') for m in mappings.get('articles',[]) if m.get('post') and m.get('entity')}
    for post in scan_posts(site_root):
        match=None
        if post['path'] in manual:
            item=next((x for x in items if x.get('id')==manual[post['path']]),None)
            if item: match=(item,1.0,'mapping')
        if not match and assoc_cfg.get('exact',True): match=find_exact(post,items)
        if not match and assoc_cfg.get('fuzzy',True):
            fuzzy=best_fuzzy(post,items)
            if fuzzy:
                score,item=fuzzy
                if score>=float(assoc_cfg.get('auto_threshold',.95)): match=(item,score,'title_alias')
                elif score>=float(assoc_cfg.get('suggest_threshold',.80)):
                    suggestions.append({'post':post['path'],'post_title':post['title'],'candidate_id':item['id'],'candidate_title':item.get('title'),'confidence':round(score,4),'method':'fuzzy_title'})
        if match:
            item,score,method=match
            ref={'url':post['url'],'title':post['title'],'path':post['path'],'confidence':round(float(score),4),'method':method}
            by_entity.setdefault(item['id'],[]).append(ref)
            by_post.setdefault(post['url'],[]).append({'entity_id':item['id'],'confidence':round(float(score),4),'method':method})
    return {'by_entity':by_entity,'by_post':by_post,'suggestions':suggestions}
