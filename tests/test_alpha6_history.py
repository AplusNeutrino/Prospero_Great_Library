from pgl.history.diff import diff_libraries


def _item(*, steam_minutes=None, steam_source=True):
    sources={'bangumi':{'present':True}}
    telemetry={}
    if steam_source:
        sources['steam']={'present':True}
    if steam_minutes is not None:
        telemetry={'steam':{'playtime_minutes':steam_minutes}}
    return {
        'id':'game:x','category':'game','title':'X','status':'completed',
        'rating':None,'progress':None,'sources':sources,'telemetry':telemetry,
    }


def test_steam_reattach_establishes_baseline_without_lifetime_delta():
    previous={'items':[_item(steam_minutes=None,steam_source=False)]}
    current={'items':[_item(steam_minutes=12000,steam_source=True)]}
    events=diff_libraries(previous,current,'2026-08-19T03:00:00Z','UTC')
    names=[event['event'] for event in events]
    assert 'source_attached' in names
    assert 'steam_playtime_delta' not in names
    assert 'steam_playtime_correction' not in names


def test_steam_delta_resumes_after_baseline_exists():
    previous={'items':[_item(steam_minutes=12000,steam_source=True)]}
    current={'items':[_item(steam_minutes=12120,steam_source=True)]}
    events=diff_libraries(previous,current,'2026-08-19T04:00:00Z','UTC')
    deltas=[event for event in events if event['event']=='steam_playtime_delta']
    assert len(deltas)==1
    assert deltas[0]['data']['delta_minutes']==120


def test_steam_detach_does_not_emit_negative_correction():
    previous={'items':[_item(steam_minutes=12000,steam_source=True)]}
    current={'items':[_item(steam_minutes=None,steam_source=False)]}
    events=diff_libraries(previous,current,'2026-08-19T05:00:00Z','UTC')
    names=[event['event'] for event in events]
    assert 'source_detached' in names
    assert 'steam_playtime_correction' not in names
