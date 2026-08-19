# Prospero_Great_Library

> Universal personal media library extension/starter kit for Jekyll, with first-class Chirpy integration.

**Release:** `0.1.0-alpha.4`  
**Architecture source of truth:** [`PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md`](./PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md)

PGL aggregates media records from **Bangumi**, **NeoDB**, and **Steam**, normalizes them into one canonical library, tracks compact history events, and renders a fully static `/library/` page.

## V1 taxonomy

```text
Book | Comic | Movie | Drama | Anime | Game | Music
```

Locked semantics:

- one item belongs to exactly one category;
- Book and Comic never overlap;
- anime movies are Anime, never duplicated into Movie;
- opera/stage play/musical are Movie items with a `performance` tag;
- Bangumi beats NeoDB when both provide the same logical field by default;
- Steam supplies Game telemetry, not subjective completion status.

## Architecture

```text
Bangumi ─┐
NeoDB ───┼─> Python adapters -> normalize -> classify -> resolve -> merge
Steam ───┘                                          │
                                                    ├─> current library
                                                    ├─> history / stats
                                                    ├─> post associations
                                                    └─> Jekyll static data
                                                             │
                                                     Chirpy + Vanilla JS
```

No runtime backend is required after the Jekyll build.

## Alpha implementation status

| Area | Status |
|---|---|
| Canonical schema / classifier | Implemented + fixture tested |
| Bangumi v0 collection adapter | Implemented; paged-response handling + private-collection filter; live deployed sync verified |
| NeoDB adapter | Implemented as capability/config-driven adapter; authenticated shelf mode verified in a deployed blog; public mode remains instance-capability-driven |
| Steam owned/recent telemetry | Owned-library sync verified in a deployed blog; recent-play enrichment remains best-effort by design |
| Steam achievements | Implemented; opt-in and conservatively refreshed for recently played games with visible stats |
| Entity resolution | Implemented + fixture tested |
| Bangumi-first merge | Implemented + fixture tested |
| History / Steam observed deltas | Implemented + fixture tested |
| Blog-post association | Implemented + fixture tested |
| Jekyll UI / Chirpy adapter | Alpha.4 classified Great Library UI implemented; local contract/fixture tested |
| Chirpy v7.6/v7.5 build matrix | Alpha.3 four-cell matrix passed in GitHub Actions; exact alpha.4 matrix rerun pending upload |

Do not treat `alpha.4` as a claim that every optional endpoint is live-verified. Steam achievements remain opt-in/unverified, and public NeoDB behavior still depends on the selected instance.

## Quick start

### 1. Install the Python core locally

```bash
python -m pip install -e .
pgl --version
```

### 2. Install the Chirpy integration into a Jekyll site

```bash
pgl install --adapter chirpy --site-root /path/to/your/jekyll-site --dry-run
pgl install --adapter chirpy --site-root /path/to/your/jekyll-site
```

The installer requires an existing Jekyll `_config.yml`, manages only PGL-owned files, records ownership hashes in `.pgl-install.json`, preserves local conflicts by default, and backs up forced replacements under `.pgl-backups/`. `_data/prospero_great_library/mappings.yml` is always treated as user-owned.

### 3. Merge `config.example.yml` into `_config.yml`

All three source adapters are optional.

### 4. Add GitHub repository secrets

Depending on enabled sources:

```text
BANGUMI_ACCESS_TOKEN
NEODB_ACCESS_TOKEN   # only when your NeoDB mode/instance requires it
STEAM_API_KEY
```

Never place tokens in `_config.yml`.

### 4.1 Bangumi private collections

Authenticated Bangumi collection reads can include entries the owner marked private. For public repositories/sites, enable the source-level publication boundary:

```yaml
prospero_great_library:
  sources:
    bangumi:
      hide_private_collections: true  # alpha.3 default; keep explicit for clarity
```

When enabled, private Bangumi records are removed **before source snapshots, entity resolution, merge, statistics, associations, and new history events**. Alpha.3 also retroactively sanitizes already-persisted PGL history when a currently-private Bangumi record can be linked to a previously public canonical entity. Private source IDs used for that migration are kept only in memory during the sync and are not persisted as a private-item index.

Run a read-only audit with:

```bash
pgl privacy-audit --site-root .
```

Use `--apply` only when you explicitly want that command to perform the sanitized sync/write. Ordinary `pgl sync` already applies the privacy boundary automatically. The audit needs the same source credentials as a normal live sync if it is expected to discover upstream-private records. `pgl doctor` warns when an authenticated Bangumi token is present but `hide_private_collections` is disabled.

