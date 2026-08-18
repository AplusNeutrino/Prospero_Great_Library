# Prospero_Great_Library — Implementation Status

**Version:** `0.1.0-alpha.2`  
**Architecture contract:** `PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md`  
**Repository baseline inspected:** `5052620b2bcf6a7392da324360e4e7f6e4ec7b19`

This file records implementation evidence. It does **not** override locked architecture decisions.

## Evidence levels

- `IMPLEMENTED`: code exists.
- `FIXTURE_PASS`: deterministic local test evidence exists.
- `PACKAGE_PASS`: built wheel/resource/install evidence exists.
- `CI_DEFINED`: an integration matrix/check exists but has not yet executed in the uploaded repository.
- `LIVE_UNVERIFIED`: real external credentials/API traffic not exercised here.
- `RUNTIME_UNVERIFIED`: target runtime unavailable in the packaging environment.

## Current status

| Capability | Status | Evidence |
|---|---|---|
| Canonical schema + invariants | done | FIXTURE_PASS |
| Seven-category classifier | done | FIXTURE_PASS |
| Book/Comic mutual exclusion | done | FIXTURE_PASS |
| Anime-movie canonicalization | done | FIXTURE_PASS |
| Performance -> Movie + tag | done | FIXTURE_PASS |
| Bangumi-first field precedence | done | FIXTURE_PASS |
| Bangumi v0 collections adapter | implemented | LIVE_UNVERIFIED |
| NeoDB public configurable adapter | implemented | LIVE_UNVERIFIED |
| NeoDB authenticated shelf adapter | implemented | LIVE_UNVERIFIED |
| Steam owned/recent telemetry | implemented | LIVE_UNVERIFIED |
| Steam achievements (opt-in) | implemented | LIVE_UNVERIFIED |
| Entity resolution + mappings | done | FIXTURE_PASS |
| Ambiguity diagnostics | done | FIXTURE_PASS |
| History/year partitions | done | FIXTURE_PASS |
| Steam observed playtime deltas | done | FIXTURE_PASS |
| Statistics | done | FIXTURE_PASS |
| Article exact/fuzzy association | done | FIXTURE_PASS |
| Privacy + per-item source visibility | done | FIXTURE_PASS |
| Source-failure last-good fallback | done | FIXTURE_PASS |
| Jekyll data writer | done | FIXTURE_PASS |
| Managed Chirpy installer/upgrader | done | FIXTURE_PASS + PACKAGE_PASS |
| Packaged Chirpy resources | done | PACKAGE_PASS |
| Vanilla JS library UI | done | static syntax + contract tests |
| Progressive no-JS fallback | done | FIXTURE_PASS |
| Safe protocol-filtered Drawer links | done | FIXTURE_PASS |
| zh-CN + en locale files | done | resource-mirror test |
| Expanded architecture demo | done | FIXTURE_PASS |
| Composite GitHub Action smoke | defined | CI_DEFINED |
| Chirpy v7.6/v7.5 Light/Dark build matrix | defined | CI_DEFINED |
| Real Chirpy/Jekyll build | pending | RUNTIME_UNVERIFIED |
| Real Bangumi/NeoDB/Steam calls | pending | LIVE_UNVERIFIED |

## Local verification at packaging

```text
pytest:                         PASS — 40 tests
Python compileall:              PASS
Ruby plugin syntax:             PASS
JavaScript syntax:              PASS
fixture demo rebuild:           PASS — 11 items
source-failure fallback test:   PASS
schema invariant tests:         PASS
installer conflict/backup:      PASS
resource mirror:                PASS
wheel resource/install smoke:   PASS
```

The repository CI contains the missing runtime checks. They remain `CI_DEFINED` / `RUNTIME_UNVERIFIED` until a real GitHub Actions run provides evidence.
