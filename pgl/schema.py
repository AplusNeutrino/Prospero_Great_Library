from __future__ import annotations
from typing import Any
from .models import CATEGORIES, STATUSES

class SchemaError(ValueError):
    pass

def validate_library(doc: dict[str, Any]) -> None:
    if doc.get("schema_version") != 1:
        raise SchemaError("library.schema_version must be 1")
    items = doc.get("items")
    if not isinstance(items, list):
        raise SchemaError("library.items must be a list")
    seen: set[str] = set()
    for i, item in enumerate(items):
        cid = item.get("id")
        if not isinstance(cid, str) or not cid:
            raise SchemaError(f"items[{i}].id missing")
        if cid in seen:
            raise SchemaError(f"duplicate canonical id: {cid}")
        seen.add(cid)
        if item.get("category") not in CATEGORIES:
            raise SchemaError(f"invalid category for {cid}: {item.get('category')}")
        status = item.get("status")
        if status is not None and status not in STATUSES:
            raise SchemaError(f"invalid status for {cid}: {status}")
        if item["category"] == "movie" and "performance" in item.get("tags", []):
            pass
        if item["category"] == "anime" and "performance" in item.get("tags", []):
            raise SchemaError(f"anime entity cannot be performance: {cid}")
        if item.get("privacy", {}).get("hidden"):
            raise SchemaError(f"hidden entity leaked into public library: {cid}")
