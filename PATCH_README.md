# Prospero Great Library 0.1.0-alpha.6 — incremental overlay delivery

**Required baseline:** upstream `main` commit `1a217d2b519780ef11f0aafce8208972f8eae00a` (`0.1.0-alpha.5`).

This archive is an **incremental overlay**, not a standalone copy of the whole repository. Upload/copy its files over the matching paths in the alpha.5 repository; **do not delete repository files that are absent from this archive**.

## Implemented fixes

### 1. Compact search

- replaces the host-theme-dependent `.visually-hidden` label with PGL-owned `.pgl-sr-only`;
- removes the oversized pill search presentation;
- desktop search defaults to ~184 px / 34 px with a 9 px radius and expands only on focus;
- mobile retains the icon → expanded-search interaction.

### 2. Steam telemetry recovery without weakening privacy

- keeps `filter_private_games=true` and `privacy_fail_closed=true` semantics;
- public Community XML first uses strict parsing;
- if strict parsing fails, removes only characters forbidden by XML 1.0 and retries;
- if malformed text still prevents XML parsing, conservatively recovers **numeric AppIDs only** from complete `<game>` blocks inside a proven `<games>...</games>` container;
- rejects HTML/lookalike/missing-structure responses and still fails closed;
- recovered AppIDs only form the anonymous public allow-list; playtime remains sourced from authenticated `GetOwnedGames`;
- a reattached Steam source establishes a new cumulative baseline and does **not** fabricate lifetime playtime as a current-year delta;
- later successful syncs resume normal observed deltas;
- UI renders unavailable Steam telemetry as `— / Steam 数据暂不可用`, never as a false `0.0h`.

**Migration note:** alpha.5 fail-closed already removed identity-bearing Steam history from the current public tree. Alpha.6 intentionally does not reconstruct private/history data from Git history. On the first successful alpha.6 Steam recovery, lifetime playtime returns immediately, while observed yearly increments restart from the new safe baseline and grow from subsequent successful syncs.

### 3. Observable Rating Distribution polish

- retains the existing real integer observation bins;
- adds low-opacity ghost frequency bars;
- adds a gradient area under the existing monotone curve;
- uses a slimmer curve with subtle data points;
- adds `N · mean · mode` summary text;
- changes category switching from pill buttons to underline-style tabs;
- remains Vanilla JS + local SVG; no Chart.js/ECharts/runtime API calls.

## New auto-installed assets

`pgl-polish.css` and `pgl-rating-polish.js` are first-class Chirpy resources. The existing installer discovers all packaged assets automatically.

## After merging alpha.6 into PGL

Upgrade the Blog's PGL installer resources and pinned Action SHA, then manually run one PGL Sync. The first successful Steam sync after alpha.5 is a baseline restoration; run a later sync after gameplay to verify a genuine new `steam_playtime_delta`.
