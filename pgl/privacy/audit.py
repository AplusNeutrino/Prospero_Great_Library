from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..models import SourceRecord


class PrivacyViolation(RuntimeError):
    """Raised when a known-private record would reach a public artifact."""


@dataclass(slots=True)
class PrivacyContext:
    """Ephemeral privacy knowledge used while producing public artifacts.

    Private source identifiers are intentionally kept in memory only.  Persisting
    them would itself disclose which items a user marked private upstream.
    """

    hidden_entity_ids: set[str] = field(default_factory=set)
    stats_only_entity_ids: set[str] = field(default_factory=set)
    hidden_sources_global: set[str] = field(default_factory=set)
    hidden_sources_by_entity: dict[str, set[str]] = field(default_factory=dict)
    private_impacted_entities: dict[str, set[str]] = field(default_factory=dict)
    private_only_entities: set[str] = field(default_factory=set)


def filter_source_records(
    name: str,
    records: list[SourceRecord],
    source_config: dict[str, Any],
) -> tuple[list[SourceRecord], list[SourceRecord]]:
    """Remove upstream-private source records before snapshots or merging.

    V1 currently has native source-privacy semantics for Bangumi collections.
    The return value includes the hidden records only for this in-memory sync so
    prior public history can be scrubbed without persisting a private-ID index.
    """

    if name != "bangumi" or not source_config.get("hide_private_collections", True):
        return records, []
    public: list[SourceRecord] = []
    hidden: list[SourceRecord] = []
    for record in records:
        (hidden if record.extra.get("private") is True else public).append(record)
    return public, hidden


def _configured_entity_privacy(config: dict[str, Any], mappings: dict[str, Any]):
    cfg = config.get("privacy", {})
    hidden = {str(x) for x in cfg.get("hide_items", [])}
    stats_only = {str(x) for x in cfg.get("stats_only_items", [])}
    hidden_sources_global = {str(x) for x in cfg.get("hide_sources", [])}
    hidden_sources_by_entity: dict[str, set[str]] = {}

    for row in mappings.get("privacy", []):
        entity = str(row.get("entity") or "")
        if not entity:
            continue
        if row.get("hidden"):
            hidden.add(entity)
        if row.get("stats_only"):
            stats_only.add(entity)
        if row.get("hide_sources"):
            hidden_sources_by_entity.setdefault(entity, set()).update(
                str(x) for x in row.get("hide_sources", [])
            )
    return hidden, stats_only, hidden_sources_global, hidden_sources_by_entity


def _entities_for_source_ids(library: dict[str, Any], source: str, source_ids: set[str]) -> set[str]:
    out: set[str] = set()
    if not source_ids:
        return out
    for item in library.get("items", []):
        source_doc = (item.get("sources") or {}).get(source) or {}
        sid = source_doc.get("id", source_doc.get("appid"))
        if sid is not None and str(sid) in source_ids and item.get("id"):
            out.add(str(item["id"]))
    return out


def build_privacy_context(
    config: dict[str, Any],
    mappings: dict[str, Any],
    previous_library: dict[str, Any],
    public_items: list[dict[str, Any]],
    hidden_source_records: dict[str, list[SourceRecord]],
) -> PrivacyContext:
    hidden, stats_only, global_sources, per_entity_sources = _configured_entity_privacy(config, mappings)
    current_public_ids = {str(x.get("id")) for x in public_items if x.get("id")}
    private_impacted: dict[str, set[str]] = {}
    private_only: set[str] = set()

    for source, records in hidden_source_records.items():
        source_ids = {str(r.source_id) for r in records}
        impacted = _entities_for_source_ids(previous_library, source, source_ids)
        if impacted:
            private_impacted[source] = impacted
            private_only.update(impacted - current_public_ids)

    return PrivacyContext(
        hidden_entity_ids=hidden,
        stats_only_entity_ids=stats_only,
        hidden_sources_global=global_sources,
        hidden_sources_by_entity=per_entity_sources,
        private_impacted_entities=private_impacted,
        private_only_entities=private_only,
    )


