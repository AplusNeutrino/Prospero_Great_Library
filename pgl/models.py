from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

CATEGORIES = ("book", "comic", "movie", "drama", "anime", "game", "music")
STATUSES = ("wishlist", "in_progress", "completed", "on_hold", "dropped")

@dataclass(slots=True)
class Rating:
    value: float
    scale: float
    normalized_10: float
    source: str | None = None
    @classmethod
    def from_value(cls, value, scale, source=None):
        if value in (None, "") or not scale: return None
        val,scl=float(value),float(scale); return cls(val,scl,round(val/scl*10.0,4),source)
    def to_dict(self): return asdict(self)

@dataclass(slots=True)
class Progress:
    current: float | int | None = None
    total: float | int | None = None
    unit: str | None = None
    percent: float | None = None
    source: str | None = None
    def to_dict(self): return {k:v for k,v in asdict(self).items() if v is not None}

@dataclass(slots=True)
class SourceRecord:
    source: str
    source_id: str
    category_hint: str | None = None
    title: str = ""
    title_original: str | None = None
    alternate_titles: list[str] = field(default_factory=list)
    year: int | None = None
    release_date: str | None = None
    cover_url: str | None = None
    summary: str | None = None
    status: str | None = None
    rating: Rating | None = None
    progress: Progress | None = None
    tags: list[str] = field(default_factory=list)
    identifiers: dict[str, Any] = field(default_factory=dict)
    links: dict[str, str] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    updated_at: str | None = None
    raw_type: Any = None
    extra: dict[str, Any] = field(default_factory=dict)
    def to_dict(self):
        d=asdict(self)
        if self.rating: d['rating']=self.rating.to_dict()
        if self.progress: d['progress']=self.progress.to_dict()
        return d
    @classmethod
    def from_dict(cls,d):
        d=dict(d)
        if isinstance(d.get('rating'),dict): d['rating']=Rating(**d['rating'])
        if isinstance(d.get('progress'),dict): d['progress']=Progress(**d['progress'])
        return cls(**{k:v for k,v in d.items() if k in cls.__dataclass_fields__})
