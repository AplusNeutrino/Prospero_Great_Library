from pathlib import Path
from pgl.associations import associate
from pgl.config import DEFAULTS

def test_exact_url_association(tmp_path):
    p=tmp_path/'_posts'; p.mkdir(); (p/'2026-01-01-x.md').write_text('---\ntitle: Test\n---\nhttps://bgm.tv/subject/3\n',encoding='utf-8')
    items=[{'id':'game:x','title':'FINAL FANTASY','title_original':None,'alternate_titles':[],'identifiers':{'bangumi_subject_id':3},'links':{'bangumi':'https://bgm.tv/subject/3'}}]
    out=associate(tmp_path,items,DEFAULTS,{'articles':[]})
    assert out['by_entity']['game:x'][0]['method']=='bangumi_url'

def test_fuzzy_title_association(tmp_path):
    p=tmp_path/'_posts'; p.mkdir(); (p/'2026-01-01-x.md').write_text('---\ntitle: "游戏记录：Final Fantasy 1"\ntags: [Final Fantasy I]\n---\ntext\n',encoding='utf-8')
    items=[{'id':'game:x','title':'FINAL FANTASY I','title_original':None,'alternate_titles':['Final Fantasy 1'],'identifiers':{},'links':{}}]
    out=associate(tmp_path,items,DEFAULTS,{'articles':[]})
    assert out['by_entity']['game:x'][0]['confidence']>=.95
