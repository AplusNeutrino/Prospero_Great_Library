from __future__ import annotations

from collections import Counter, defaultdict
from math import floor
from typing import Any, Iterable

CATEGORIES = ("book", "comic", "movie", "drama", "anime", "game", "music")
DEFAULT_BROWSE_STATUSES = ("in_progress", "completed")
RATING_BIN_SIZE = 0.5
RATING_BINS = tuple(round(i * RATING_BIN_SIZE, 1) for i in range(1, 21))


def _steam(item: dict[str, Any]) -> dict[str, Any]:
    return ((item.get("telemetry") or {}).get("steam") or {})


def _recent_playtime_minutes(item: dict[str, Any]) -> int:
    steam = _steam(item)
    return int(
        steam.get("recent_playtime_minutes")
        or steam.get("playtime_2weeks_minutes")
        or 0
    )


def _rating_bin(value: Any) -> float | None:
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None
    if rating <= 0:
        return None
    # Round half-up to the nearest 0.5. Python's round() uses bankers' rounding,
    # which is undesirable for deterministic catalogue bins.
    binned = floor(rating * 2.0 + 0.5) / 2.0
    return min(10.0, max(0.5, binned))


def _rating_curve(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    scopes: dict[str, list[int]] = {"all": [0] * len(RATING_BINS)}
    scopes.update({category: [0] * len(RATING_BINS) for category in CATEGORIES})
    for item in items:
        if item.get("status") not in DEFAULT_BROWSE_STATUSES:
            continue
        value = (item.get("rating") or {}).get("normalized_10")
        bucket = _rating_bin(value)
        if bucket is None:
            continue
        index = int(round(bucket / RATING_BIN_SIZE)) - 1
        if not 0 <= index < len(RATING_BINS):
            continue
        scopes["all"][index] += 1
        category = item.get("category")
        if category in scopes:
            scopes[category][index] += 1
    return {
        "bin_size": RATING_BIN_SIZE,
        "bins": list(RATING_BINS),
        "scopes": scopes,
    }


def _navigation(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    default = Counter({category: 0 for category in CATEGORIES})
    wishlist = Counter({category: 0 for category in CATEGORIES})
    other = {
        "on_hold": Counter({category: 0 for category in CATEGORIES}),
        "dropped": Counter({category: 0 for category in CATEGORIES}),
    }
    for item in items:
        category = item.get("category")
        if category not in CATEGORIES:
            continue
        status = item.get("status")
        if status in DEFAULT_BROWSE_STATUSES:
            default[category] += 1
        elif status == "wishlist":
            wishlist[category] += 1
        elif status in other:
            other[status][category] += 1
    return {
        "default_by_category": dict(default),
        "default_total": sum(default.values()),
        "wishlist_by_category": dict(wishlist),
        "wishlist_total": sum(wishlist.values()),
        "other_status_by_category": {status: dict(counts) for status, counts in other.items()},
    }


def _current_activity(items: Iterable[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    current_cfg = ((config.get("ui") or {}).get("current") or {})
    if current_cfg.get("enabled", True) is False:
        return []
    include_in_progress = current_cfg.get("include_all_in_progress", True) is not False
    include_steam_recent = current_cfg.get("include_steam_recent", True) is not False
    rows: list[dict[str, Any]] = []
    for item in items:
        reason = None
        if include_in_progress and item.get("status") == "in_progress":
            reason = "in_progress"
        elif include_steam_recent and item.get("category") == "game" and _recent_playtime_minutes(item) > 0:
            reason = "steam_recent"
        if reason is None:
            continue
        steam = _steam(item)
        last_activity = (
            steam.get("last_played_at")
            if reason == "steam_recent"
            else None
        ) or (item.get("timestamps") or {}).get("canonical_updated_at") or ""
        rows.append({
            "entity_id": item.get("id"),
            "reason": reason,
            "last_activity": last_activity,
            "recent_playtime_minutes": _recent_playtime_minutes(item) if item.get("category") == "game" else 0,
        })
    rows.sort(
        key=lambda row: (
            0 if row["reason"] == "in_progress" else 1,
            # ISO timestamps sort lexically; invert by using a secondary stable
            # sort pass to keep implementation explicit below.
            str(row.get("entity_id") or ""),
        )
    )
    # Sort each reason partition by activity descending while preserving the
    # explicit-in-progress-before-Steam-recent contract.
    rows.sort(key=lambda row: str(row.get("last_activity") or ""), reverse=True)
    rows.sort(key=lambda row: 0 if row["reason"] == "in_progress" else 1)
    return rows


def build_stats(
    items: list[dict[str, Any]],
    history_events: list[dict[str, Any]] | None = None,
    *,
    aggregate_items: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build public-facing statistics and UI navigation derivatives.

    ``items`` are identity-bearing public items and are the only records that
    may appear in navigation, current-activity or rankings. ``aggregate_items``
    may additionally contain ``stats_only`` records; those may contribute only
    anonymous aggregate counts/totals/distributions.
    """

    history_events = history_events or []
    config = config or {}
    aggregate = aggregate_items if aggregate_items is not None else items

    cats: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    ratings: Counter[str] = Counter()
    steam_total = 0
    for item in aggregate:
        category = item.get("category")
        if category:
            cats[category] += 1
        status = item.get("status")
        if status:
            statuses[status] += 1
        rating = (item.get("rating") or {}).get("normalized_10")
        if rating is not None:
            ratings[str(int(round(float(rating))))] += 1
        steam_total += int(_steam(item).get("playtime_minutes") or 0)

    # Ranking remains in the backwards-compatible stats schema, but uses only
    # public identity-bearing items so stats_only titles can never leak.
    steam_ranking = []
    for item in items:
        minutes = int(_steam(item).get("playtime_minutes") or 0)
        if minutes:
            steam_ranking.append({"id": item["id"], "title": item.get("title"), "minutes": minutes})
    steam_ranking.sort(key=lambda row: row["minutes"], reverse=True)

    yearly: defaultdict[str, int] = defaultdict(int)
    for event in history_events:
        if event.get("event") == "steam_playtime_delta":
            yearly[event.get("local_date", "")[:4]] += int((event.get("data") or {}).get("delta_minutes") or 0)

    return {
        "stats_schema_version": 2,
        "total_items": len(aggregate),
        "by_category": dict(cats),
        "by_status": dict(statuses),
        # Legacy integer distribution retained for one compatibility cycle.
        "rating_distribution": dict(sorted(ratings.items(), key=lambda pair: int(pair[0]))),
        "rating_curve_distribution": _rating_curve(aggregate),
        "navigation": _navigation(items),
        "current_activity": _current_activity(items, config),
        "steam": {
            "lifetime_playtime_minutes": steam_total,
            "ranking": steam_ranking,
            "observed_playtime_by_year_minutes": dict(yearly),
        },
    }
