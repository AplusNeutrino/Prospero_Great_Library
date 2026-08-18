# Delivery Notes — 0.1.0-alpha.2

## Baseline

Inspected repository baseline:

```text
AplusNeutrino/Prospero_Great_Library
main: 5052620b2bcf6a7392da324360e4e7f6e4ec7b19
```

At packaging time the remote `main` still contains only `PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md`. This delivery continues from the local `0.1.0-alpha.1` implementation rather than treating the empty implementation state on `main` as a rollback. No GitHub write is performed by this delivery process.

## Release focus

`0.1.0-alpha.2` is a Phase-7 hardening release. It keeps the Alpha.1 data model and source architecture, and closes evidence/product gaps around installation, demo coverage, UI resilience, compatibility CI, and security boundaries.

## Added / hardened

- Managed `pgl install --adapter chirpy` command.
  - requires an existing Jekyll `_config.yml`;
  - manifest-backed safe upgrades;
  - local conflicts preserved by default;
  - `--force` replacement with backup by default;
  - user-owned `mappings.yml` never overwritten.
- Chirpy adapter resources embedded in the Python wheel and byte-mirrored from the release tree.
- `pgl doctor` detects the supported Chirpy `7.6` / `7.5` lines and warns on older detected lines.
- Demo expanded to 11 deterministic items covering all seven categories, all five statuses, Bangumi-only, NeoDB-only, Steam-only, merged entities, performance Movie, Anime Movie, Comic vs Book, article associations, timeline, Steam statistics, and positive observed Steam deltas.
- Library UI now uses real client-side progressive rendering rather than initially emitting every item.
- First 60 server-rendered cards remain available as a no-JS/static-data failure fallback.
- Search is debounced; filters/view/sort persist in the URL query string.
- Drawer/card client rendering uses DOM APIs instead of `innerHTML`.
- External and article URLs are restricted to HTTP(S) before clickable links are emitted.
- Chirpy-specific CSS is reduced to a thin current-variable adapter.
- Composite Action updated to current `actions/setup-python@v7`.
- Reference Pages workflow aligned with current Chirpy Starter action majors (`checkout@v7`, `configure-pages@v6`, Ruby 3.4, `upload-pages-artifact@v5`, `deploy-pages@v5`).
- CI now defines:
  - Python 3.11 / 3.13 tests;
  - local composite-Action smoke test;
  - Chirpy `v7.6.0` and `v7.5.0` × Light/Dark build matrix.
- Added explicit schema-invariant and source-failure/last-good regression tests.

## Final local evidence

```text
pytest                           PASS — 40 tests
Python compileall                PASS
Ruby plugin syntax               PASS
Vanilla JS syntax                PASS
Demo two-stage fixture sync       PASS — 11 first-seen; then 4 changes
Steam positive delta events       PASS — 2
Article association               PASS — 2 linked entities / 2 posts
Installer idempotency/conflicts   PASS
Wheel resource inclusion          PASS
Wheel isolated install            PASS — 0.1.0-alpha.2
Source-failure last-good fallback PASS
Schema invariants                 PASS
```

## Runtime evidence still pending

These are **unverified**, not failures:

- real Bangumi request with a real account/token;
- real Steam request with a real API key/profile visibility configuration;
- real NeoDB authenticated/public collection request for the selected instance;
- actual GitHub execution of the composite-Action smoke job;
- actual Jekyll builds for Chirpy v7.6.0/v7.5.0 in Light/Dark.

The packaging environment has Ruby but no Bundler/Jekyll executable. The compatibility matrix is therefore shipped as executable GitHub CI but must not be reported as runtime PASS until the uploaded workflow runs.

## Repository-state privacy note

PGL filters hidden data before public site artifacts, but `_data/prospero_great_library/sources/` is synchronization state. If a blog repository is public, site-output privacy does not make those stored source snapshots private.

## Manual-upload validation order

1. Upload/extract the package into the repository root, preserving `.github/`.
2. Let `PGL CI` run.
3. Treat `chirpy-compatibility` as the first real Chirpy runtime evidence.
4. If CI passes, validate live sources one at a time: Bangumi, Steam, then NeoDB.
5. Update `IMPLEMENTATION_STATUS.md` only when the corresponding evidence actually exists.
