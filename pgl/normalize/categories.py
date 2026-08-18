from __future__ import annotations
from typing import Iterable
from ..models import SourceRecord

ANIME_WORDS = ("anime", "animation", "animated", "动画", "動畫", "アニメ")
COMIC_WORDS = ("comic", "manga", "漫画", "コミック", "manhua", "manhwa")
DRAMA_WORDS = ("tv", "电视剧", "剧集", "连续剧", "drama", "series")
PERFORMANCE_WORDS = ("performance", "opera", "stage play", "musical", "歌剧", "舞台剧", "音乐剧", "演出")
GAME_WORDS = ("game", "游戏")
MUSIC_WORDS = ("music", "音乐", "album", "专辑")

def _evidence_blob(r: SourceRecord) -> str:
    # Type classification must not be triggered merely because a title happens to contain
    # words such as "anime", "game", or "TV". Use source-native tags/type/extra evidence.
    parts = [" ".join(r.tags), str(r.raw_type or ""), str(r.extra)]
    return " ".join(parts).casefold()

def has_words(text: str, words: Iterable[str]) -> bool:
    return any(w.casefold() in text for w in words)

def classify_record(r: SourceRecord) -> tuple[str, list[str]]:
    hint = (r.category_hint or "").casefold()
    blob = _evidence_blob(r)
    tags = list(dict.fromkeys(r.tags))

    if r.source == "steam" or hint == "game" or has_words(blob, GAME_WORDS) and hint not in {"book","movie"}:
        return "game", tags
    if hint == "anime" or has_words(blob, ANIME_WORDS):
        return "anime", tags
    if hint == "comic" or (hint == "book" and has_words(blob, COMIC_WORDS)):
        return "comic", tags
    if hint in {"performance"} or has_words(blob, PERFORMANCE_WORDS):
        if "performance" not in tags:
            tags.append("performance")
        return "movie", tags
    if hint == "drama" or (hint == "movie" and has_words(blob, DRAMA_WORDS)):
        return "drama", tags
    if hint == "movie":
        return "movie", tags
    if hint == "book":
        return "book", tags
    if hint == "music" or has_words(blob, MUSIC_WORDS):
        return "music", tags
    return hint if hint in {"book","comic","movie","drama","anime","game","music"} else "book", tags

def choose_group_category(records: list[SourceRecord]) -> tuple[str, list[str]]:
    classified = [(r, *classify_record(r)) for r in records]
    # Trusted source-aware evidence. Game first prevents telemetry from being stolen by textual hints.
    for wanted in ("game", "anime", "comic", "drama"):
        if any(cat == wanted for _, cat, _ in classified):
            return wanted, _union_tags(classified)
    if any("performance" in tags for _, _, tags in classified):
        tags = _union_tags(classified)
        if "performance" not in tags: tags.append("performance")
        return "movie", tags
    for wanted in ("movie", "book", "music"):
        if any(cat == wanted for _, cat, _ in classified):
            return wanted, _union_tags(classified)
    return "book", _union_tags(classified)

def _union_tags(classified):
    out=[]
    for _, _, tags in classified:
        for tag in tags:
            if tag not in out: out.append(tag)
    return out
