# Changelog

## 0.1.0-alpha.5 — 2026-08-19

### Fixed

- render the installed Chirpy sidebar tab title from the target site's title (`[site.title]大图书馆` for zh locales, `[site.title] Great Library` otherwise), while preserving explicit `ui.title` overrides;
- change the Observable Rating Distribution to integer-only 1–10 observation bins and remove the hidden semicolon-separated rating dump from the page;
- populate Steam-only cover images from public Steam Community metadata, normalize legacy HTTP media links to HTTPS, and use the Steam app icon as a fallback;
- prevent private Steam games from entering PGL by probing anonymous public visibility first, restricting `GetOwnedGames` to that public AppID set, avoiding unfiltered `GetRecentlyPlayedGames` in privacy-safe mode, and failing closed if visibility cannot be verified;
- sort Current Activity by the canonical Library category order (Book → Comic → Movie → Drama → Anime → Game → Music), then state/recent activity within each category;
- restore Bangumi manga classification by consuming `SlimSubject.tags` metadata and explicit book-category evidence when available instead of relying on a nonexistent SlimSubject `platform` field.

### Privacy

- Steam records that disappear from the previously public snapshot are treated as privacy-impacted for history sanitization without persisting a private-AppID index;
- public sync diagnostics expose only that the Steam privacy filter is enabled, not private-game identifiers or counts.

### Validation

- regression coverage added for dynamic Chirpy tab titles, integer rating bins, Steam public-AppID filtering/covers/fail-closed behavior, Current category ordering, and Bangumi comic classification.

## 0.1.0-alpha.4 — 2026-08-18

### Delivery revision 2 fix

- synchronized Demo locale mirrors with the canonical alpha.4 Jekyll/package locales so `pgl install --adapter chirpy --site-root demo/site --dry-run` no longer reports false local-file conflicts;
- corrected Demo reset ownership for installer-managed locales and made Demo builds fail on installer conflicts;
- extended resource-mirror/install regression coverage so future locale drift is caught before packaging.

### Added

- redesigned `/library/` as a classified Great Library index/dashboard instead of a mixed flat card feed;
- added automatic `[site.title]大图书馆` page title plus localized subtitle and explicit configuration overrides;
- added a main-site-inspired seven-category ledger and a separate Wishlist ledger;
- added deterministic default browse semantics: `in_progress` + `completed`, with `in_progress` always sorted first;
- unified the Chinese Wishlist status label as `计划品鉴`;
- added 24-item numbered pagination with query-state routing and browser Back/Forward restoration;
- moved Library search into the page header and made it global across public categories/statuses;
- added vertical Current Activity rows including all explicit `in_progress` items and Steam recent-only games;
- added a 0.5-bin SVG Observable Rating Distribution curve with all-domain and per-category switching;
- added compact Grid/List layouts, local layout preference, and advanced Source/Year/other-status controls;
- expanded demo fixtures past one full 24-item category page and added UI/stats/router regression coverage.

### Changed

- `stats_schema_version` is now `2` and exposes navigation counts, rating-curve scopes, and Current Activity candidates;
- identity-bearing navigation/current/ranking data is computed only from public items while `stats_only` records may still contribute anonymous aggregate statistics;
- removed the old Load More/60-card mixed-feed behavior;
- removed the Steam lifetime-ranking details from the default UI while retaining compatible backend data;
- reduced card density and moved secondary metadata toward the detail Drawer;
- the Chirpy adapter now suppresses Chirpy's default page heading only for the PGL page via a scoped `:has(#prospero-great-library)` selector.

### Compatibility evidence

- the imported alpha.3 baseline has a successful GitHub Actions run covering Python tests, Action smoke, and clean Chirpy Starter builds for `v7.6.0`/`v7.5.0` in both Light and Dark modes;
- alpha.4 keeps those two Chirpy targets but requires a fresh uploaded CI run before its new UI/runtime contract is promoted to PASS.

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
