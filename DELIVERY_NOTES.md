# Delivery Notes — 0.1.0-alpha.4

## Baseline and design provenance

This delivery was built from the repository state represented by:

```text
AplusNeutrino/Prospero_Great_Library
main: 02b513756c1b247ff5a3957e74963f3de6ec453c
```

That latest commit adds the approved UI/IA design source:

```text
docs/Prospero_Great_Library_UI_Revision_Plan.md
```

The underlying code baseline is the imported alpha.3 privacy-hardened implementation. No GitHub write/push is performed by this delivery process.

## Release focus

`0.1.0-alpha.4` is the **Great Library information-architecture and large-library usability release**. It deliberately leaves source ownership, entity schema, history semantics, and alpha.3 privacy boundaries intact.

### Root Library redesign

`/library/` is no longer a mixed Book/Comic/Movie/Drama/Anime/Game/Music feed. It now acts as a classified index/dashboard:

```text
site-aware Great Library title + subtitle
Library-local search
Current Activity ledger
Observable Rating Distribution
seven-category ledger
separate Wishlist entry
Timeline
```

### Classified browsing

- Default category browse contains only `in_progress` and `completed`.
- Every `in_progress` item sorts before every `completed` item, independent of secondary sort.
- Wishlist is a separate classified area and uses `计划品鉴` in zh-CN.
- `on_hold` and `dropped` are excluded from normal browsing but remain available through global search/advanced status access.
- There is no permanent All Collection mixed-browser view.
- Category and Wishlist results use 24 items per page.
- URL state + History API preserve category/page/search state and browser Back/Forward behavior.

### Search and Current Activity

- Search moved from the old filter dashboard into the Library header.
- Search is global across all public categories and statuses and groups results by category.
- Current Activity is vertical, unbounded by the old eight-item limit, and includes both explicit `in_progress` items and Steam recent-only games.

### Observable Rating Distribution

The old rating chips are replaced with a lightweight Vanilla-JS/SVG curve:

- 0.5-point real frequency bins;
- no KDE or fabricated observations;
- visual monotone smoothing only;
- unrated records excluded;
- wishlist/on_hold/dropped excluded from the default observed distribution;
- quick All/Book/Comic/Movie/Drama/Anime/Game/Music switching.

The old Steam lifetime-ranking details are removed from the default UI, while compatible backend ranking data remains available.

### Compact catalogue layouts

Grid/List switching remains, but both layouts are compressed. Secondary source/detail metadata is moved toward the existing Drawer so browsing density is substantially higher. The layout preference is stored locally rather than in the URL.

## Data/statistics changes

`stats_schema_version` is now `2`. New derived fields include:

```text
navigation.default_by_category
navigation.wishlist_by_category
navigation.other_status_by_category
rating_curve_distribution
current_activity
```

Identity-bearing navigation/current/ranking fields are generated only from public items. `stats_only` records may still contribute anonymous aggregate totals/distributions without reappearing by title through a side channel.

## Chirpy adapter

PGL still does not copy Chirpy layouts. Alpha.4 adds its own page header, so the adapter suppresses Chirpy's default page heading only for an article containing `#prospero-great-library`. The current Chirpy `v7.6.0` and `v7.5.0` page-layout structures were inspected during development and CI now checks the expected `dynamic-title`/`.content` contract before building.

## Compatibility evidence

The alpha.3 code imported into this baseline already produced GitHub Actions run `32114762265` with all jobs successful, including clean-starter Jekyll production builds for:

```text
Chirpy v7.6.0 × light  PASS
Chirpy v7.6.0 × dark   PASS
Chirpy v7.5.0 × light  PASS
Chirpy v7.5.0 × dark   PASS
```

This is historical baseline evidence. The exact alpha.4 package has not existed on GitHub yet, so its corresponding four-cell runtime remains `RUN_PENDING` until the owner uploads it and CI executes.

## Demo / regression coverage

The demo now contains 39 canonical items, including a Book category with 29 default-visible records so 24-item pagination is exercised rather than merely asserted by source inspection. The test suite also covers Wishlist separation, default status order, Current Activity, 0.5 rating bins, stats-only identity isolation, global search/router contracts, and compact layout contracts.

## Privacy preservation

Alpha.3 privacy hardening remains a release invariant:

- Bangumi private collection interception remains default-on;
- current/history scrub remains active;
- hidden/stats-only/source visibility rules remain active;
- no private-ID index is published;
- public diagnostics remain metadata-minimized by default;
- PGL still does not rewrite Git history automatically.

## Final-package verification

This section is updated during final QA immediately before the ZIP/checksum files are created.

```text
pytest                                      PASS — 65 tests
Python compileall                           PASS
Ruby syntax                                 PASS — core + packaged plugin
JavaScript syntax                           PASS — core + packaged asset
JSON/YAML parse                             PASS — 19 JSON / 14 YAML
Demo pipeline                               PASS — 39 canonical items
Resource/UI/stats mirror subset             PASS — 14 tests
Installer idempotency                       PASS — 19 managed files; mappings preserved
Wheel build + isolated install              PASS — 0.1.0a4 wheel/resources
History idempotency                         PASS — 39 first events; 0 on identical rerun
Secret/public-privacy leakage scan          PASS — 15 public JSON artifacts checked
ZIP per-file checksum verification          PASS — verified after archive creation
Alpha.4 exact Chirpy 7.6/7.5 Light/Dark     RUN_PENDING (requires upload)
```

The final ZIP SHA-256 is written to the sibling `.sha256` file after packaging. Per-file repository checksums are stored in `SHA256SUMS.txt`.
