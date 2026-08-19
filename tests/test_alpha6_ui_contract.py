from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_search_is_compact_and_host_theme_independent():
    header=(ROOT/'jekyll/_includes/pgl/header.html').read_text(encoding='utf-8')
    css=(ROOT/'jekyll/assets/pgl/pgl-polish.css').read_text(encoding='utf-8')
    assert 'pgl-sr-only' in header and 'visually-hidden' not in header
    assert '.pgl-sr-only' in css
    assert 'width:11.5rem' in css
    assert 'border-radius:9px' in css

def test_stats_render_unknown_when_steam_privacy_probe_is_unavailable():
    html=(ROOT/'jekyll/_includes/pgl/stats.html').read_text(encoding='utf-8')
    assert "steam_status == 'ok' or steam_status == 'stale'" in html
    assert '{{ l.steam_unavailable }}' in html
    assert '—' in html

def test_rating_polish_has_histogram_area_curve_and_summary():
    js=(ROOT/'jekyll/assets/pgl/pgl-rating-polish.js').read_text(encoding='utf-8')
    html=(ROOT/'jekyll/_includes/pgl/rating-chart.html').read_text(encoding='utf-8')
    css=(ROOT/'jekyll/assets/pgl/pgl-polish.css').read_text(encoding='utf-8')
    assert 'pgl-chart-bar' in js and 'pgl-chart-area' in js and 'pgl-chart-point' in js
    assert 'pgl-rating-summary' in html
    assert 'border-bottom-color:var(--pgl-accent)' in css


def test_new_polish_assets_are_loaded_and_mirrored():
    library=(ROOT/'jekyll/_includes/pgl/library.html').read_text(encoding='utf-8')
    assert 'pgl-polish.css' in library
    assert 'pgl-rating-polish.js' in library
    for rel in ['pgl-polish.css','pgl-rating-polish.js']:
        assert (ROOT/'jekyll/assets/pgl'/rel).read_bytes()==(ROOT/'pgl/resources/chirpy/assets'/rel).read_bytes()
        assert (ROOT/'jekyll/assets/pgl'/rel).read_bytes()==(ROOT/'demo/site/assets/pgl'/rel).read_bytes()


def test_version_markers_are_alpha6():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='0.1.0-alpha.6'
    assert '0.1.0a6' in (ROOT/'pyproject.toml').read_text(encoding='utf-8')
    assert '0.1.0-alpha.6' in (ROOT/'pgl/__init__.py').read_text(encoding='utf-8')
    assert "VERSION='0.1.0-alpha.6'" in (ROOT/'pgl/cli.py').read_text(encoding='utf-8')
