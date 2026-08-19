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

def test_bangumi_accepts_paged_collection_response(monkeypatch):
    adapter=BangumiAdapter({'username':'demo_user','base_url':'https://api.bgm.tv'},token='x')
    calls=[]
    def fake(url,headers=None,params=None,retries=3):
        offset=params['offset']; calls.append(offset)
        rows=[] if offset else [{'subject_id':42,'subject_type':2,'type':2,'subject':{'id':42,'type':2,'name':'Example'}}]
        return {'total':1,'limit':50,'offset':offset,'data':rows}
    monkeypatch.setattr(adapter,'_get_json',fake)
    rows=adapter.fetch_collections()
    assert calls==[0]
    assert [row.source_id for row in rows]==['42']


def test_bangumi_slim_subject_tags_feed_comic_classifier():
    from pgl.normalize.categories import classify_record
    raw = {
        'subject_id': 1001,
        'subject_type': 1,
        'type': 2,
        'subject': {
            'id': 1001,
            'type': 1,
            'name': 'Example Manga',
            'tags': [{'name': '漫画', 'count': 500}, {'name': '少年漫画', 'count': 200}],
        },
    }
    record = BangumiAdapter.normalize_collection(raw)
    assert '漫画' in record.tags
    assert record.extra['subject_tags'] == ['漫画', '少年漫画']
    assert classify_record(record)[0] == 'comic'


def test_bangumi_explicit_book_category_1001_is_comic_hint():
    raw = {'subject_id': 1002, 'subject_type': 1, 'subject': {'id': 1002, 'type': 1, 'name': 'Comic', 'category': 1001}}
    record = BangumiAdapter.normalize_collection(raw)
    assert record.category_hint == 'comic'


def test_steam_game_uses_public_logo_or_icon_as_cover():
    logo = 'https://cdn.example/steam-logo.jpg'
    r = SteamAdapter.normalize_game({'appid': 10, 'name': 'X', 'img_icon_url': 'abc'}, public_meta={'logo': logo})
    assert r.cover_url == logo
    fallback = SteamAdapter.normalize_game({'appid': 11, 'name': 'Y', 'img_icon_url': 'def'})
    assert fallback.cover_url.endswith('/11/def.jpg')


def test_steam_public_visibility_filters_authenticated_query_to_public_appids(monkeypatch):
    adapter = SteamAdapter({'steam_id': '123', 'filter_private_games': True}, token='token')
    monkeypatch.setattr(adapter, 'fetch_public_games', lambda sid: {1: {'name': 'Public', 'logo': 'https://x/public.jpg', 'store_link': None}})
    calls=[]

    def fake_json(url, headers=None, params=None, retries=3):
        calls.append((url, params))
        if 'GetOwnedGames' in url:
            # Defensive test: even if upstream ignored appids_filter and returned
            # another game, PGL still drops it before SourceRecord creation.
            return {'response': {'games': [
                {'appid': 1, 'name': 'Public', 'playtime_forever': 10},
                {'appid': 2, 'name': 'Private', 'playtime_forever': 20},
            ]}}
        raise AssertionError('safe Steam mode must not call GetRecentlyPlayedGames')

    monkeypatch.setattr(adapter, '_get_json', fake_json)
    rows = adapter.fetch_collections()
    assert [x.source_id for x in rows] == ['1']
    assert rows[0].cover_url == 'https://x/public.jpg'
    params = calls[0][1]
    assert ('appids_filter[0]', 1) in params
    assert not any('GetRecentlyPlayedGames' in url for url, _ in calls)


def test_steam_public_games_xml_parser(monkeypatch):
    adapter = SteamAdapter({'steam_id': '123'}, token='token')
    xml = '<gamesList><games><game><appID>7</appID><name>Seven</name><logo>https://x/7.jpg</logo><storeLink>https://store.steampowered.com/app/7/</storeLink></game></games></gamesList>'
    monkeypatch.setattr(adapter, '_get_text', lambda *args, **kwargs: xml)
    games = adapter.fetch_public_games('123')
    assert games[7]['logo'] == 'https://x/7.jpg'


def test_steam_public_games_normalizes_http_urls(monkeypatch):
    adapter = SteamAdapter({'steam_id': '123'}, token='key')
    xml = '''<gamesList><games><game><appID>42</appID><name>Visible</name><logo>http://cdn.example/logo.jpg</logo><storeLink>http://store.steampowered.com/app/42/</storeLink></game></games></gamesList>'''
    monkeypatch.setattr(adapter, '_get_text', lambda *a, **k: xml)
    games = adapter.fetch_public_games('123')
    assert games[42]['logo'] == 'https://cdn.example/logo.jpg'
    assert games[42]['store_link'] == 'https://store.steampowered.com/app/42/'
