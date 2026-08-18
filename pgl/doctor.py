from __future__ import annotations
import re
from pathlib import Path
from .config import secret

SUPPORTED_CHIRPY_LINES = ("7.6", "7.5")


def _detect_gem_version(root: Path, gem: str) -> str | None:
    lock = root / "Gemfile.lock"
    if lock.exists():
        text = lock.read_text(encoding="utf-8", errors="replace")
        match = re.search(rf"^\s{{4}}{re.escape(gem)} \(([^)]+)\)", text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    gemfile = root / "Gemfile"
    if gemfile.exists():
        text = gemfile.read_text(encoding="utf-8", errors="replace")
        match = re.search(rf"gem\s+[\"']{re.escape(gem)}[\"']\s*,\s*[\"'][~><=\s]*([0-9]+\.[0-9]+(?:\.[0-9]+)?)[\"']", text)
        if match:
            return match.group(1)
    return None


def _is_chirpy_site(root: Path) -> bool:
    cfg = root / "_config.yml"
    if cfg.exists() and "jekyll-theme-chirpy" in cfg.read_text(encoding="utf-8", errors="replace"):
        return True
    gemfile = root / "Gemfile"
    return gemfile.exists() and "jekyll-theme-chirpy" in gemfile.read_text(encoding="utf-8", errors="replace")


def run_doctor(site_root, config):
    root = Path(site_root)
    checks = []
    checks.append({"check": "site_root", "ok": root.exists(), "detail": str(root.resolve())})
    for name in ("bangumi", "neodb", "steam"):
        c = config.get("sources", {}).get(name, {})
        if not c.get("enabled"):
            checks.append({"check": name, "ok": True, "detail": "disabled"})
            continue
        missing = []
        if name == "bangumi" and not c.get("username"):
            missing.append("username")
        if name == "steam":
            if not c.get("steam_id"):
                missing.append("steam_id")
            if not secret("STEAM_API_KEY"):
                missing.append("STEAM_API_KEY")
        if name == "neodb":
            mode = str(c.get("mode") or "public").casefold()
            if mode == "authenticated":
                if not secret("NEODB_ACCESS_TOKEN"):
                    missing.append("NEODB_ACCESS_TOKEN")
                if not (c.get("authenticated_shelf_endpoint") or c.get("collection_endpoint")):
                    missing.append("authenticated_shelf_endpoint")
            else:
                if not c.get("username"):
                    missing.append("username")
                if not c.get("collection_endpoint"):
                    missing.append("collection_endpoint (documented public endpoint for the selected instance)")
        checks.append({"check": name, "ok": not missing, "detail": "ok" if not missing else "missing: " + ", ".join(missing)})
        if name == "bangumi" and secret("BANGUMI_ACCESS_TOKEN"):
            privacy_enabled = bool(c.get("hide_private_collections", True))
            checks.append({
                "check": "bangumi_privacy_filter",
                "ok": privacy_enabled,
                "detail": "enabled" if privacy_enabled else "authenticated sync may expose private collections; set hide_private_collections: true",
            })

    data = root / "_data" / "prospero_great_library"
    checks.append({"check": "mappings", "ok": True, "detail": str(data / "mappings.yml")})
    page_exists = (root / "library.md").exists() or (root / "_tabs" / "library.md").exists()
    checks.append({"check": "library_page", "ok": page_exists, "detail": "installed" if page_exists else "optional until Chirpy installer runs"})

    if _is_chirpy_site(root):
        version = _detect_gem_version(root, "jekyll-theme-chirpy")
        if version:
            supported = any(version == line or version.startswith(line + ".") for line in SUPPORTED_CHIRPY_LINES)
            detail = f"detected {version}; supported lines: {', '.join(SUPPORTED_CHIRPY_LINES)}"
            checks.append({"check": "chirpy_version", "ok": supported, "detail": detail})
        else:
            checks.append({"check": "chirpy_version", "ok": True, "detail": "Chirpy detected; exact version unresolved (run bundle install to create Gemfile.lock)"})
        required = [
            root / "_includes" / "pgl" / "library.html",
            root / "assets" / "pgl" / "pgl.css",
            root / "assets" / "pgl" / "pgl.js",
            root / "_plugins" / "prospero_great_library.rb",
        ]
        missing = [str(p.relative_to(root)) for p in required if not p.exists()]
        checks.append({"check": "chirpy_adapter", "ok": not missing, "detail": "installed" if not missing else "missing: " + ", ".join(missing)})
    else:
        checks.append({"check": "chirpy_version", "ok": True, "detail": "not detected; generic Jekyll mode"})

    return checks
