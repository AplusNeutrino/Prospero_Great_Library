from pathlib import Path

from pgl.config import DEFAULTS
from pgl.doctor import run_doctor


def _version_check(tmp_path: Path, requirement: str):
    (tmp_path / '_config.yml').write_text('theme: jekyll-theme-chirpy\n', encoding='utf-8')
    (tmp_path / 'Gemfile').write_text(f'gem "jekyll-theme-chirpy", "~> {requirement}"\n', encoding='utf-8')
    checks = run_doctor(tmp_path, DEFAULTS)
    return next(row for row in checks if row['check'] == 'chirpy_version')


def test_doctor_accepts_current_supported_chirpy_lines(tmp_path: Path):
    assert _version_check(tmp_path, '7.6')['ok'] is True
    assert _version_check(tmp_path, '7.5')['ok'] is True


def test_doctor_warns_for_older_chirpy_line(tmp_path: Path):
    check = _version_check(tmp_path, '7.4')
    assert check['ok'] is False
    assert 'supported lines' in check['detail']


def test_doctor_requires_private_filter_for_authenticated_bangumi(tmp_path: Path, monkeypatch):
    from copy import deepcopy
    cfg=deepcopy(DEFAULTS)
    cfg['sources']['bangumi'].update({'enabled':True,'username':'demo','hide_private_collections':False})
    monkeypatch.setenv('BANGUMI_ACCESS_TOKEN','secret')
    checks=run_doctor(tmp_path,cfg)
    row=next(x for x in checks if x['check']=='bangumi_privacy_filter')
    assert row['ok'] is False
    cfg['sources']['bangumi']['hide_private_collections']=True
    checks=run_doctor(tmp_path,cfg)
    row=next(x for x in checks if x['check']=='bangumi_privacy_filter')
    assert row['ok'] is True


def test_doctor_reports_steam_privacy_filter(tmp_path, monkeypatch):
    from copy import deepcopy
    from pgl.config import DEFAULTS
    from pgl.doctor import run_doctor
    import pgl.doctor as doctor_module

    (tmp_path / '_config.yml').write_text('title: x\n', encoding='utf-8')
    cfg = deepcopy(DEFAULTS)
    cfg['sources']['steam'].update({'enabled': True, 'steam_id': '123'})
    monkeypatch.setattr(doctor_module, 'secret', lambda name: 'x' if name == 'STEAM_API_KEY' else None)
    checks = run_doctor(tmp_path, cfg)
    row = next(x for x in checks if x['check'] == 'steam_privacy_filter')
    assert row['ok'] is True
