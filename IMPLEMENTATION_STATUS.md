# Prospero_Great_Library — Implementation Status

**Version:** `0.1.0-alpha.4`  
**Architecture contract:** `PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md`  
**UI/IA contract:** `docs/Prospero_Great_Library_UI_Revision_Plan.md`  
**Repository baseline inspected:** `main` commit `02b513756c1b247ff5a3957e74963f3de6ec453c` (UI plan only on top of imported alpha.3 code).

This file records implementation evidence. It does **not** override locked architecture or UI-plan decisions.

## Evidence levels

- `IMPLEMENTED`: code exists.
- `FIXTURE_PASS`: deterministic local test evidence exists.
- `PACKAGE_PASS`: built wheel/resource/install evidence exists.
- `CI_PASS`: the exact referenced code ran successfully in GitHub Actions.
- `LIVE_PASS`: real external service data reached a deployed PGL sync successfully.
- `USER_DEPLOYED`: the owner reports the generated integration was deployed successfully.
- `LIVE_UNVERIFIED`: optional live behavior has not been independently evidenced.

## Core/data status

| Capability | Status | Evidence |
|---|---|---|
| Canonical schema + locked category invariants | done | FIXTURE_PASS |
| Bangumi v0 collections + pagination | done | LIVE_PASS + FIXTURE_PASS |
| Bangumi private collection interception | done | LIVE_PASS + FIXTURE_PASS |
| Retroactive privacy/history scrub + privacy-audit | done | FIXTURE_PASS |
| NeoDB authenticated shelf adapter | done | LIVE_PASS |
| NeoDB public configurable mode | implemented | LIVE_UNVERIFIED (instance-dependent) |
| Steam owned-library telemetry | done | LIVE_PASS |
| Steam recent-play telemetry | implemented | FIXTURE_PASS / best-effort live path |
| Steam achievements (opt-in) | implemented | LIVE_UNVERIFIED |
| Entity resolution + Bangumi-first merge | done | LIVE_PASS + FIXTURE_PASS |
| History/year partitions + observed Steam deltas | done | FIXTURE_PASS |
| Article exact/fuzzy association | done | FIXTURE_PASS |
| Hidden/stats-only/source privacy | done | FIXTURE_PASS |
| Source-failure last-good fallback | done | FIXTURE_PASS |

## Alpha.4 UI / IA status

| Capability | Status | Evidence |
|---|---|---|
| `[site.title]大图书馆` title + subtitle | implemented | FIXTURE/static contract PASS |
| Root Great Library dashboard (no mixed feed) | implemented | FIXTURE/static contract PASS |
| Seven-category ledger | implemented | FIXTURE/static contract PASS |
| Default `in_progress + completed` browser | implemented | FIXTURE_PASS |
| `in_progress` always before completed | implemented | FIXTURE_PASS |
| Separate Wishlist + `计划品鉴` label | implemented | FIXTURE_PASS |
| `on_hold` / `dropped` hidden by default | implemented | FIXTURE_PASS |
| Global Library-header search | implemented | FIXTURE/static contract PASS |
| 24-item numbered pagination + History API router | implemented | FIXTURE/static contract PASS |
| Vertical Current Activity + Steam recent-only | implemented | FIXTURE_PASS |
| Observable Rating Distribution SVG curve | implemented | FIXTURE_PASS |
| Per-domain rating switching | implemented | FIXTURE/static contract PASS |
| Unrated/wishlist/other statuses excluded from chart | implemented | FIXTURE_PASS |
| Steam ranking removed from default UI | implemented | static contract PASS |
| Compact Grid/List + local preference | implemented | static contract PASS |
| Safe detail Drawer + timeline retained | implemented | regression PASS |
| Stats-only identity isolation in navigation/current/ranking | implemented | FIXTURE_PASS |
| zh-CN + en alpha.4 locales | implemented | resource-mirror PASS |

## Compatibility evidence

The imported alpha.3 code has a real successful GitHub Actions run (`32114762265`) with:

```text
action-smoke                         PASS
test (Python 3.11)                   PASS
test (Python 3.13)                   PASS
Chirpy v7.6.0 light                  PASS
Chirpy v7.6.0 dark                   PASS
Chirpy v7.5.0 light                  PASS
Chirpy v7.5.0 dark                   PASS
```

The four Chirpy jobs installed PGL into clean Chirpy Starter checkouts and performed real production Jekyll builds.

**Alpha.4 exact-runtime status:** `RUN_PENDING`. Alpha.4 changes the UI/router/styles and adds a scoped `dynamic-title` contract, so the successful alpha.3 runtime is baseline evidence only. A new CI run is required after the user uploads alpha.4.

## Local alpha.4 evidence before final packaging

Current pre-release implementation evidence:

```text
pytest                                  PASS — 65 tests
Demo pipeline                           PASS — 39 canonical items
Book default-browse fixture             PASS — 29 items (>24 page size)
Rating curve observations               PASS — 35 eligible rated observations
Python compileall                       PASS
JavaScript syntax                        PASS — core + packaged resource
Ruby plugin syntax                       PASS — core + packaged resource
JSON/YAML parse                          PASS — 19 JSON / 14 YAML
Resource/UI/stats mirror subset          PASS — 14 tests
Installer idempotency                    PASS — user mappings preserved
History identical-rerun idempotency      PASS — 39 first events / 0 duplicate events
Wheel build + isolated import/resources  PASS
Public privacy / literal-secret scan     PASS
```

The exact alpha.4 Chirpy runtime matrix remains pending upload; all package-level checks available in the local environment have passed.

## Live deployment evidence retained from alpha.3

A production blog sync on 2026-08-18 completed all three enabled collection paths and exercised Bangumi private filtering against real private records. Exact personal/private collection counts are intentionally omitted from public project documentation. The owner also deployed the generated PGL/Chirpy integration successfully.
