# Prospero_Great_Library — Implementation Status

**Version:** `0.1.0-alpha.3`  
**Architecture contract:** `PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md`  
**Reconstructed development baseline:** upstream `main` at `115c7f2573033170d7ab72f0b3c18958899cb5dd` plus deployed-blog runtime evidence from 2026-08-18.

This file records implementation evidence. It does **not** override locked architecture decisions.

## Evidence levels

- `IMPLEMENTED`: code exists.
- `FIXTURE_PASS`: deterministic local test evidence exists.
- `PACKAGE_PASS`: built wheel/resource/install evidence exists.
- `LIVE_PASS`: real external service data reached a deployed PGL sync successfully.
- `USER_DEPLOYED`: the owner reports the generated integration was deployed successfully on the production blog.
- `CI_DEFINED`: an integration matrix/check exists but a retrievable run result is not recorded here.
- `LIVE_UNVERIFIED`: optional live behavior has not been independently evidenced.

## Current status

| Capability | Status | Evidence |
|---|---|---|
| Canonical schema + invariants | done | FIXTURE_PASS |
| Seven-category classifier | done | FIXTURE_PASS |
| Book/Comic mutual exclusion | done | FIXTURE_PASS |
| Anime-movie canonicalization | done | FIXTURE_PASS |
| Performance -> Movie + tag | done | FIXTURE_PASS |
| Bangumi-first field precedence | done | FIXTURE_PASS |
| Bangumi v0 collections adapter | done | LIVE_PASS |
| Bangumi paged collection response | done | LIVE_PASS + FIXTURE_PASS |
| Bangumi private collection interception | done | LIVE_PASS + FIXTURE_PASS |
| Retroactive privacy history scrub | done | FIXTURE_PASS |
| Privacy audit CLI / fail-closed invariant | done | FIXTURE_PASS |
| NeoDB authenticated shelf adapter | done | LIVE_PASS |
| NeoDB public configurable adapter | implemented | LIVE_UNVERIFIED (instance-dependent) |
| Steam owned-library telemetry | done | LIVE_PASS |
| Steam recent-play telemetry | implemented | best-effort; separate live evidence not recorded |
| Steam achievements (opt-in) | implemented | LIVE_UNVERIFIED |
| Entity resolution + mappings | done | LIVE_PASS + FIXTURE_PASS |
| Ambiguity diagnostics | done | LIVE_PASS + FIXTURE_PASS |
| History/year partitions | done | FIXTURE_PASS |
| Steam observed playtime deltas | done | FIXTURE_PASS |
| Statistics | done | LIVE_PASS + FIXTURE_PASS |
| Article exact/fuzzy association | done | FIXTURE_PASS |
| PGL hidden/stats-only/source privacy | done | FIXTURE_PASS |
| Source-failure last-good fallback | done | FIXTURE_PASS |
| Jekyll data writer | done | USER_DEPLOYED + FIXTURE_PASS |
| Managed Chirpy installer/upgrader | done | PACKAGE_PASS + USER_DEPLOYED |
| Packaged Chirpy resources | done | PACKAGE_PASS |
| Vanilla JS library UI | done | USER_DEPLOYED + static syntax/contract tests |
| Progressive no-JS fallback | done | FIXTURE_PASS |
| Safe protocol-filtered Drawer links | done | FIXTURE_PASS |
| zh-CN + en locale files | done | resource-mirror test |
| Expanded architecture demo | done | FIXTURE_PASS |
| Composite GitHub Action | done | USER_DEPLOYED |
| Scheduled sync -> persist -> explicit Pages dispatch pattern | done | USER_DEPLOYED |
| Chirpy v7.6/v7.5 Light/Dark build matrix | defined | CI_DEFINED |
| Steam achievements live calls | pending | LIVE_UNVERIFIED |
| NeoDB anonymous/public collection mode | pending per instance | LIVE_UNVERIFIED |

## Live deployment evidence used for this status

A production blog sync on 2026-08-18 reported all three enabled sources as `ok`. All three enabled source collection paths completed successfully, and the Bangumi privacy boundary filtered a nonzero set of real private collection records before generated public state was written. Exact user-library/private-record counts are intentionally omitted from the public project documentation. This is runtime evidence for the main collection-sync path, not proof of every optional sub-endpoint.

The owner also reports the generated PGL/Chirpy integration was deployed successfully. GitHub check-run evidence was not available through the connector used while preparing this package, so the repository's formal compatibility matrix remains recorded separately rather than being retroactively marked as CI-passed.

## Final local verification evidence for alpha.3

```text
pytest                                      PASS — 54 tests
Python compileall                           PASS
Ruby plugin syntax                          PASS — Syntax OK
JavaScript syntax                           PASS — node --check
JSON/YAML parse                             PASS
Demo fixture pipeline                       PASS — 11 items; controlled second stage 4 events; 2 Steam deltas; 2 linked entities
Identical-fixture history idempotency       PASS — first sync 11 events; second identical sync 0 new events
Privacy migration/history scrub             PASS
Mixed-source private-history preservation   PASS
Source-failure last-good fallback            PASS
Schema/category invariants                  PASS
Installer idempotency + user mapping retain PASS
Wheel build                                 PASS — offline build with existing local build toolchain
Wheel isolated install/import/resources     PASS
Account/secret leakage scan                 PASS
Exact Chirpy v7.6/v7.5 Light/Dark build     RUN_PENDING
```

The packaging container has Ruby but does not have Bundler/Jekyll installed, and network access is unavailable for fetching missing Ruby dependencies. Therefore the four-cell Chirpy runtime matrix remains `CI_DEFINED / RUN_PENDING`; Ruby syntax/static contract checks are not represented as a full Jekyll runtime pass.

The current compatibility targets remain Chirpy `v7.6.0` and `v7.5.0`; as of 2026-08-18 those are the two most recent published RubyGem releases.