> **Git-history boundary:** PGL can sanitize the current working tree and future generated artifacts, but a normal new commit cannot erase private data that was already committed to an earlier revision of a public Git repository. If an older commit ever contained data that should never have been public, repository-history rewriting/removal is a separate one-time maintenance operation. PGL deliberately does not attempt that destructive Git operation automatically.

Detailed privacy counts and scrub reasons are not persisted by default. `privacy.publish_diagnostics: false` is the default; set it to `true` only if you intentionally want those counts/reasons in generated repository data. `pgl privacy-audit` still reports full details to the invoking process so an operator can inspect them without making them part of the published state.

### 5. Diagnose

```bash
pgl doctor --site-root .
```

### 6. Sync

```bash
pgl sync --site-root .
```

For a deterministic no-network demo:

```bash
pgl build-data --site-root demo/site --config _config.yml --fixtures demo/fixtures
```

## NeoDB alpha configuration

NeoDB is federated and instance versions can differ. PGL therefore keeps the endpoint layer configurable and never falls back to HTML scraping.

### Default public mode

```yaml
prospero_great_library:
  sources:
    neodb:
      enabled: true
      instance: "https://neodb.social"
      mode: public
      username: "your-name"
      collection_endpoint: "DOCUMENTED_PUBLIC_ENDPOINT_WITH_{username}_IF_NEEDED"
```

Public mode is the product default, but PGL does not claim every NeoDB instance exposes an anonymous personal-shelf endpoint. If your instance does not, use authenticated mode.

### Authenticated mode

```yaml
prospero_great_library:
  sources:
    neodb:
      enabled: true
      instance: "https://neodb.social"
      mode: authenticated
      authenticated_shelf_endpoint: "/api/me/shelf/{shelf}"
      shelf_types: [wishlist, progress, complete, dropped]
```

Add `NEODB_ACCESS_TOKEN` as a secret. The adapter paginates shelf responses, maps `shelf_type` into PGL status, treats `rating_grade` as the user's rating, keeps the item community rating only as source metadata, and makes relative NeoDB item URLs absolute. The shelf endpoint remains configurable for instance compatibility.

For a custom public endpoint, `collection_endpoint` supports `{username}` substitution and common JSON collection shapes (`list`, `items`, `data`, `results`, `collections`). If the required capability is unavailable, NeoDB becomes `capability_unavailable`; other sources continue and the last-known-good snapshot is preserved.

## Generated data

```text
_data/prospero_great_library/
├── library.json
├── stats.json
├── sync_status.json
├── associations.json
├── mappings.yml
├── sources/
│   ├── bangumi.json
│   ├── neodb.json
│   └── steam.json
└── diagnostics/
    ├── entity_resolution.json
    ├── associations.json
    └── privacy.json

assets/data/prospero_great_library/
├── library.json
├── stats.json
├── sync_status.json
├── manifest.json
└── history/
    └── YYYY.json
```

Source snapshots under `_data/.../sources/` are state for diff/failure recovery. If your repository itself is public, remember that repository visibility is distinct from PGL's **site-output privacy filters**.

Privacy applies to history as well as current cards. If an item is changed to `hidden`, `stats_only`, or becomes a currently-detected private Bangumi collection, PGL sanitizes affected persisted timeline events before rebuilding public history partitions. This closes the migration gap where deleting an item from the current library alone would leave its old timeline visible.

## History semantics

PGL records observed state transitions, not invented historical facts.

For Steam:

```text
observed delta = newest lifetime playtime - previous successful lifetime playtime
```

A positive delta becomes `steam_playtime_delta`. A negative delta becomes a correction diagnostic/event and is not counted as negative gameplay.

Annual Steam figures therefore mean **observed playtime increase during PGL tracking**, with sync-boundary limitations.

## Entity resolution

Order:

```text
1. explicit mapping
2. durable identifier
3. known cross-source link
4. ISBN/ISBN13
5. exact normalized title + compatible category/year
6. alias + compatible category/year
7. high-confidence fuzzy candidate
8. ambiguous => remain separate
```

Default thresholds:

```text
>= 0.95 automatic
0.80–0.9499 suggestion only
< 0.80 ignored
```

Manual escape hatch:

```yaml
# _data/prospero_great_library/mappings.yml
entities:
  - id: game:my-stable-id
    bangumi: 12345
    steam: 39140
```

