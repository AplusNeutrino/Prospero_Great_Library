from __future__ import annotations
from pathlib import Path
from typing import Any
import re, yaml

FRONT=re.compile(r'^---\s*\n(.*?)\n---\s*\n',re.S)

def parse_post(path: Path, site_root: Path) -> dict[str,Any]:
    text=path.read_text(encoding='utf-8',errors='replace')
    fm={}; body=text
    m=FRONT.match(text)
    if m:
        try: fm=yaml.safe_load(m.group(1)) or {}
        except Exception: fm={}
        body=text[m.end():]
    rel=path.relative_to(site_root).as_posix()
    url=fm.get('permalink')
    if not url:
        stem=path.stem
        stem=re.sub(r'^\d{4}-\d{2}-\d{2}-','',stem)
        url=f'/posts/{stem}/'
    return {'path':rel,'url':url,'title':str(fm.get('title') or path.stem),'tags':fm.get('tags') or [],'front_matter':fm,'body':body}

def scan_posts(site_root: str|Path):
    root=Path(site_root); posts=[]
    for ext in ('*.md','*.markdown'):
        for p in sorted((root/'_posts').glob('**/'+ext)) if (root/'_posts').exists() else []:
            posts.append(parse_post(p,root))
    return posts
