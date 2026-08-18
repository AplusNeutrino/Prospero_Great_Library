from pgl.models import SourceRecord
from pgl.normalize.categories import classify_record,choose_group_category

def test_comic_over_book():
    r=SourceRecord(source='bangumi',source_id='1',category_hint='book',title='X',tags=['manga'])
    assert classify_record(r)[0]=='comic'

def test_anime_group_over_movie():
    a=SourceRecord(source='bangumi',source_id='1',category_hint='anime',title='X')
    b=SourceRecord(source='neodb',source_id='2',category_hint='movie',title='X')
    assert choose_group_category([a,b])[0]=='anime'

def test_performance_is_movie_tag():
    r=SourceRecord(source='neodb',source_id='2',category_hint='performance',title='Stage')
    cat,tags=choose_group_category([r])
    assert cat=='movie' and 'performance' in tags

def test_live_action_tv_from_real_platform_is_drama():
    r=SourceRecord(source='bangumi',source_id='6',category_hint='movie',title='Live Action',tags=['TV'],raw_type=6,extra={'platform':'TV'})
    assert classify_record(r)[0]=='drama'

def test_neodb_animated_movie_is_anime():
    r=SourceRecord(source='neodb',source_id='m1',category_hint='movie',title='Animated Feature',tags=['Animation'])
    assert classify_record(r)[0]=='anime'

def test_keyword_in_book_title_does_not_steal_category():
    r=SourceRecord(source='neodb',source_id='b1',category_hint='book',title='The Anime Machine',tags=[])
    assert classify_record(r)[0]=='book'