def _event_source(event: dict[str, Any]) -> tuple[str | None, str | None]:
    source = event.get("source")
    data_source = (event.get("data") or {}).get("source")
    return (str(source) if source else None, str(data_source) if data_source else None)


def sanitize_history(
    events: Iterable[dict[str, Any]],
    context: PrivacyContext,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Remove historical records that would disclose hidden library information."""

    kept: list[dict[str, Any]] = []
    removed = Counter()
    private_by_entity: dict[str, set[str]] = {}
    for source, entity_ids in context.private_impacted_entities.items():
        for entity_id in entity_ids:
            private_by_entity.setdefault(entity_id, set()).add(source)

    for event in events:
        entity_id = str(event.get("entity_id") or "")
        source, data_source = _event_source(event)
        if entity_id in context.hidden_entity_ids:
            removed["hidden_entity"] += 1
            continue
        if entity_id in context.stats_only_entity_ids:
            removed["stats_only_entity"] += 1
            continue
        if entity_id in context.private_only_entities:
            removed["private_source_only_entity"] += 1
            continue

        hidden_sources = context.hidden_sources_global | context.hidden_sources_by_entity.get(entity_id, set())
        if source in hidden_sources or data_source in hidden_sources:
            removed["hidden_source"] += 1
            continue

        private_sources = private_by_entity.get(entity_id, set())
        if source in private_sources or data_source in private_sources:
            removed["private_source_event"] += 1
            continue

        kept.append(event)

    return kept, {
        "history_events_scrubbed": sum(removed.values()),
        "history_scrub_reasons": dict(sorted(removed.items())),
    }


def audit_public_payload(
    library: dict[str, Any],
    source_docs: dict[str, dict[str, Any]],
    history: Iterable[dict[str, Any]],
    config: dict[str, Any],
    context: PrivacyContext,
) -> list[dict[str, Any]]:
    """Return known privacy-boundary violations in artifacts intended for publication."""

    violations: list[dict[str, Any]] = []
    hide_bangumi_private = bool(
        config.get("sources", {}).get("bangumi", {}).get("hide_private_collections", True)
    )

    if hide_bangumi_private:
        for record in (source_docs.get("bangumi") or {}).get("records", []):
            if (record.get("extra") or {}).get("private") is True:
                violations.append({"artifact": "sources/bangumi", "reason": "private_record_present"})
        for item in library.get("items", []):
            bgm = (item.get("sources") or {}).get("bangumi") or {}
            if (bgm.get("extra") or {}).get("private") is True:
                violations.append({
                    "artifact": "library",
                    "entity_id": item.get("id"),
                    "reason": "private_bangumi_source_present",
                })

    private_by_entity: dict[str, set[str]] = {}
    for source, entity_ids in context.private_impacted_entities.items():
        for entity_id in entity_ids:
            private_by_entity.setdefault(entity_id, set()).add(source)

    for event in history:
        entity_id = str(event.get("entity_id") or "")
        source, data_source = _event_source(event)
        if entity_id in context.hidden_entity_ids or entity_id in context.stats_only_entity_ids:
            violations.append({"artifact": "history", "entity_id": entity_id, "reason": "hidden_entity_event"})
            continue
        if entity_id in context.private_only_entities:
            violations.append({"artifact": "history", "entity_id": entity_id, "reason": "private_only_entity_event"})
            continue
        hidden_sources = context.hidden_sources_global | context.hidden_sources_by_entity.get(entity_id, set())
        if source in hidden_sources or data_source in hidden_sources:
            violations.append({"artifact": "history", "entity_id": entity_id, "reason": "hidden_source_event"})
            continue
        private_sources = private_by_entity.get(entity_id, set())
        if source in private_sources or data_source in private_sources:
            violations.append({"artifact": "history", "entity_id": entity_id, "reason": "private_source_event"})

    return violations


def assert_public_payload_safe(*args, **kwargs) -> None:
    violations = audit_public_payload(*args, **kwargs)
    if violations:
        first = violations[0]
        raise PrivacyViolation(
            f"Privacy invariant failed with {len(violations)} violation(s); first={first}"
        )
