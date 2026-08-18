from __future__ import annotations
from collections import Counter,defaultdict

def build_stats(items, history_events=None):
    history_events=history_events or []
    cats=Counter(); statuses=Counter(); ratings=Counter(); steam_total=0; steam_ranking=[]
    for x in items:
        cats[x.get('category')]+=1
        if x.get('status'): statuses[x['status']]+=1
        r=(x.get('rating') or {}).get('normalized_10')
        if r is not None: ratings[str(int(round(float(r))))]+=1
        mins=int((((x.get('telemetry') or {}).get('steam') or {}).get('playtime_minutes') or 0))
        if mins:
            steam_total+=mins; steam_ranking.append({'id':x['id'],'title':x.get('title'),'minutes':mins})
    yearly=defaultdict(int)
    for e in history_events:
        if e.get('event')=='steam_playtime_delta': yearly[e.get('local_date','')[:4]] += int((e.get('data') or {}).get('delta_minutes') or 0)
    steam_ranking.sort(key=lambda x:x['minutes'], reverse=True)
    return {'total_items':len(items),'by_category':dict(cats),'by_status':dict(statuses),'rating_distribution':dict(sorted(ratings.items(),key=lambda x:int(x[0]))),
            'steam':{'lifetime_playtime_minutes':steam_total,'ranking':steam_ranking,'observed_playtime_by_year_minutes':dict(yearly)}}
