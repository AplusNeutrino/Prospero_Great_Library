# Prospero_Great_Library

> Universal personal media library extension/starter kit for Jekyll, with first-class Chirpy integration.

**Release:** `0.1.0-alpha.2`  
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
| Bangumi v0 collection adapter | Implemented against official v0 schema; live call not executed in packaging environment |
| NeoDB adapter | Implemented as capability/config-driven adapter; no HTML scraping; live collection endpoint must be selected from the configured instance's Developer/OpenAPI docs |
| Steam owned/recent telemetry | Implemented against official Web API methods; live call not executed in packaging environment |
| Steam achievements | Implemented; opt-in and conservatively refreshed for recently played games with visible stats |
| Entity resolution | Implemented + fixture tested |
| Bangumi-first merge | Implemented + fixture tested |
| History / Steam observed deltas | Implemented + fixture tested |
| Blog-post association | Implemented + fixture tested |
| Jekyll UI / Chirpy adapter | Implemented; installer/resource/UI contract fixture-tested |
| Chirpy v7.6/v7.5 build matrix | CI matrix implemented for Light/Dark; **runtime pending until uploaded CI executes** |

Do not treat `alpha.2` as a claim of live production verification for every external service or Chirpy runtime combination.

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
    └── associations.json

assets/data/prospero_great_library/
├── library.json
├── stats.json
├── sync_status.json
├── manifest.json
└── history/
    └── YYYY.json
```

Source snapshots under `_data/.../sources/` are state for diff/failure recovery. If your repository itself is public, remember that repository visibility is distinct from PGL's **site-output privacy filters**.

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

`/library/` supports progressively enhanced static output:

- search;
- category/status/source/year filters;
- title/rating/update/Steam-playtime sorting;
- Grid/List toggle;
- 60-card progressive rendering with Load More;
- current in-progress shortcuts;
- modal/dialog details;
- source links with required fallback behavior;
- rating distribution and Steam ranking statistics;
- lazy-loaded yearly timeline.

If JavaScript fails, server-rendered cards remain visible.

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

The Pages reference does **not** persist generated history by itself because it uses `contents: read`; use the separate sync workflow when repository persistence is required. Do not blindly replace a working site workflow—merge the PGL step into it.

## Compatibility

`0.1.0-alpha.2` targets Chirpy `v7.6.0` and `v7.5.0`, whose theme gems both declare Jekyll `~> 4.3`. The repository contains a four-cell Light/Dark compatibility build matrix, but this packaging environment has no Bundler/Jekyll runtime; therefore the matrix is **RUN_PENDING**, not claimed as passed. See [`COMPATIBILITY.md`](./COMPATIBILITY.md).

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
