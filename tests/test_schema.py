import pytest

from pgl.schema import SchemaError, validate_library


def _item(cid='book:a', category='book', status='wishlist'):
    return {'id': cid, 'category': category, 'status': status, 'tags': [], 'privacy': {}}


def test_schema_accepts_valid_public_library():
    validate_library({'schema_version': 1, 'items': [_item()]})


def test_schema_rejects_duplicate_id_invalid_category_and_hidden_leak():
    with pytest.raises(SchemaError, match='duplicate canonical id'):
        validate_library({'schema_version': 1, 'items': [_item(), _item()]})
    with pytest.raises(SchemaError, match='invalid category'):
        validate_library({'schema_version': 1, 'items': [_item(category='podcast')]})
    hidden = _item()
    hidden['privacy'] = {'hidden': True}
    with pytest.raises(SchemaError, match='hidden entity leaked'):
        validate_library({'schema_version': 1, 'items': [hidden]})


def test_schema_rejects_performance_anime():
    item = _item(category='anime')
    item['tags'] = ['performance']
    with pytest.raises(SchemaError, match='anime entity cannot be performance'):
        validate_library({'schema_version': 1, 'items': [item]})
