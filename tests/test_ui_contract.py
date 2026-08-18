from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_chirpy_ui_contains_locked_v1_controls_and_lazy_fallback():
    filters = (ROOT / 'jekyll/_includes/pgl/filters.html').read_text(encoding='utf-8')
    library = (ROOT / 'jekyll/_includes/pgl/library.html').read_text(encoding='utf-8')
    js = (ROOT / 'jekyll/assets/pgl/pgl.js').read_text(encoding='utf-8')
    assert 'pgl-year' in filters
    assert 'pgl-load-more' in library
    assert 'pgl-current' in library
    assert 'data-history-manifest' in library
    assert 'limit: 60' in library
    assert 'initialLimit' in js
    assert 'setTimeout(() => apply(true), 140)' in js
    assert 'grid.replaceChildren' in js


def test_drawer_links_are_protocol_filtered_and_dom_built():
    js = (ROOT / 'jekyll/assets/pgl/pgl.js').read_text(encoding='utf-8')
    assert "['http:', 'https:'].includes(url.protocol)" in js
    assert 'dialogContent.replaceChildren()' in js
    assert 'appendSafeLink' in js
    assert 'innerHTML' not in js
