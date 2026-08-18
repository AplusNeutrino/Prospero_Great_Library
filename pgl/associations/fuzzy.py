from __future__ import annotations
from difflib import SequenceMatcher
from ..normalize.titles import normalize_title, clean_post_title

def best_fuzzy(post, items):
    pt=normalize_title(clean_post_title(post.get('title')))
    if not pt: return None
    best=None
    post_tags={normalize_title(str(t)) for t in (post.get('tags') or [])}
    for item in items:
        titles=[item.get('title'),item.get('title_original'),*(item.get('alternate_titles') or [])]
        scores=[]
        for t in titles:
            nt=normalize_title(t)
            if not nt: continue
            if nt==pt: ratio=.97
            elif nt in pt or pt in nt: ratio=.955 if min(len(nt),len(pt))>=4 else .85
            else: ratio=SequenceMatcher(None,pt,nt).ratio()
            scores.append(ratio)
        if not scores: continue
        score=max(scores)
        aliases={normalize_title(str(x)) for x in titles if x}
        if post_tags & aliases: score=min(1.0,score+.02)
        if best is None or score>best[0]: best=(score,item)
    return best
