from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'pgl/resources/chirpy'


def test_packaged_chirpy_resources_match_release_tree():
    pairs = []
    for source in (ROOT / 'jekyll/_includes/pgl').glob('*.html'):
        pairs.append((source, RES / 'includes' / source.name))
    for source in (ROOT / 'jekyll/assets/pgl').glob('*'):
        if source.is_file():
            pairs.append((source, RES / 'assets' / source.name))
    for source in (ROOT / 'jekyll/locales').glob('*.yml'):
        pairs.append((source, RES / 'locales' / source.name))
    pairs.extend([
        (ROOT / 'jekyll/_plugins/prospero_great_library.rb', RES / 'prospero_great_library.rb'),
        (ROOT / 'adapters/chirpy/library-page.md', RES / 'library-page.md'),
    ])
    assert pairs
    for source, mirror in pairs:
        assert mirror.exists(), mirror
        assert source.read_bytes() == mirror.read_bytes(), source
