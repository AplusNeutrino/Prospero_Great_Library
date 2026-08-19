# Prospero_Great_Library — Implementation Status

**Version:** `0.1.0-alpha.5`  
**Architecture contract:** `PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md`  
**UI/IA contract:** `docs/Prospero_Great_Library_UI_Revision_Plan.md`  
**Development baseline:** merged alpha.4 r2 (`main` commit `46bba99dca66bf8e3218c3f5ffb5ef7eded01a0d`).

This file records implementation evidence. It does **not** override locked architecture or UI-plan decisions.

## Evidence levels

- `IMPLEMENTED`: code exists.
- `FIXTURE_PASS`: deterministic local test evidence exists.
- `PACKAGE_PASS`: built wheel/resource/install evidence exists.
- `CI_PASS`: the exact referenced code ran successfully in GitHub Actions.
- `LIVE_PASS`: real external service data reached a deployed PGL sync successfully.
- `LIVE_UNVERIFIED`: external behavior is implemented but needs a fresh real deployment.

## Core/data status

| Capability | Status | Evidence |
|---|---|---|
| Canonical schema + seven-category invariants | done | FIXTURE_PASS |
| Bangumi collections + pagination | done | LIVE_PASS |
| Bangumi private collection interception | done | LIVE_PASS |
| Bangumi Book/Comic classification from SlimSubject metadata tags | fixed alpha.5 | FIXTURE_PASS; LIVE_UNVERIFIED |
| NeoDB authenticated shelf | done | LIVE_PASS |
| NeoDB public configurable mode | implemented | LIVE_UNVERIFIED |
| Steam owned/playtime telemetry | done | prior LIVE_PASS |
| Steam public-only AppID privacy gate | fixed alpha.5 | FIXTURE_PASS; LIVE_UNVERIFIED |
| Steam public cover enrichment | fixed alpha.5 | FIXTURE_PASS; LIVE_UNVERIFIED |
| Steam privacy fail-closed + retroactive history scrub | fixed alpha.5 | FIXTURE_PASS |
| Steam achievements (opt-in) | implemented | LIVE_UNVERIFIED |
| Entity resolution + Bangumi-first merge | done | LIVE_PASS |
| History/year partitions + observed Steam deltas | done | FIXTURE_PASS |
| Hidden/stats-only/source privacy | done | FIXTURE_PASS |

## Alpha.5 UI fixes

| Capability | Status | Evidence |
|---|---|---|
| Chirpy sidebar `[site.title]大图书馆` / Great Library | fixed | FIXTURE_PASS |
| Explicit `ui.title` sidebar override | fixed | FIXTURE_PASS |
| Integer-only Observable Rating Distribution bins 1–10 | fixed | FIXTURE_PASS |
| Removed hidden semicolon rating dump | fixed | static contract PASS |
| Current Activity canonical category ordering | fixed | FIXTURE_PASS |
| Existing alpha.4 dashboard/search/pagination/Grid/List | retained | regression PASS |

## Compatibility evidence

Alpha.4 r2 has a fully successful GitHub Actions run `32202478262`, including Python tests, Action smoke, and clean Chirpy Starter builds for `v7.6.0`/`v7.5.0` in both Light and Dark modes.

Alpha.5 exact-runtime status remains `RUN_PENDING` until this delivery is uploaded. The Steam public-visibility path also remains `LIVE_UNVERIFIED` until a real authenticated sync confirms the public-AppID probe against production Steam settings.
