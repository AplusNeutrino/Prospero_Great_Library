# Changelog

## 0.1.0-alpha.3 — 2026-08-18

### Added

- integrated the deployed Bangumi paged-collection response fix;
- integrated `hide_private_collections` from the deployed production branch and made private-collection interception enabled by default;
- added retroactive history sanitization for currently-private Bangumi collections;
- extended history sanitization to PGL `hidden`, `stats_only`, and hidden-source policies;
- added `pgl privacy-audit` with optional `--apply`;
- added a fail-closed privacy publication invariant;
- added `diagnostics/privacy.json`; detailed private-record counts/reasons are runtime-only by default and require `privacy.publish_diagnostics: true` to persist;
- added `pgl doctor` warning for authenticated Bangumi sync without private filtering;
- hardened the reference scheduled workflow to detect untracked generated files, rebase before push, and optionally dispatch a separate Pages workflow through `PGL_PAGES_WORKFLOW`.

### Security

- private upstream identifiers used to scrub legacy history remain ephemeral and are not persisted as a private-item index;
- known-private data is removed before snapshots/merge/stats/new history/public output;
- privacy migration also rewrites prior public history partitions so a later privacy change does not leave timeline residue;
- persisted privacy diagnostics are metadata-minimized by default;
- PGL documents that current-tree sanitization cannot erase sensitive data from already-published Git commits and never rewrites Git history automatically.

### Runtime evidence

- deployed blog sync verified the main Bangumi, authenticated NeoDB, and Steam collection paths;
- deployed Bangumi privacy filtering was exercised against real private collection entries.

## 0.1.0-alpha.2 — 2026-08-18

Phase-7 hardening release continuing the Alpha.1 implementation.

### Added
- Managed, manifest-backed `pgl install --adapter chirpy` installer/upgrader with conflict preservation and backups.
- Packaged Chirpy resources inside the Python wheel.
- Chirpy 7.6/7.5 compatibility detection and a four-cell Light/Dark GitHub CI matrix.
- Expanded 11-item architecture demo covering all locked V1 category/status/source cases.
- Composite GitHub Action smoke job and stronger Pages reference workflow.
- Explicit schema-invariant and source-failure last-good regression tests.
- Compatibility documentation.

### Changed
- Library front end now progressively creates cards client-side while retaining a 60-card no-JS fallback.
- Search is debounced and library view state is reflected in query parameters.
- Chirpy CSS now inherits current theme variables through a thin adapter.
- Reference GitHub Actions updated to current major versions used by current Chirpy Starter.

### Security / safety
- Drawer/card content is built with DOM APIs rather than `innerHTML`.
- Third-party and associated-article clickable URLs are restricted to HTTP(S).
- Installer refuses targets without an existing Jekyll `_config.yml`.
- `mappings.yml` remains user-owned across install/upgrade operations.

### Still unverified
- Live external account/API behavior.
- Actual Chirpy v7.6/v7.5 Light/Dark Jekyll builds until uploaded GitHub CI runs.

## 0.1.0-alpha.1 — 2026-08-18

First runnable implementation of the architecture contract: Python core/CLI, Bangumi/NeoDB/Steam adapters, canonical merge, history/statistics, article association, Jekyll/Chirpy integration, demo fixtures, privacy filters, and automated core tests.
