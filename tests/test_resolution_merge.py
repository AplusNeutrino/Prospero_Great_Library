from pgl.models import SourceRecord,Rating
from pgl.resolve.entities import resolve
from pgl.merge import merge_all
from pgl.config import DEFAULTS

def test_crosslink_merges_at_one():
    b=SourceRecord(source='bangumi',source_id='7',category_hint='anime',title='X',identifiers={'bangumi_subject_id':7})
    n=SourceRecord(source='neodb',source_id='n',category_hint='movie',title='Different title',identifiers={'bangumi_subject_id':7})
    rr=resolve([b,n],{'entities':[],'classifications':[]},.95,.8)
    assert len(rr.groups)==1

def test_bangumi_precedence_even_for_book():
    b=SourceRecord(source='bangumi',source_id='7',category_hint='book',title='Bangumi Title',year=2020,status='completed',rating=Rating.from_value(9,10,'bangumi'),identifiers={'isbn13':'9781234567890'},links={'bangumi':'https://bgm.tv/subject/7'})
    n=SourceRecord(source='neodb',source_id='n',category_hint='book',title='NeoDB Title',year=2020,status='in_progress',rating=Rating.from_value(4,5,'neodb'),identifiers={'isbn13':'9781234567890'},links={'neodb':'https://neo/book/n'})
    rr=resolve([b,n],{'entities':[],'classifications':[]},.95,.8)
    item=merge_all(rr.groups,DEFAULTS,{'entities':[]}, {'items':[]}, '2026-08-18T00:00:00Z')[0]
    assert item['title']=='Bangumi Title'
    assert item['status']=='completed'
    assert item['rating']['normalized_10']==9
    assert item['links']['primary']=='https://neo/book/n'

def test_ambiguous_fuzzy_does_not_merge():
    a=SourceRecord(source='bangumi',source_id='1',category_hint='game',title='Final Fantasy X')
    b=SourceRecord(source='steam',source_id='2',category_hint='game',title='Final Fantasy X-2')
    rr=resolve([a,b],{'entities':[],'classifications':[]},.95,.8)
    assert len(rr.groups)==2

def test_unchanged_entity_preserves_canonical_updated_at():
    b=SourceRecord(source='bangumi',source_id='7',category_hint='book',title='Same',status='completed',links={'bangumi':'https://bgm.tv/subject/7'})
    first=merge_all([[b]],DEFAULTS,{'entities':[]},{'items':[]},'2026-08-18T00:00:00Z')[0]
    second=merge_all([[b]],DEFAULTS,{'entities':[]},{'items':[first]},'2026-08-19T00:00:00Z')[0]
    assert second['timestamps']['canonical_updated_at']=='2026-08-18T00:00:00Z'
    assert second['timestamps']['last_seen_at']=='2026-08-19T00:00:00Z'
