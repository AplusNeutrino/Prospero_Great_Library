from __future__ import annotations
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .events import make_event

def local_date(observed_at, timezone_name):
    dt=datetime.fromisoformat(observed_at.replace('Z','+00:00')).astimezone(ZoneInfo(timezone_name))
    return dt.date().isoformat()

def diff_libraries(previous,current,observed_at,timezone_name='UTC'):
    prev={x['id']:x for x in previous.get('items',[]) if x.get('id')}
    cur={x['id']:x for x in current.get('items',[]) if x.get('id')}
    date=local_date(observed_at,timezone_name); events=[]
    for cid,new in cur.items():
        old=prev.get(cid); cat=new.get('category')
        if not old:
            events.append(make_event(cid,cat,'entity_first_seen',None,observed_at,date,{'title':new.get('title')})); continue
        for field,event in [('status','status_changed'),('category','category_changed')]:
            if old.get(field)!=new.get(field):
                events.append(make_event(cid,cat,event,new.get('_provenance',{}).get(field),observed_at,date,{'title':new.get('title'),'from':old.get(field),'to':new.get(field)}))
        orat=(old.get('rating') or {}).get('normalized_10'); nrat=(new.get('rating') or {}).get('normalized_10')
        if orat!=nrat:
            events.append(make_event(cid,cat,'rating_changed',(new.get('rating') or {}).get('source'),observed_at,date,{'title':new.get('title'),'from':orat,'to':nrat}))
        op=(old.get('progress') or {}); np=(new.get('progress') or {})
        if (op.get('current'),op.get('total')) != (np.get('current'),np.get('total')):
            events.append(make_event(cid,cat,'progress_changed',np.get('source'),observed_at,date,{'title':new.get('title'),'from':op.get('current'),'to':np.get('current'),'total':np.get('total'),'unit':np.get('unit')}))
        os=set((old.get('sources') or {}).keys()); ns=set((new.get('sources') or {}).keys())
        for s in sorted(ns-os): events.append(make_event(cid,cat,'source_attached',s,observed_at,date,{'title':new.get('title'),'source':s}))
        for s in sorted(os-ns): events.append(make_event(cid,cat,'source_detached',s,observed_at,date,{'title':new.get('title'),'source':s}))
        ost=((old.get('telemetry') or {}).get('steam') or {}); nst=((new.get('telemetry') or {}).get('steam') or {})
        if ost or nst:
            ov=int(ost.get('playtime_minutes') or 0); nv=int(nst.get('playtime_minutes') or 0)
            if nv>ov:
                events.append(make_event(cid,cat,'steam_playtime_delta','steam',observed_at,date,{'title':new.get('title'),'from_minutes':ov,'to_minutes':nv,'delta_minutes':nv-ov}))
            elif nv<ov:
                events.append(make_event(cid,cat,'steam_playtime_correction','steam',observed_at,date,{'title':new.get('title'),'from_minutes':ov,'to_minutes':nv}))
            oa=(ost.get('achievements') or {}); na=(nst.get('achievements') or {})
            if oa.get('unlocked') != na.get('unlocked') and na:
                events.append(make_event(cid,cat,'steam_achievement_progress','steam',observed_at,date,{'title':new.get('title'),'from_unlocked':oa.get('unlocked'),'to_unlocked':na.get('unlocked'),'total':na.get('total')}))
    return events
