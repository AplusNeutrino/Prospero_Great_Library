from __future__ import annotations
from typing import Any
from .base import SourceAdapter, AdapterError
from ..models import SourceRecord, Rating, Progress
from ..normalize.statuses import map_bangumi

TYPE_MAP={1:'book',2:'anime',3:'music',4:'game',6:'movie'}

class BangumiAdapter(SourceAdapter):
    name='bangumi'

    def _headers(self):
        h={'User-Agent':'Prospero_Great_Library/0.1 (+https://github.com/AplusNeutrino/Prospero_Great_Library)', 'Accept':'application/json'}
        if self.token: h['Authorization']=f'Bearer {self.token}'
        return h

    def fetch_collections(self) -> list[SourceRecord]:
        username=self.config.get('username')
        if not username: raise AdapterError('Bangumi username is required')
        base=self.config.get('base_url','https://api.bgm.tv').rstrip('/')
        out=[]; offset=0; limit=50
        while True:
            data=self._get_json(f'{base}/v0/users/{username}/collections', headers=self._headers(), params={'limit':limit,'offset':offset})
            if isinstance(data,list):
                rows=data; total=None
            elif isinstance(data,dict) and isinstance(data.get('data'),list):
                rows=data['data']; total=data.get('total')
            else:
                raise AdapterError('Unexpected Bangumi collections response')
            out.extend(self.normalize_collection(x) for x in rows)
            offset += len(rows)
            if not rows or len(rows)<limit or (isinstance(total,int) and offset>=total): break
        return out

    @staticmethod
    def normalize_collection(item: dict[str,Any]) -> SourceRecord:
        subject=item.get('subject') or {}
        sid=str(item.get('subject_id') or subject.get('id') or '')
        stype=item.get('subject_type') or subject.get('type')
        hint=TYPE_MAP.get(int(stype)) if str(stype).isdigit() else TYPE_MAP.get(stype)
        title=subject.get('name_cn') or subject.get('name') or f'Bangumi {sid}'
        original=subject.get('name') if subject.get('name') and subject.get('name') != title else None
        aliases=[]
        if original: aliases.append(original)
        date=subject.get('date')
        year=None
        if isinstance(date,str) and len(date)>=4 and date[:4].isdigit(): year=int(date[:4])
        images=subject.get('images') or {}
        rate=item.get('rate')
        rating=Rating.from_value(rate,10,'bangumi') if rate not in (None,0) else None
        progress=None
        ep=item.get('ep_status'); vol=item.get('vol_status')
        total_eps=subject.get('eps') or subject.get('total_episodes')
        if ep is not None or vol is not None:
            if hint in ('anime','movie','drama'):
                progress=Progress(current=ep,total=total_eps,unit='episode',source='bangumi')
            elif hint in ('book','comic'):
                progress=Progress(current=vol,unit='volume',source='bangumi')
            if progress and progress.current is not None and progress.total:
                try: progress.percent=round(float(progress.current)/float(progress.total)*100,2)
                except Exception: pass
        tags=list(item.get('tags') or [])
        # Surface platform/type metadata to classifier without inventing a second category hierarchy.
        platform=subject.get('platform')
        if platform: tags.append(str(platform))
        extra={'comment':item.get('comment'),'private':item.get('private'), 'platform':platform}
        return SourceRecord(
            source='bangumi', source_id=sid, category_hint=hint, title=title,
            title_original=original, alternate_titles=aliases, year=year, release_date=date,
            cover_url=images.get('large') or images.get('common') or images.get('medium'),
            summary=subject.get('short_summary') or subject.get('summary'), status=map_bangumi(item.get('type')),
            rating=rating, progress=progress, tags=list(dict.fromkeys(t for t in tags if t)),
            identifiers={'bangumi_subject_id':int(sid) if sid.isdigit() else sid},
            links={'bangumi':f'https://bgm.tv/subject/{sid}'}, updated_at=item.get('updated_at'), raw_type=stype, extra=extra)
