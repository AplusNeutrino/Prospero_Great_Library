from __future__ import annotations
import json, hashlib, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def short_hash(value: str, n: int = 10) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:n]

def load_json(path: str | Path, default: Any):
    p=Path(path)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError): return default

def atomic_json(path: str | Path, data: Any) -> None:
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    payload=json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    fd,tmp=tempfile.mkstemp(prefix=p.name+".", dir=p.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as f: f.write(payload)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def safe_http_url(value):
    if not value: return None
    try:
        u=urlparse(str(value))
        return str(value) if u.scheme in ("http","https") and u.netloc else None
    except Exception:
        return None
