from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml

def load_mappings(path: str | Path) -> dict[str, Any]:
    p=Path(path)
    if not p.exists(): return {"entities":[],"classifications":[],"articles":[],"privacy":[]}
    data=yaml.safe_load(p.read_text(encoding='utf-8')) or {}
    return {k:data.get(k,[]) or [] for k in ("entities","classifications","articles","privacy")}

def explicit_entity_for(record, mappings):
    for m in mappings.get('entities',[]):
        val=m.get(record.source)
        if val is not None and str(val)==str(record.source_id): return m.get('id')
    return None
