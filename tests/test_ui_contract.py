from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_alpha4_library_information_architecture_contract():
    library = read('jekyll/_includes/pgl/library.html')
    header = read('jekyll/_includes/pgl/header.html')
    toolbar = read('jekyll/_includes/pgl/view-toolbar.html')
    js = read('jekyll/assets/pgl/pgl.js')

    assert 'pgl-root-view' in library
    assert 'pgl-browser-view' in library
    assert 'pgl/category-ledger.html' in library
    assert 'pgl/rating-chart.html' in library
    assert 'pgl-load-more' not in library
    assert 'limit: 60' not in library
    assert 'pgl-search' in header
    assert 'pgl-year' in toolbar
    assert 'pgl-source' in toolbar
    assert "const PAGE_SIZE = Math.max(1, Number(root.dataset.pageSize || 24))" in js
    assert "window.addEventListener('popstate'" in js
    assert "history[method]" in js
    assert "localStorage.setItem('pgl.layout'" in js


def test_default_status_contract_and_wishlist_isolation_are_explicit():
    js = read('jekyll/assets/pgl/pgl.js')
    zh = read('jekyll/locales/zh-CN.yml')
    assert "new Set(['in_progress', 'completed'])" in js
    assert "item.status === 'wishlist'" in js
    assert "a.status === 'in_progress' ? 0 : 1" in js
    assert 'wishlist: 计划品鉴' in zh
    assert 'statuses: {wishlist: 计划品鉴' in zh
    assert '想看/想读/想玩' not in zh


def test_no_all_collection_primary_view_and_global_search_exists():
    library = read('jekyll/_includes/pgl/library.html')
    js = read('jekyll/assets/pgl/pgl.js')
    assert 'All Collection' not in library
    assert '全部藏品' not in library
    assert "if (next.q) { next.view = 'search'" in js
    assert "items.filter((item) => itemSearchText(item).includes(q))" in js
    assert 'pgl-search-group-heading' in js


def test_rating_curve_is_svg_monotone_and_steam_ranking_ui_removed():
    rating = read('jekyll/_includes/pgl/rating-chart.html')
    stats = read('jekyll/_includes/pgl/stats.html')
    js = read('jekyll/assets/pgl/pgl.js')
    assert '<svg id="pgl-rating-chart"' in rating
    assert 'data-rating-scope="all"' in rating
    assert 'function monotonePath(points)' in js
    assert 'pgl-rating-a11y' not in rating
    assert 'chartA11y' not in js
    assert 'pgl-chart-curve' in js
    assert 'pgl-ranking' not in stats
    assert 'steam_top_games' not in stats


def test_current_activity_is_vertical_unlimited_and_accepts_steam_recent():
    current = read('jekyll/_includes/pgl/current.html')
    css = read('jekyll/assets/pgl/pgl.css')
    assert 'limit:' not in current
    assert "activity.reason == 'steam_recent'" in current
    assert 'pgl-current-row' in current
    assert '.pgl-current-list { display:flex; flex-direction:column;' in css


def test_compact_grid_and_list_contract():
    css = read('jekyll/assets/pgl/pgl.css')
    assert 'repeat(auto-fill,minmax(142px,1fr))' in css
    assert 'grid-template-columns:62px minmax(0,1fr)' in css
    assert '@media (max-width: 720px)' in css
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in css


def test_drawer_links_are_protocol_filtered_and_dom_built():
    js = read('jekyll/assets/pgl/pgl.js')
    assert "['http:', 'https:'].includes(url.protocol)" in js
    assert 'dialogContent.replaceChildren()' in js
    assert 'appendSafeLink' in js
    assert 'innerHTML' not in js


def test_site_aware_title_hook_and_chirpy_heading_suppression():
    plugin = read('jekyll/_plugins/prospero_great_library.rb')
    page = read('adapters/chirpy/library-page.md')
    adapter_css = read('jekyll/assets/pgl/pgl-chirpy.css')
    assert "Jekyll::Hooks.register :pages, :pre_render" in plugin
    assert "format(template, site: site_title)" in plugin
    assert 'pgl_library: true' in page
    assert 'title: __PGL_LIBRARY_TITLE__' in page
    assert 'article:has(#prospero-great-library) > .dynamic-title' in adapter_css
