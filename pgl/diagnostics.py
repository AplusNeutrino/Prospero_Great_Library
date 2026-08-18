from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(slots=True)
class Diagnostic:
    level: str
    code: str
    message: str
    source: str | None = None
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v not in (None, {}, [])}