Per-item privacy/source visibility can use the same mapping file:

```yaml
privacy:
  - entity: game:my-stable-id
    hide_sources: [steam]
  - entity: book:private-id
    hidden: true
```

## Blog-post association

PGL scans `_posts` without rewriting them.

Exact automatic signals:

- canonical PGL ID in front matter;
- Bangumi subject URL;
- NeoDB item URL;
- Steam store URL/AppID;
- ISBN.

Optional explicit front matter:

```yaml
library:
  id: game:my-stable-id
```

High-confidence title/alias matches may auto-associate. Ambiguous candidates are emitted to diagnostics and never silently inserted into posts.

To show an associated library mini-card/link inside post pages, integrate:

```liquid
{% include pgl/post-card.html %}
```

through a small Chirpy hook/include rather than forking the whole post layout.

## UI

Alpha.4 turns `/library/` into a classified **Great Library index/dashboard** rather than a mixed flat feed. The default public browser now provides:

- a site-aware title (`[site.title]大图书馆` by default) and localized subtitle;
- a compact Library-local search box in the header;
- a vertical **Current** activity ledger containing every explicit `in_progress` item plus Steam recent-only games;
- an SVG **Observable Rating Distribution** curve with all-domain and seven-category switching;
- a seven-category ledger for Book / Comic / Movie / Drama / Anime / Game / Music;
- a separate Wishlist area whose Chinese public label is `计划品鉴`;
- category browsing limited by default to `in_progress + completed`, with `in_progress` always ordered first;
- `on_hold` / `dropped` hidden from default browsing but still discoverable through global search / advanced status access;
- no permanent "All Collection" mixed browsing view; global search is the cross-category discovery surface;
- true numbered pagination at **24 items per page**, with URL/history state and Back/Forward restoration;
- compact Grid/List modes with the user's layout preference stored locally;
- advanced Source/Year filtering and category-appropriate sorting;
- the existing safe detail Drawer and lazy-loaded yearly timeline.

Root `/library/` remains meaningful without JavaScript (header/current/statistical/category index content is server rendered), while classified pagination/search requires the static JavaScript controller.

## Theme contract

Public PGL styles are neutral. Override CSS variables in your site:

```css
:root {
  --pgl-bg: transparent;
  --pgl-surface: var(--card-bg);
  --pgl-border: rgba(127, 127, 127, .25);
  --pgl-text: inherit;
  --pgl-muted: #777;
  --pgl-accent: #6c63ff;
}
```

Personal day/night branding belongs in site-specific CSS, not the reusable PGL core.

## GitHub Actions

- `action.yml`: self-contained composite sync action using the current `actions/setup-python@v7` line.
- `workflows/pgl-sync.yml`: scheduled/manual state-sync example that persists generated state.
- `workflows/pgl-pages-example.yml`: Chirpy Pages reference build that syncs PGL into the checkout used for that deployment.
- `.github/workflows/ci.yml`: Python tests, local Action smoke test, plus a Chirpy `v7.6.0` / `v7.5.0` × Light / Dark build matrix.

The Pages reference does **not** persist generated history by itself because it uses `contents: read`; use the separate sync workflow when repository persistence is required. The sync reference uses `git status --porcelain` so first-run/untracked generated files are detected, rebases before pushing, and can explicitly dispatch a separate Pages workflow when repository variable `PGL_PAGES_WORKFLOW` is set (for example `pages-deploy.yml`). Do not blindly replace a working site workflow—merge the PGL step into it.

## Compatibility

`0.1.0-alpha.4` continues to target Chirpy `v7.6.0` and `v7.5.0`. The preceding alpha.3 code passed all four clean-starter GitHub Actions cells (7.6/7.5 × Light/Dark). Alpha.4 adds a scoped dynamic-title integration contract and corresponding CI checks; the exact alpha.4 matrix remains **RUN_PENDING until this package is uploaded and CI executes**. See [`COMPATIBILITY.md`](./COMPATIBILITY.md).

## Development

```bash
python -m pip install -e '.[test]'
pytest
python demo/build_demo.py
node --check jekyll/assets/pgl/pgl.js
ruby -c jekyll/_plugins/prospero_great_library.rb
```

## Design changes

Before changing category semantics, precedence, history, privacy, source responsibilities, or merge thresholds, read `PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md`.

The architecture file is the design contract; implementation convenience is not sufficient reason to break its locked decisions.

## License

MIT. Third-party services and their data remain subject to their own terms and licenses.
