from __future__ import annotations
import re

BGM=re.compile(r'(?:bgm\.tv|bangumi\.tv)/subject/(\d+)',re.I)
STEAM=re.compile(r'store\.steampowered\.com/app/(\d+)',re.I)
NEODB=re.compile(r'https?://[^\s)\]}>]+/(?:book|movie|tv|game|music|performance)/[^\s)\]}>]+',re.I)
ISBN=re.compile(r'\b(?:97[89][\- ]?)?(?:\d[\- ]?){9}[\dXx]\b')

def find_exact(post, items):
    fm=post.get('front_matter') or {}; text=post.get('body','')
    lib=fm.get('library')
    requested=lib.get('id') if isinstance(lib,dict) else lib if isinstance(lib,str) else None
    if requested:
        x=next((i for i in items if i.get('id')==requested),None)
        if x: return x,1.0,'canonical_id'
    bgm={m.group(1) for m in BGM.finditer(text)}
    steam={m.group(1) for m in STEAM.finditer(text)}
    neodb={m.group(0).rstrip('.,') for m in NEODB.finditer(text)}
    isbns={re.sub(r'[^0-9Xx]','',m.group(0)).upper() for m in ISBN.finditer(text)}
    for item in items:
        ids=item.get('identifiers') or {}; links=item.get('links') or {}
        if str(ids.get('bangumi_subject_id') or '') in bgm and bgm: return item,1.0,'bangumi_url'
        if str(ids.get('steam_appid') or '') in steam and steam: return item,1.0,'steam_url'
        if links.get('neodb') in neodb and neodb: return item,1.0,'neodb_url'
        for key in ('isbn','isbn10','isbn13'):
            v=re.sub(r'[^0-9Xx]','',str(ids.get(key) or '')).upper()
            if v and v in isbns: return item,1.0,'isbn'
    return None
