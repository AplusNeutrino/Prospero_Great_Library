from __future__ import annotations
import hashlib,json

def make_event(entity_id,category,event,source,observed_at,local_date,data):
    basis=json.dumps([entity_id,event,source,observed_at,data],ensure_ascii=False,sort_keys=True)
    eid='evt_'+hashlib.sha1(basis.encode()).hexdigest()[:16]
    return {'id':eid,'observed_at':observed_at,'local_date':local_date,'entity_id':entity_id,'category':category,'event':event,'source':source,'data':data}
