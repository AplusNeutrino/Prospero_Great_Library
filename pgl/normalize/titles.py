from __future__ import annotations
import re
import unicodedata

SPACE = re.compile(r"\s+")
PUNCT = re.compile(r"[\s\-–—_:：·・/\\|.,，。'\"“”‘’!?！？()（）\[\]【】{}]+")
POST_PREFIX = re.compile(r"^(游戏记录|阅读记录|观影记录|动画记录|书评|影评|剧评|漫评|音乐记录)\s*[:：\-–—]?\s*", re.I)

def normalize_title(value: str | None) -> str:
    if not value:
        return ""
    s = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    s = PUNCT.sub("", s)
    return s

def clean_post_title(value: str | None) -> str:
    if not value:
        return ""
    s = unicodedata.normalize("NFKC", str(value)).strip()
    s = POST_PREFIX.sub("", s)
    return SPACE.sub(" ", s).strip()
