from __future__ import annotations
from typing import Any
from datetime import datetime, timezone
from .base import SourceAdapter, AdapterError
from ..models import SourceRecord

class SteamAdapter(SourceAdapter):
    name='steam'
    api='https://api.steampowered.com'

    def fetch_collections(self) -> list[SourceRecord]:
        sid=self.config.get('steam_id')
        if not sid: raise AdapterError('Steam steam_id is required')
        if not self.token: raise AdapterError('STEAM_API_KEY is required')
        params={'key':self.token,'steamid':sid,'include_appinfo':1,'include_played_free_games':1,'format':'json'}
        owned=self._get_json(f'{self.api}/IPlayerService/GetOwnedGames/v0001/', params=params)
        games=((owned or {}).get('response') or {}).get('games') or []
        recent_map={}
        try:
            recent=self._get_json(f'{self.api}/IPlayerService/GetRecentlyPlayedGames/v0001/', params={'key':self.token,'steamid':sid,'format':'json'})
            recent_map={int(g['appid']):g for g in (((recent or {}).get('response') or {}).get('games') or []) if g.get('appid') is not None}
        except Exception:
            recent_map={}
        records=[self.normalize_game(g,recent_map.get(int(g.get('appid',-1)))) for g in games]
        if self.config.get('fetch_achievements',False):
            # Conservative default: enrich recently played games only. This keeps API usage bounded.
            recent_ids=set(recent_map)
            for rec in records:
                appid=int(rec.source_id)
                if appid in recent_ids and rec.extra.get('has_community_visible_stats'):
                    ach=self.fetch_achievements(appid)
                    if ach:
                        rec.telemetry.setdefault('steam',{})['achievements']=ach
        return records

    @staticmethod
    def normalize_game(game: dict[str,Any], recent: dict[str,Any] | None=None) -> SourceRecord:
        appid=int(game.get('appid'))
        recent=recent or {}
        telemetry={
            'owned': True,
            'playtime_minutes': int(game.get('playtime_forever') or 0),
            'recent_playtime_minutes': int(recent.get('playtime_2weeks') or game.get('playtime_2weeks') or 0),
            'last_played_at': SteamAdapter._iso_epoch(game.get('rtime_last_played') or recent.get('rtime_last_played')),
        }
        return SourceRecord(source='steam',source_id=str(appid),category_hint='game',title=game.get('name') or f'Steam {appid}',
            identifiers={'steam_appid':appid}, links={'steam':f'https://store.steampowered.com/app/{appid}/'}, telemetry={'steam':telemetry},
            extra={'img_icon_url':game.get('img_icon_url'),'has_community_visible_stats':game.get('has_community_visible_stats')})

    @staticmethod
    def _iso_epoch(value: Any) -> str | None:
        try:
            ts=int(value or 0)
        except (TypeError,ValueError):
            return None
        if ts <= 0:
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace('+00:00','Z')

    def fetch_achievements(self, appid: int) -> dict[str,Any] | None:
        if not self.token: return None
        sid=self.config.get('steam_id')
        try:
            data=self._get_json(f'{self.api}/ISteamUserStats/GetPlayerAchievements/v0001/', params={'key':self.token,'steamid':sid,'appid':appid,'l':'english','format':'json'})
            stats=(data or {}).get('playerstats') or {}
            ach=stats.get('achievements') or []
            if not stats.get('success', bool(ach)): return None
            unlocked=sum(1 for a in ach if int(a.get('achieved') or 0)==1)
            total=len(ach)
            return {'unlocked':unlocked,'total':total,'percent':round(unlocked/total*100,2) if total else 0.0}
        except Exception:
            return None
