from __future__ import annotations
import json
from pathlib import Path

from pgl.install import InstallError, install_chirpy


def _jekyll_site(tmp_path: Path) -> Path:
    (tmp_path / "_config.yml").write_text("theme: jekyll-theme-chirpy\n", encoding="utf-8")
    return tmp_path


def test_chirpy_installer_is_idempotent_and_manifested(tmp_path: Path):
    tmp_path = _jekyll_site(tmp_path)
    actions = install_chirpy(tmp_path)
    assert not [x for x in actions if x.action == 'conflict']
    assert (tmp_path / '_tabs/library.md').exists()
    assert (tmp_path / '_includes/pgl/library.html').exists()
    manifest = json.loads((tmp_path / '.pgl-install.json').read_text(encoding='utf-8'))
    assert manifest['adapter'] == 'chirpy'
    assert '_tabs/library.md' in manifest['managed']

    second = install_chirpy(tmp_path)
    assert not [x for x in second if x.action == 'conflict']
    assert [x for x in second if x.action == 'unchanged']


def test_chirpy_installer_preserves_local_conflict_until_force(tmp_path: Path):
    tmp_path = _jekyll_site(tmp_path)
    install_chirpy(tmp_path)
    target = tmp_path / '_tabs/library.md'
    original = target.read_text(encoding='utf-8')
    target.write_text('LOCAL CUSTOMIZATION\n', encoding='utf-8')

    actions = install_chirpy(tmp_path)
    assert any(x.action == 'conflict' and x.path == '_tabs/library.md' for x in actions)
    assert target.read_text(encoding='utf-8') == 'LOCAL CUSTOMIZATION\n'

    forced = install_chirpy(tmp_path, force=True)
    assert any(x.action == 'backup' and x.path == '_tabs/library.md' for x in forced)
    assert target.read_text(encoding='utf-8') == original
    backups = list((tmp_path / '.pgl-backups').glob('*/_tabs/library.md'))
    assert len(backups) == 1
    assert backups[0].read_text(encoding='utf-8') == 'LOCAL CUSTOMIZATION\n'


def test_chirpy_installer_never_overwrites_user_mapping(tmp_path: Path):
    tmp_path = _jekyll_site(tmp_path)
    mapping = tmp_path / '_data/prospero_great_library/mappings.yml'
    mapping.parent.mkdir(parents=True)
    mapping.write_text('entities:\n  - custom: true\n', encoding='utf-8')
    install_chirpy(tmp_path, force=True)
    assert 'custom: true' in mapping.read_text(encoding='utf-8')


def test_chirpy_installer_refuses_non_jekyll_directory(tmp_path: Path):
    import pytest
    with pytest.raises(InstallError, match="_config.yml"):
        install_chirpy(tmp_path)

def test_demo_site_is_current_with_packaged_chirpy_resources():
    from pathlib import Path
    from pgl.install import install_chirpy

    root = Path(__file__).resolve().parents[1]
    actions = install_chirpy(root / "demo" / "site", dry_run=True)
    conflicts = [item for item in actions if item.action == "conflict"]
    assert conflicts == []



def test_chirpy_installer_renders_site_aware_sidebar_title(tmp_path: Path):
    (tmp_path / '_config.yml').write_text('title: 中间层\nlang: zh-CN\n', encoding='utf-8')
    install_chirpy(tmp_path)
    tab = (tmp_path / '_tabs/library.md').read_text(encoding='utf-8')
    assert 'title: "中间层大图书馆"' in tab


def test_chirpy_installer_sidebar_title_honors_ui_override(tmp_path: Path):
    (tmp_path / '_config.yml').write_text(
        'title: Example\nlang: en\nprospero_great_library:\n  ui:\n    title: My Archive\n',
        encoding='utf-8',
    )
    install_chirpy(tmp_path)
    tab = (tmp_path / '_tabs/library.md').read_text(encoding='utf-8')
    assert 'title: "My Archive"' in tab
