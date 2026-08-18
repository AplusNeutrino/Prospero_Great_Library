from __future__ import annotations
from typing import Any
from ..util import short_hash

def event_id(entity_id,event,observed_at,data):
    stable=f'{entity_id}|{event}|{observed_at}|{repr(sorted(data.items()))}'
    return 'evt_'+short_hash(stable,16)

def make_event(entity_id,category,event,source,observed_at,local_date,data):
    return {'id':event_id(entity_id,event,observed_at,data),'observed_at':observed_at,'local_date':local_date,'entity_id':entity_id,'category':category,'event':event,'source':source,'data':data}
