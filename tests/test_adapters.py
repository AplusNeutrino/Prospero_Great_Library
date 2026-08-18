from pgl.adapters.bangumi import BangumiAdapter
from pgl.adapters.steam import SteamAdapter
from pgl.adapters.neodb import NeoDBAdapter

def test_bangumi_collection_normalization():
    raw={'subject_id':42,'subject_type':2,'rate':9,'type':3,'comment':'x','ep_status':4,'updated_at':'2026-08-18T00:00:00Z','subject':{'id':42,'type':2,'name':'原名','name_cn':'中文名','date':'2024-01-01','eps':12,'images':{'large':'https://x'}}}
    r=BangumiAdapter.normalize_collection(raw)
    assert r.category_hint=='anime' and r.status=='in_progress'
    assert r.rating.normalized_10==9 and r.progress.current==4 and r.progress.total==12

def test_steam_game_normalization():
    r=SteamAdapter.normalize_game({'appid':39140,'name':'FINAL FANTASY','playtime_forever':600,'rtime_last_played':123},{'appid':39140,'playtime_2weeks':30})
    assert r.category_hint=='game'
    assert r.telemetry['steam']['playtime_minutes']==600
    assert r.telemetry['steam']['recent_playtime_minutes']==30
    assert r.status is None

def test_neodb_performance_normalization():
    r=NeoDBAdapter.normalize_item({'item':{'id':'x','type':'performance','title':'Hamlet','url':'https://example/performance/x'},'status':'complete','rating':4.5,'rating_scale':5})
    assert r.category_hint=='performance'
    assert 'performance' in r.tags
    assert r.status=='completed' and r.rating.normalized_10==9

def test_steam_last_played_is_iso_utc():
    r=SteamAdapter.normalize_game({'appid':1,'name':'X','playtime_forever':1,'rtime_last_played':1})
    assert r.telemetry['steam']['last_played_at']=='1970-01-01T00:00:01Z'

def test_neodb_authenticated_shelf_paginates_and_maps_status(monkeypatch):
    adapter=NeoDBAdapter({'mode':'authenticated','instance':'https://neodb.social','shelf_types':['progress'],'authenticated_shelf_endpoint':'/api/me/shelf/{shelf}'},token='x')
    calls=[]
    def fake(url,headers=None,params=None,retries=3):
        page=params['page']; calls.append(page)
        return {'pages':2,'data':[{'shelf_type':'progress','item':{'id':f'b{page}','type':'book','title':f'Book {page}','url':f'https://neodb.social/book/b{page}'}}]}
    monkeypatch.setattr(adapter,'_get_json',fake)
    rows=adapter.fetch_collections()
    assert calls==[1,2]
    assert [x.status for x in rows]==['in_progress','in_progress']

def test_neodb_real_shelf_shape_uses_category_and_user_rating_not_community():
    entry={
        'shelf_type':'complete','rating_grade':8,'created_time':'2026-01-02T03:04:05Z','tags':[],
        'item':{'uuid':'tv1','type':'TVSeason','category':'tv','url':'/tv/season/tv1','display_title':'Example','orig_title':'Original','other_title':['Alias'],'year':2025,'genre':['动画'],'rating':9.7,'rating_count':100}
    }
    r=NeoDBAdapter.normalize_item(entry,'https://neodb.social',10)
    assert r.category_hint=='drama'  # classifier upgrades to anime from genre, adapter keeps source-native category hint
    assert r.rating.normalized_10==8
    assert r.extra['community_rating']==9.7
    assert r.links['neodb']=='https://neodb.social/tv/season/tv1'
    assert r.title_original=='Original' and 'Alias' in r.alternate_titles
