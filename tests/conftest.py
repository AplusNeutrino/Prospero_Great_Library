from pathlib import Path
import json,pytest
from pgl.models import SourceRecord

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def fixture_records():
    out=[]
    for name in ('bangumi','neodb','steam'):
        doc=json.loads((ROOT/'demo'/'fixtures'/f'{name}.json').read_text(encoding='utf-8'))
        out.extend(SourceRecord.from_dict(x) for x in doc['records'])
    return out
