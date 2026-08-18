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
