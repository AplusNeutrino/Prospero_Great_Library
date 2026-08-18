from pgl.history.diff import diff_libraries

def test_steam_positive_delta_and_status():
    old={'items':[{'id':'game:a','category':'game','status':'in_progress','rating':None,'progress':None,'sources':{'bangumi':{},'steam':{}},'telemetry':{'steam':{'playtime_minutes':100}}}]}
    new={'items':[{'id':'game:a','category':'game','status':'completed','rating':None,'progress':None,'sources':{'bangumi':{},'steam':{}},'telemetry':{'steam':{'playtime_minutes':160}},'_provenance':{'status':'bangumi'}}]}
    ev=diff_libraries(old,new,'2026-08-18T00:00:00Z','UTC')
    names={x['event'] for x in ev}
    assert 'status_changed' in names and 'steam_playtime_delta' in names
    delta=next(x for x in ev if x['event']=='steam_playtime_delta')
    assert delta['data']['delta_minutes']==60

def test_negative_playtime_is_correction():
    old={'items':[{'id':'game:a','category':'game','status':None,'rating':None,'progress':None,'sources':{'steam':{}},'telemetry':{'steam':{'playtime_minutes':160}}}]}
    new={'items':[{'id':'game:a','category':'game','status':None,'rating':None,'progress':None,'sources':{'steam':{}},'telemetry':{'steam':{'playtime_minutes':100}},'_provenance':{}}]}
    ev=diff_libraries(old,new,'2026-08-18T00:00:00Z','UTC')
    assert any(x['event']=='steam_playtime_correction' for x in ev)
    assert not any(x['event']=='steam_playtime_delta' for x in ev)

def test_history_change_event_carries_title_for_timeline():
    old={'items':[{'id':'book:a','category':'book','title':'Book A','status':'wishlist','rating':None,'progress':None,'sources':{},'telemetry':{}}]}
    new={'items':[{'id':'book:a','category':'book','title':'Book A','status':'completed','rating':None,'progress':None,'sources':{},'telemetry':{},'_provenance':{'status':'bangumi'}}]}
    ev=diff_libraries(old,new,'2026-08-18T00:00:00Z','UTC')
    row=next(x for x in ev if x['event']=='status_changed')
    assert row['data']['title']=='Book A'
