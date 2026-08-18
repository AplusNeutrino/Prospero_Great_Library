from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from ..models import SourceRecord
from ..normalize.categories import classify_record
from .confidence import score_records
from .mappings import explicit_entity_for

@dataclass
class ResolutionResult:
    groups: list[list[SourceRecord]]
    diagnostics: dict[str,Any]

def apply_classification_overrides(records, mappings):
    idx={(m.get('source'),str(m.get('source_id'))):m.get('category') for m in mappings.get('classifications',[]) if m.get('source') and m.get('source_id') is not None}
    for r in records:
        cat=idx.get((r.source,str(r.source_id)))
        if cat: r.category_hint=cat

def resolve(records: list[SourceRecord], mappings: dict[str,Any], auto_threshold=.95, suggest_threshold=.80) -> ResolutionResult:
    apply_classification_overrides(records,mappings)
    groups: list[list[SourceRecord]]=[]
    explicit_groups={}
    diagnostics={'ambiguous':[],'auto_merged':[]}
    for r in records:
        eid=explicit_entity_for(r,mappings)
        if eid:
            explicit_groups.setdefault(eid,[]).append(r)
        else:
            best=None
            for gi,g in enumerate(groups):
                # One source record per source per canonical entity unless explicitly mapped.
                if any(x.source==r.source for x in g): continue
                scores=[score_records(r,x) for x in g]
                score,method=max(scores,key=lambda x:x[0]) if scores else (0,'')
                if best is None or score>best[0]: best=(score,method,gi)
            if best and best[0]>=auto_threshold:
                groups[best[2]].append(r)
                diagnostics['auto_merged'].append({'source':r.source,'source_id':r.source_id,'confidence':best[0],'method':best[1]})
            else:
                if best and best[0]>=suggest_threshold:
                    diagnostics['ambiguous'].append({'source':r.source,'source_id':r.source_id,'title':r.title,'candidate_group':best[2],'confidence':best[0],'method':best[1]})
                groups.append([r])
    # explicit mappings are authoritative; combine before ordinary groups if source IDs overlap
    for eid, eg in explicit_groups.items():
        attached=[]
        for i,g in enumerate(groups):
            if any((x.source,x.source_id)==(e.source,e.source_id) for x in g for e in eg): attached.append(i)
        merged=list(eg)
        for i in reversed(attached): merged.extend(groups.pop(i))
        groups.append(_unique(merged))
    return ResolutionResult(groups,diagnostics)

def _unique(records):
    out=[]; seen=set()
    for r in records:
        k=(r.source,str(r.source_id))
        if k not in seen: seen.add(k); out.append(r)
    return out
