from __future__ import annotations
from abc import ABC, abstractmethod
import random, time
from typing import Any
import httpx
from ..models import SourceRecord

class AdapterError(RuntimeError): pass
class CapabilityUnavailable(AdapterError): pass
class PrivacyBoundaryUnavailable(AdapterError): pass

class SourceAdapter(ABC):
    name: str
    def __init__(self, config: dict[str, Any], token: str | None = None):
        self.config=config; self.token=token

    @abstractmethod
    def fetch_collections(self) -> list[SourceRecord]: ...

    def healthcheck(self) -> dict[str, Any]:
        return {"source": self.name, "ok": True}

    def _get_json(self, url: str, *, headers=None, params=None, retries: int = 3) -> Any:
        headers = headers or {}
        timeout=httpx.Timeout(20.0, connect=10.0)
        last=None
        for attempt in range(retries):
            try:
                with httpx.Client(timeout=timeout, follow_redirects=True) as c:
                    r=c.get(url, headers=headers, params=params)
                if r.status_code == 429:
                    retry=float(r.headers.get('Retry-After','1') or 1)
                    time.sleep(min(retry,10)); continue
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, ValueError) as exc:
                last=exc
                if attempt+1 < retries:
                    time.sleep((2**attempt)*0.5 + random.random()*0.2)
        raise AdapterError(f"{self.name} request failed: {last}")
    def _get_text(self, url: str, *, headers=None, params=None, retries: int = 3) -> str:
        headers = headers or {}
        timeout=httpx.Timeout(20.0, connect=10.0)
        last=None
        for attempt in range(retries):
            try:
                with httpx.Client(timeout=timeout, follow_redirects=True) as c:
                    r=c.get(url, headers=headers, params=params)
                if r.status_code == 429:
                    retry=float(r.headers.get('Retry-After','1') or 1)
                    time.sleep(min(retry,10)); continue
                r.raise_for_status()
                return r.text
            except httpx.HTTPError as exc:
                last=exc
                if attempt+1 < retries:
                    time.sleep((2**attempt)*0.5 + random.random()*0.2)
        raise AdapterError(f"{self.name} request failed: {last}")
