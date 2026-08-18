from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import yaml

DEFAULTS: dict[str, Any] = {
    "enabled": True,
    "locale": "zh-CN",
    "page": {"permalink": "/library/"},
    "sources": {
        "bangumi": {"enabled": False, "username": "", "base_url": "https://api.bgm.tv"},
        "neodb": {"enabled": False, "instance": "https://neodb.social", "mode": "public", "username": "", "collection_endpoint": "", "authenticated_shelf_endpoint": "/api/me/shelf/{shelf}", "shelf_types": ["wishlist","progress","complete","dropped"]},
        "steam": {"enabled": False, "steam_id": "", "fetch_achievements": False},
    },
    "precedence": {k: ["bangumi", "neodb"] for k in ("book","comic","movie","drama","anime","music")},
    "categories": {"order": ["book","comic","movie","drama","anime","game","music"]},
    "sync": {"timezone": "Asia/Shanghai", "on_deploy": True, "daily": True, "preserve_last_good": True},
    "history": {"enabled": True, "partition": "year", "steam_playtime_deltas": True},
    "association": {"enabled": True, "exact": True, "fuzzy": True, "auto_threshold": 0.95, "suggest_threshold": 0.80, "auto_edit_posts": False},
    "privacy": {"enabled": True, "hide_items": [], "hide_sources": [], "stats_only_items": []},
    "ui": {"layout": "grid", "allow_grid_list_toggle": True, "drawer": True, "lazy_render": True, "show_stats": True, "show_timeline": True, "show_sources": True, "show_steam_playtime": True, "show_achievements": True},
}

def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out

def load_config(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    raw: dict[str, Any] = {}
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        raw = data.get("prospero_great_library", data.get("personal_library", {})) or {}
    return deep_merge(DEFAULTS, raw)

def secret(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None
