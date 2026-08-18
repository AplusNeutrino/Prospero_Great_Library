from pgl.privacy.filters import apply_privacy

def test_hidden_never_public():
    items=[{'id':'book:a','category':'book','links':{},'sources':{},'privacy':{}},{'id':'book:b','category':'book','links':{},'sources':{},'privacy':{}}]
    cfg={'privacy':{'hide_items':['book:a'],'stats_only_items':[],'hide_sources':[]}}
    public,stats=apply_privacy(items,cfg,{'privacy':[]})
    assert [x['id'] for x in public]==['book:b']
    assert [x['id'] for x in stats]==['book:b']

def test_hidden_source_removes_source_provenance():
    items=[{'id':'book:a','category':'book','links':{'neodb':'https://x'},'sources':{'neodb':{'present':True}},'privacy':{},'rating':{'value':4,'scale':5,'normalized_10':8,'source':'neodb'},'_provenance':{'rating':'neodb'}}]
    cfg={'privacy':{'hide_items':[],'stats_only_items':[],'hide_sources':['neodb']}}
    public,_=apply_privacy(items,cfg,{'privacy':[]})
    assert 'neodb' not in public[0]['sources']
    assert public[0]['rating']['source'] is None
    assert public[0]['_provenance']['rating'] is None


def test_per_item_source_visibility_override():
    items=[{'id':'game:a','category':'game','links':{'bangumi':'https://bgm.tv/subject/1','steam':'https://store.steampowered.com/app/1/'},'sources':{'bangumi':{'present':True},'steam':{'present':True}},'privacy':{},'rating':None}]
    cfg={'privacy':{'hide_items':[],'stats_only_items':[],'hide_sources':[]}}
    mappings={'privacy':[{'entity':'game:a','hide_sources':['steam']}]}
    public,_=apply_privacy(items,cfg,mappings)
    assert 'steam' not in public[0]['sources'] and 'steam' not in public[0]['links']
    assert public[0]['links']['primary']=='https://bgm.tv/subject/1'
