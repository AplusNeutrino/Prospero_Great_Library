from __future__ import annotations
from typing import Any
from datetime import datetime, timezone
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

from .base import SourceAdapter, AdapterError, PrivacyBoundaryUnavailable
from ..models import SourceRecord

# XML 1.0 permits tab/LF/CR plus U+0020..D7FF, E000..FFFD and supplementary
# scalar values. Steam's deprecated Community XML surface has occasionally
# emitted control characters that strict XML parsers reject. Strip *only*
# characters XML 1.0 itself forbids; do not otherwise rewrite the document.
_XML10_FORBIDDEN = re.compile(
    '[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\uD800-\\uDFFF\\uFFFE\\uFFFF]'
)
_GAME_BLOCK = re.compile(r'<game(?:\s[^>]*)?>(.*?)</game\s*>', re.I | re.S)
_APP_ID = re.compile(r'<app(?:ID|id)>\s*(\d+)\s*</app(?:ID|id)>', re.I)
_GAMES_OPEN = re.compile(r'<games(?:\s[^>]*)?>', re.I)
_GAMES_CLOSE = re.compile(r'</games\s*>', re.I)
_ERROR_TAG = re.compile(r'<error(?:\s[^>]*)?>(.*?)</error\s*>', re.I | re.S)


class SteamAdapter(SourceAdapter):
    name = 'steam'
    api = 'https://api.steampowered.com'

    def fetch_collections(self) -> list[SourceRecord]:
        sid = self.config.get('steam_id')
        if not sid:
            raise AdapterError('Steam steam_id is required')
        if not self.token:
            raise AdapterError('STEAM_API_KEY is required')

        filter_private = self.config.get('filter_private_games', True) is not False
        public_games: dict[int, dict[str, Any]] | None = None
        if filter_private:
            try:
                public_games = self.fetch_public_games(str(sid))
            except Exception as exc:
                if self.config.get('privacy_fail_closed', True) is not False:
                    raise PrivacyBoundaryUnavailable(
                        f'Steam public visibility probe unavailable; refusing to publish authenticated owned-game data: {exc}'
                    ) from exc
                public_games = None

        params: Any = {
            'key': self.token,
            'steamid': sid,
            'include_appinfo': 1,
            'include_played_free_games': 1,
            'format': 'json',
        }
        if filter_private and public_games is not None:
            if not public_games:
                return []
            params = list(params.items())
            for index, appid in enumerate(sorted(public_games)):
                params.append((f'appids_filter[{index}]', appid))

        owned = self._get_json(f'{self.api}/IPlayerService/GetOwnedGames/v0001/', params=params)
        games = ((owned or {}).get('response') or {}).get('games') or []

        recent_map: dict[int, dict[str, Any]] = {}
        if not filter_private:
            try:
                recent = self._get_json(
                    f'{self.api}/IPlayerService/GetRecentlyPlayedGames/v0001/',
                    params={'key': self.token, 'steamid': sid, 'format': 'json'},
                )
                recent_map = {
                    int(g['appid']): g
                    for g in (((recent or {}).get('response') or {}).get('games') or [])
                    if g.get('appid') is not None
                }
            except Exception:
                recent_map = {}

        records: list[SourceRecord] = []
        for game in games:
            appid = int(game.get('appid', -1))
            if filter_private and public_games is not None and appid not in public_games:
                continue
            public_meta = public_games.get(appid) if public_games is not None else None
            records.append(self.normalize_game(game, recent_map.get(appid), public_meta=public_meta, private=False))

        if self.config.get('fetch_achievements', False):
            recent_ids = {
                int(rec.source_id)
                for rec in records
                if int((rec.telemetry.get('steam') or {}).get('recent_playtime_minutes') or 0) > 0
            }
            for rec in records:
                appid = int(rec.source_id)
                if rec.extra.get('private') is True:
                    continue
                if appid in recent_ids and rec.extra.get('has_community_visible_stats'):
                    ach = self.fetch_achievements(appid)
                    if ach:
                        rec.telemetry.setdefault('steam', {})['achievements'] = ach
        return records

    def fetch_public_games(self, steam_id: str) -> dict[int, dict[str, Any]]:
        """Return games visible on the anonymous Steam Community games page.

        Privacy semantics are intentionally fail-closed. Parsing is tolerant
        only in ways that cannot widen the public AppID set:

        1. strict XML parsing;
        2. removal of XML-1.0-forbidden control characters and strict retry;
        3. conservative recovery of numeric AppIDs from complete ``<game>``
           blocks inside an explicit ``<games>...</games>`` container.

        The recovery path does not trust names, logos, or URLs. Those fields
        continue to come from authenticated GetOwnedGames when possible. If the
        response is HTML, structurally incomplete, or otherwise cannot prove a
        public games container, the adapter still fails closed.
        """
        template = self.config.get(
            'public_games_url',
            'https://steamcommunity.com/profiles/{steam_id}/games?tab=all&xml=1',
        )
        url = str(template).format(steam_id=quote(str(steam_id), safe=''))
        text = self._get_text(url, headers={'User-Agent': 'Prospero_Great_Library/0.1'})

        root = self._parse_public_games_xml(text)
        if root is not None:
            error = root.findtext('.//error')
            if error and error.strip():
                raise AdapterError(f'Steam public games unavailable: {error.strip()}')
            games_container = root.find('.//games')
            if games_container is None:
                raise AdapterError('Steam public games XML did not contain a games list')
            visible: dict[int, dict[str, Any]] = {}
            for game in games_container.findall('./game'):
                raw_appid = game.findtext('appID') or game.findtext('appid')
                try:
                    appid = int(raw_appid or '')
                except (TypeError, ValueError):
                    continue
                visible[appid] = {
                    'name': (game.findtext('name') or '').strip() or None,
                    'logo': self._https_url(game.findtext('logo')),
                    'store_link': self._https_url(game.findtext('storeLink')),
                }
            return visible

        # Strict parsing failed even after safe control-character cleanup.
        # Recover *only* the public membership signal required by the privacy
        # boundary. A malformed name such as "A & B" must not zero the entire
        # Steam source, but malformed/HTML structure must still fail closed.
        return self._recover_public_appids(text)

    @staticmethod
    def _parse_public_games_xml(text: str) -> ET.Element | None:
        try:
            return ET.fromstring(text)
        except ET.ParseError:
            cleaned = _XML10_FORBIDDEN.sub('', text)
            if cleaned == text:
                return None
            try:
                return ET.fromstring(cleaned)
            except ET.ParseError:
                return None

    @staticmethod
    def _recover_public_appids(text: str) -> dict[int, dict[str, Any]]:
        lowered = text.lstrip().lower()
        if lowered.startswith('<!doctype html') or '<html' in lowered[:512]:
            raise AdapterError('Steam public games response was HTML, not the public games XML surface')
        if not _GAMES_OPEN.search(text) or not _GAMES_CLOSE.search(text):
            raise AdapterError('Steam public games response did not contain a recoverable games list')
        error = _ERROR_TAG.search(text)
        if error and re.sub(r'<[^>]+>', '', error.group(1)).strip():
            raise AdapterError('Steam public games response contained an error')

        blocks = _GAME_BLOCK.findall(text)
        if not blocks:
            # A structurally present, empty <games></games> container is a
            # legitimate public library with zero visible games.
            open_match = _GAMES_OPEN.search(text)
            close_match = _GAMES_CLOSE.search(text)
            if open_match and close_match and close_match.start() >= open_match.end():
                inner = text[open_match.end():close_match.start()]
                if not inner.strip():
                    return {}
            raise AdapterError('Steam public games response contained no recoverable game entries')

        visible: dict[int, dict[str, Any]] = {}
        for block in blocks:
            match = _APP_ID.search(block)
            if not match:
                continue
            appid = int(match.group(1))
            if appid > 0:
                visible[appid] = {'name': None, 'logo': None, 'store_link': None}
        if not visible:
            raise AdapterError('Steam public games response contained no recoverable AppIDs')
        return visible

    @staticmethod
    def _https_url(value: Any) -> str | None:
        url = str(value or '').strip()
        if not url:
            return None
        if url.startswith('http://'):
            return 'https://' + url[len('http://'):]
        return url

    @staticmethod
    def _icon_url(appid: int, icon_hash: Any) -> str | None:
        icon = str(icon_hash or '').strip()
        if not icon:
            return None
        return f'https://media.steampowered.com/steamcommunity/public/images/apps/{appid}/{icon}.jpg'

    @staticmethod
    def normalize_game(game: dict[str, Any], recent: dict[str, Any] | None = None, *, public_meta: dict[str, Any] | None = None, private: bool = False) -> SourceRecord:
        appid = int(game.get('appid'))
        recent = recent or {}; public_meta = public_meta or {}
        telemetry = {
            'owned': True,
            'playtime_minutes': int(game.get('playtime_forever') or 0),
            'recent_playtime_minutes': int(recent.get('playtime_2weeks') or game.get('playtime_2weeks') or 0),
            'last_played_at': SteamAdapter._iso_epoch(game.get('rtime_last_played') or recent.get('rtime_last_played')),
        }
        cover_url = public_meta.get('logo') or SteamAdapter._icon_url(appid, game.get('img_icon_url'))
        return SourceRecord(
            source='steam', source_id=str(appid), category_hint='game',
            title=game.get('name') or public_meta.get('name') or f'Steam {appid}',
            cover_url=cover_url, identifiers={'steam_appid': appid},
            links={'steam': public_meta.get('store_link') or f'https://store.steampowered.com/app/{appid}/'},
            telemetry={'steam': telemetry},
            extra={'img_icon_url':game.get('img_icon_url'),'public_logo_url':public_meta.get('logo'),'has_community_visible_stats':game.get('has_community_visible_stats'),'private':bool(private)},
        )

    @staticmethod
    def _iso_epoch(value: Any) -> str | None:
        try: ts=int(value or 0)
        except (TypeError,ValueError): return None
        if ts <= 0: return None
        return datetime.fromtimestamp(ts,tz=timezone.utc).isoformat().replace('+00:00','Z')

    def fetch_achievements(self, appid: int) -> dict[str, Any] | None:
        if not self.token: return None
        sid=self.config.get('steam_id')
        try:
            data=self._get_json(f'{self.api}/ISteamUserStats/GetPlayerAchievements/v0001/',params={'key':self.token,'steamid':sid,'appid':appid,'l':'english','format':'json'})
            stats=(data or {}).get('playerstats') or {}; ach=stats.get('achievements') or []
            if not stats.get('success',bool(ach)): return None
            unlocked=sum(1 for a in ach if int(a.get('achieved') or 0)==1); total=len(ach)
            return {'unlocked':unlocked,'total':total,'percent':round(unlocked/total*100,2) if total else 0.0}
        except Exception:
            return None
