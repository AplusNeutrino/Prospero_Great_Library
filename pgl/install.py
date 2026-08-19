from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Iterable
import yaml

from . import __version__

MANIFEST_NAME = ".pgl-install.json"


class InstallError(ValueError):
    """Raised when the target is not a safe installable Jekyll site."""



@dataclass
class InstallAction:
    path: str
    action: str
    detail: str = ""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _resource_bytes(relative: str) -> bytes:
    node = resources.files("pgl").joinpath("resources", "chirpy", *relative.split("/"))
    return node.read_bytes()


def _site_config(site_root: Path) -> dict:
    try:
        data = yaml.safe_load((site_root / "_config.yml").read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _library_title(site_root: Path) -> str:
    config = _site_config(site_root)
    pgl = config.get("prospero_great_library") or config.get("personal_library") or {}
    ui = pgl.get("ui") or {} if isinstance(pgl, dict) else {}
    explicit = ui.get("title") if isinstance(ui, dict) else None
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    site_title = str(config.get("title") or "").strip() or "Personal"
    lang = str(config.get("lang") or (pgl.get("locale") if isinstance(pgl, dict) else "") or "en")
    return f"{site_title}大图书馆" if lang.lower().startswith("zh") else f"{site_title} Great Library"


def _render_resource(relative: str, site_root: Path) -> bytes:
    data = _resource_bytes(relative)
    if relative != "library-page.md":
        return data
    text = data.decode("utf-8")
    # JSON string quoting is valid YAML and safely handles colons/quotes/non-ASCII.
    rendered_title = json.dumps(_library_title(site_root), ensure_ascii=False)
    return text.replace("__PGL_LIBRARY_TITLE__", rendered_title).encode("utf-8")


def _templates() -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    base = resources.files("pgl").joinpath("resources", "chirpy")
    for child in base.joinpath("includes").iterdir():
        if child.name.endswith(".html"):
            result.append((f"includes/{child.name}", f"_includes/pgl/{child.name}"))
    for child in base.joinpath("assets").iterdir():
        if child.is_file():
            result.append((f"assets/{child.name}", f"assets/pgl/{child.name}"))
    for child in base.joinpath("locales").iterdir():
        if child.name.endswith(".yml"):
            result.append((f"locales/{child.name}", f"_data/pgl_locales/{child.name}"))
    result.extend(
        [
            ("prospero_great_library.rb", "_plugins/prospero_great_library.rb"),
            ("library-page.md", "_tabs/library.md"),
        ]
    )
    return sorted(result, key=lambda x: x[1])


def _load_manifest(site_root: Path) -> dict:
    path = site_root / MANIFEST_NAME
    if not path.exists():
        return {"schema_version": 1, "managed": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "managed": {}}
    if not isinstance(data, dict):
        return {"schema_version": 1, "managed": {}}
    data.setdefault("managed", {})
    return data


def _backup_path(site_root: Path, dest_rel: str, stamp: str) -> Path:
    return site_root / ".pgl-backups" / stamp / dest_rel


def install_chirpy(
    site_root: str | Path,
    *,
    dry_run: bool = False,
    force: bool = False,
    backup: bool = True,
) -> list[InstallAction]:
    """Install or safely upgrade the thin Chirpy adapter.

    Existing files are only updated automatically when the prior PGL install
    manifest proves that the local file has not been modified since PGL wrote
    it. A conflicting local file is preserved unless ``force`` is requested.
    Forced replacement is backed up by default.
    """

    site = Path(site_root).resolve()
    if not site.exists() or not site.is_dir():
        raise InstallError(f"site root does not exist or is not a directory: {site}")
    if not (site / "_config.yml").is_file():
        raise InstallError(f"refusing to install: no _config.yml found under {site}")
    previous = _load_manifest(site)
    previous_managed = previous.get("managed", {}) if isinstance(previous.get("managed"), dict) else {}
    new_managed: dict[str, dict[str, str]] = {}
    actions: list[InstallAction] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for resource_rel, dest_rel in _templates():
        data = _render_resource(resource_rel, site)
        desired_hash = _sha256_bytes(data)
        dest = site / dest_rel
        old_entry = previous_managed.get(dest_rel) or {}
        old_hash = old_entry.get("sha256")

        if not dest.exists():
            action = "create"
        else:
            current_hash = _sha256_file(dest)
            if current_hash == desired_hash:
                action = "unchanged"
            elif old_hash and current_hash == old_hash:
                action = "update"
            elif force:
                action = "replace"
            else:
                actions.append(InstallAction(dest_rel, "conflict", "local file preserved; use --force to replace"))
                # Preserve prior ownership hash, if any, but do not claim the
                # conflicting local file matches this release.
                if old_hash:
                    new_managed[dest_rel] = {"sha256": old_hash}
                continue

        if action == "replace" and backup and dest.exists():
            backup_path = _backup_path(site, dest_rel, stamp)
            actions.append(InstallAction(dest_rel, "backup", str(backup_path.relative_to(site))))
            if not dry_run:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest, backup_path)

        actions.append(InstallAction(dest_rel, action))
        if not dry_run and action in {"create", "update", "replace"}:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        new_managed[dest_rel] = {"sha256": desired_hash}

    mapping_rel = "_data/prospero_great_library/mappings.yml"
    mapping = site / mapping_rel
    if not mapping.exists():
        actions.append(InstallAction(mapping_rel, "create", "user-owned mapping file"))
        if not dry_run:
            mapping.parent.mkdir(parents=True, exist_ok=True)
            mapping.write_text("entities: []\nclassifications: []\narticles: []\nprivacy: []\n", encoding="utf-8")
    else:
        actions.append(InstallAction(mapping_rel, "preserve", "user-owned mapping file"))

    manifest = {
        "schema_version": 1,
        "pgl_version": __version__,
        "adapter": "chirpy",
        "installed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "managed": new_managed,
    }
    actions.append(InstallAction(MANIFEST_NAME, "write" if not dry_run else "would_write"))
    if not dry_run:
        (site / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return actions


def format_actions(actions: Iterable[InstallAction]) -> str:
    lines = []
    for item in actions:
        suffix = f" — {item.detail}" if item.detail else ""
        lines.append(f"{item.action.upper():10} {item.path}{suffix}")
    return "\n".join(lines)
