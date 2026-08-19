import pytest
from pgl.adapters.steam import SteamAdapter
from pgl.adapters.base import AdapterError


def adapter_with(text):
    adapter=SteamAdapter({'steam_id':'123'},token='key')
    adapter._get_text=lambda *a,**k:text
    return adapter


def test_illegal_xml10_control_character_is_safely_removed():
    xml='<gamesList><games><game><appID>7</appID><name>Bad\x0bName</name></game></games></gamesList>'
    games=adapter_with(xml).fetch_public_games('123')
    assert list(games)==[7]
    assert games[7]['name']=='BadName'


def test_unescaped_ampersand_falls_back_to_appid_only_recovery():
    xml='<gamesList><games><game><appID>42</appID><name>A & B</name><logo>https://x/42.jpg</logo></game></games></gamesList>'
    games=adapter_with(xml).fetch_public_games('123')
    assert games=={42:{'name':None,'logo':None,'store_link':None}}


def test_recovery_rejects_html_or_missing_games_container():
    with pytest.raises(AdapterError):
        adapter_with('<html><body><appID>42</appID></body></html>').fetch_public_games('123')


def test_recovery_accepts_structurally_empty_games_container():
    xml='<gamesList><games></games></gamesList>'
    assert adapter_with(xml).fetch_public_games('123')=={}


def test_recovery_never_infers_appid_from_outside_complete_game_block():
    xml='<gamesList><games><appID>999</appID><game><name>Broken & Name</name></game></games></gamesList>'
    with pytest.raises(AdapterError):
        adapter_with(xml).fetch_public_games('123')


def test_recovery_rejects_html_even_if_it_contains_game_like_tags():
    html='<!doctype html><html><body><games><game><appID>42</appID></game></games></body></html>'
    with pytest.raises(AdapterError):
        adapter_with(html).fetch_public_games('123')


def test_malformed_public_xml_recovery_still_filters_owned_games(monkeypatch):
    malformed='<gamesList><games><game><appID>7</appID><name>A & B</name></game></games></gamesList>'
    adapter=SteamAdapter({'steam_id':'123','filter_private_games':True},token='token')
    monkeypatch.setattr(adapter,'_get_text',lambda *a,**k:malformed)
    calls=[]
    def fake_json(url,headers=None,params=None,retries=3):
        calls.append((url,params))
        return {'response':{'games':[
            {'appid':7,'name':'Public Game','playtime_forever':600,'playtime_2weeks':30},
            {'appid':8,'name':'Should Be Filtered','playtime_forever':999},
        ]}}
    monkeypatch.setattr(adapter,'_get_json',fake_json)
    records=adapter.fetch_collections()
    assert [r.source_id for r in records]==['7']
    assert records[0].telemetry['steam']['playtime_minutes']==600
    assert records[0].telemetry['steam']['recent_playtime_minutes']==30
    assert ('appids_filter[0]',7) in calls[0][1]
