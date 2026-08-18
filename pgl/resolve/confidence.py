from __future__ import annotations
from difflib import SequenceMatcher
from ..normalize.titles import normalize_title
from ..models import SourceRecord
from ..normalize.categories import classify_record

FAMILIES=[{'book','comic'},{'movie','drama','anime'},{'game'},{'music'}]

def compatible(a: str|None,b: str|None)->bool:
    if not a or not b: return True
    if a==b: return True
    return any(a in fam and b in fam for fam in FAMILIES)

def record_titles(r: SourceRecord):
    return [x for x in [r.title,r.title_original,*r.alternate_titles] if x]

def score_records(a: SourceRecord,b: SourceRecord)->tuple[float,str]:
    if a.source==b.source: return (0.0,'same_source')
    # durable source cross-links
    for key in ('bangumi_subject_id','steam_appid','neodb_item_id'):
        av=a.identifiers.get(key); bv=b.identifiers.get(key)
        if av is not None and bv is not None and str(av)==str(bv): return (1.0,f'id:{key}')
    for key in ('isbn13','isbn10','isbn'):
        av=str(a.identifiers.get(key) or '').replace('-',''); bv=str(b.identifiers.get(key) or '').replace('-','')
        if av and bv and av==bv: return (1.0,f'id:{key}')
    # a source may carry a cross-source URL identifier
    if a.source=='neodb' and a.identifiers.get('bangumi_subject_id') and b.source=='bangumi' and str(a.identifiers['bangumi_subject_id'])==str(b.source_id):
        return (1.0,'crosslink:bangumi')
    if b.source=='neodb' and b.identifiers.get('bangumi_subject_id') and a.source=='bangumi' and str(b.identifiers['bangumi_subject_id'])==str(a.source_id):
        return (1.0,'crosslink:bangumi')
    acat=classify_record(a)[0]; bcat=classify_record(b)[0]
    if not compatible(acat,bcat): return (0.0,'incompatible_category')
    if a.year and b.year and abs(int(a.year)-int(b.year))>1: return (0.0,'year_conflict')
    at=[normalize_title(x) for x in record_titles(a)]; bt=[normalize_title(x) for x in record_titles(b)]
    at=[x for x in at if x]; bt=[x for x in bt if x]
    if set(at)&set(bt):
        return (0.97 if a.year and b.year else 0.955,'exact_title')
    best=0.0
    for x in at:
        for y in bt:
            best=max(best,SequenceMatcher(None,x,y).ratio())
    # Fuzzy matches deliberately top out below automatic threshold unless supporting year is present.
    if best>=0.90:
        score=min(0.949, 0.80 + (best-0.90)*1.49 + (0.05 if a.year and b.year else 0))
        return (round(score,4),'fuzzy_title')
    return (round(best*0.88,4),'weak_title')
