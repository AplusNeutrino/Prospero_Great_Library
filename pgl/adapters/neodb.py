from __future__ import annotations
from typing import Any
from urllib.parse import urljoin
from .base import SourceAdapter, AdapterError, CapabilityUnavailable
from ..models import SourceRecord, Rating, Progress
from ..normalize.statuses import map_neodb

TYPE_HINTS={'book':'book','movie':'movie','tv':'drama','tvshow':'drama','performance':'performance','game':'game','music':'music','album':'music'}

class NeoDBAdapter(SourceAdapter):
    name='neodb'

    def _headers(self):
        h={'Accept':'application/json','User-Agent':'Prospero_Great_Library/0.1'}
        if self.token: h['Authorization']=f'Bearer {self.token}'
        return h

    def fetch_collections(self) -> list[SourceRecord]:
        mode=str(self.config.get('mode') or 'public').casefold()
        endpoint=(self.config.get('collection_endpoint') or '').strip()
        instance=self.config.get('instance','https://neodb.social').rstrip('/')+'/'
        username=self.config.get('username')

        # Authenticated mode has a long-standing NeoDB shelf API convention. Keep the
        # path configurable because NeoDB is federated and instance versions differ.
        if mode == 'authenticated' and not endpoint:
            if not self.token:
                raise CapabilityUnavailable('NeoDB authenticated mode requires NEODB_ACCESS_TOKEN')
            endpoint=(self.config.get('authenticated_shelf_endpoint') or '/api/me/shelf/{shelf}').strip()
            shelf_types=self.config.get('shelf_types') or ['wishlist','progress','complete','dropped']
            out=[]
            for shelf in shelf_types:
                page=1
                while True:
                    url=urljoin(instance, endpoint.lstrip('/')).format(shelf=shelf,username=username or '')
                    try:
                        data=self._get_json(url, headers=self._headers(), params={'page':page})
                    except AdapterError:
                        # Some older instances may not expose every shelf type (notably dropped).
                        # Do not discard already fetched shelves because one optional shelf is absent.
                        if shelf == 'dropped':
                            break
                        raise
                    items=self._unwrap(data)
                    for row in items:
                        if isinstance(row,dict) and not row.get('shelf_type'):
                            row=dict(row); row['shelf_type']=shelf
                        out.append(self.normalize_item(row,instance.rstrip('/'),self.config.get('user_rating_scale',10)))
                    pages=int(data.get('pages') or 1) if isinstance(data,dict) else 1
                    if page >= pages or not items:
                        break
                    page += 1
            return out

        # Public mode deliberately requires a documented instance endpoint rather than
        # silently scraping HTML. A custom endpoint may also be used in authenticated mode.
        if not endpoint:
            raise CapabilityUnavailable(
                'NeoDB public collection endpoint is not pinned by PGL. Configure sources.neodb.collection_endpoint '
                'from your instance Developer/OpenAPI documentation, or switch to authenticated mode; PGL intentionally does not HTML-scrape.')
        if '{username}' in endpoint and not username:
            raise AdapterError('NeoDB username is required by the configured collection_endpoint')
        url=urljoin(instance, endpoint.lstrip('/')).format(username=username or '')
        data=self._get_json(url, headers=self._headers())
        items=self._unwrap(data)
        return [self.normalize_item(x,instance.rstrip('/'),self.config.get('user_rating_scale',10)) for x in items]

    @staticmethod
    def _unwrap(data):
        if isinstance(data,list): return data
        if isinstance(data,dict):
            for key in ('items','data','results','collections'):
                if isinstance(data.get(key),list): return data[key]
        raise AdapterError('Unexpected NeoDB collection response; configure a compatible documented endpoint')

    @staticmethod
    def _progress(value: Any) -> Progress | None:
        if value is None:
            return None
        if isinstance(value,dict):
            current=value.get('current',value.get('value'))
            total=value.get('total')
            unit=value.get('unit')
            percent=value.get('percent')
            if percent is None and current is not None and total:
                try: percent=round(float(current)/float(total)*100,2)
                except (TypeError,ValueError,ZeroDivisionError): percent=None
            return Progress(current=current,total=total,unit=unit,percent=percent,source='neodb')
        try:
            percent=float(value)
            return Progress(current=percent,total=100,unit='percent',percent=percent,source='neodb')
        except (TypeError,ValueError):
            return None

    @staticmethod
    def normalize_item(entry: dict[str,Any], instance: str='https://neodb.social', user_rating_scale: float=10) -> SourceRecord:
        item=entry.get('item') if isinstance(entry.get('item'),dict) else entry
        item=item or {}
        # `category` is the stable high-level catalog kind; `type` may be TVSeason, Edition, etc.
        typ=str(item.get('category') or entry.get('category') or item.get('type') or entry.get('type') or '').casefold()
        typ=typ.rsplit('/',1)[-1]
        hint=TYPE_HINTS.get(typ, typ if typ in TYPE_HINTS.values() else None)
        nid=str(item.get('uuid') or item.get('id') or entry.get('item_id') or item.get('url') or '')
        title=item.get('display_title') or item.get('title') or item.get('name') or f'NeoDB {nid}'
        alt=[]
        for key in ('original_title','title_original','orig_title'):
            if item.get(key) and item[key] != title: alt.append(str(item[key]))
        for v in item.get('other_titles') or item.get('other_title') or item.get('alternative_titles') or []:
            if v and str(v) not in alt: alt.append(str(v))
        date=item.get('year') or item.get('pub_year') or item.get('release_date') or item.get('date')
        year=None
        if isinstance(date,int): year=date
        elif date and str(date)[:4].isdigit(): year=int(str(date)[:4])
        cover=item.get('cover_image_url') or item.get('cover') or item.get('image')
        if isinstance(cover,dict): cover=cover.get('url') or cover.get('large')
        # NeoDB item.rating is the community aggregate, not the current user's rating.
        # Personal shelf responses expose rating_grade; generic fixture/custom endpoints may
        # supply user_rating or rating at the collection-entry level.
        rvalue=entry.get('rating_grade')
        if rvalue in (None,0,''):
            rvalue=entry.get('user_rating')
        if rvalue in (None,0,'') and 'rating' in entry:
            rvalue=entry.get('rating')
        if rvalue not in (None,0,''):
            try:
                numeric_rating=float(rvalue)
            except (TypeError,ValueError):
                numeric_rating=None
        else:
            numeric_rating=None
        if entry.get('rating_grade') not in (None,0,''):
            rscale=entry.get('rating_scale') or user_rating_scale
        else:
            rscale=entry.get('rating_scale') or (5 if numeric_rating is not None and numeric_rating<=5 else 10)
        rating=Rating.from_value(numeric_rating,rscale,'neodb') if numeric_rating is not None else None
        status=map_neodb(entry.get('status') or entry.get('collection_status') or entry.get('shelf_type') or entry.get('shelf'))
        tags=[]
        for t in (entry.get('tags') or item.get('tags') or []):
            if isinstance(t,dict): t=t.get('name')
            if t: tags.append(str(t))
        for g in (item.get('genre') or item.get('genres') or []):
            if isinstance(g,dict): g=g.get('name')
            if g and str(g) not in tags: tags.append(str(g))
        if hint=='performance' and 'performance' not in tags: tags.append('performance')
        ids={'neodb_item_id':nid}
        for key in ('isbn','isbn13','isbn10'):
            val=item.get(key)
            if val: ids[key]=str(val).replace('-','')
        ext=item.get('external_resources') or item.get('external_links') or []
        links={}
        url=item.get('url') or entry.get('url')
        if url: links['neodb']=urljoin(instance.rstrip('/')+'/',str(url).lstrip('/'))
        if isinstance(ext,dict): ext=[{'site':k,'url':v} for k,v in ext.items()]
        for e in ext if isinstance(ext,list) else []:
            if not isinstance(e,dict): continue
            site=str(e.get('site') or e.get('name') or '').casefold(); eu=e.get('url')
            if eu and ('bangumi' in site or 'bgm.tv/subject/' in str(eu)):
                links['bangumi']=str(eu)
                try: ids['bangumi_subject_id']=int(str(eu).rstrip('/').split('/')[-1])
                except Exception: pass
        return SourceRecord(source='neodb',source_id=nid,category_hint=hint,title=title,title_original=alt[0] if alt else None,
            alternate_titles=alt,year=year,release_date=str(date) if date else None,cover_url=cover,summary=item.get('brief') or item.get('description') or item.get('summary'),
            status=status,rating=rating,progress=NeoDBAdapter._progress(entry.get('progress')),tags=list(dict.fromkeys(tags)),identifiers=ids,links=links,
            updated_at=entry.get('updated_time') or entry.get('updated_at') or entry.get('created_time'),raw_type=typ,extra={'raw_collection_status':entry.get('status') or entry.get('collection_status') or entry.get('shelf_type'),'community_rating':item.get('rating'),'community_rating_count':item.get('rating_count'),'comment_text':entry.get('comment_text'),'api_url':item.get('api_url')})
