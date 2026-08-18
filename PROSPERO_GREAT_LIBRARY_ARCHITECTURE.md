# Prospero_Great_Library
## Universal Personal Media Library Extension for Jekyll / Chirpy

> **Document type:** Architecture Specification / Implementation Prompt / Design Source of Truth  
> **Project name:** `Prospero_Great_Library`  
> **Short name:** `PGL`  
> **Design version:** `0.1.0-design`  
> **Date:** 2026-08-18  
> **License target:** MIT  
> **V1 official theme support:** Jekyll + Chirpy  
> **Core design target:** Theme-independent Jekyll data/sync core  
> **Status:** Authoritative pre-implementation design contract

---

# 0. How this document must be used

This file is the **authoritative design source of truth** for `Prospero_Great_Library`.

Whenever a future developer, maintainer, contributor, coding agent, or AI assistant works on this project, it MUST:

1. Read this file before making architectural changes.
2. Treat sections marked **LOCKED** as product decisions, not suggestions.
3. Verify current external API details against the official upstream documentation before implementing or modifying adapters.
4. Prefer changing adapter implementations over changing the canonical PGL schema.
5. Preserve backward compatibility of generated data wherever practical.
6. Never silently change source precedence, category rules, history semantics, privacy behavior, or entity-resolution thresholds.
7. If implementation evidence proves that a locked design is impossible or materially harmful, document the conflict first and update this file in the same change that modifies the design.
8. Distinguish:
   - product/design decisions;
   - current implementation state;
   - current external API behavior.
9. Never treat a third-party API detail observed at one point in time as a permanent architectural guarantee.
10. Keep the project usable without any runtime backend after Jekyll has built the site.

This document is deliberately more detailed than a normal README. Its purpose is to prevent design drift when project context is incomplete.

---

# 1. Project vision

`Prospero_Great_Library` is an open-source **Universal Personal Media Library extension / starter kit** for Jekyll blogs.

Its first-class target is the Chirpy Jekyll theme, but the data, synchronization, normalization, history, and entity-resolution layers must not depend on Chirpy.

The intended user experience is:

```text
Bangumi ───────┐
               │
NeoDB ─────────┼──> PGL Sync / Normalize / Merge ──> Canonical Library
               │                                      │
Steam ─────────┘                                      ├──> Jekyll/Liquid
                                                      ├──> Static JSON
                                                      └──> Vanilla JS UI
```

A blog owner should be able to expose a unified `/library/` page containing books, comics, films, drama, anime, games, and music without building a backend service.

PGL is not intended to replace Bangumi, NeoDB, or Steam. Those services remain the systems where users maintain their media records. PGL acts as a **read-oriented aggregation, normalization, presentation, and history layer**.

The user's own blog is only one consumer of PGL. Personal site-specific visual styling must be implemented as a theme override on top of PGL rather than embedded into the public PGL core.

---

# 2. Core principles

## 2.1 Static-first

**LOCKED**

After synchronization/build completes:

- the browser MUST NOT need Bangumi, NeoDB, or Steam credentials;
- the browser SHOULD NOT directly call those external APIs;
- all secrets remain in GitHub Actions or local environment variables;
- the generated blog remains a static site;
- no database server, serverless backend, long-running process, Docker service, or application server is required for ordinary deployment.

Client-side JavaScript may perform:

- filtering;
- sorting;
- searching;
- drawer/modal behavior;
- pagination/lazy rendering;
- statistics visualization;
- timeline rendering.

It should operate only on locally generated PGL data.

---

## 2.2 Adapter isolation

External services are volatile. PGL must treat them as replaceable adapters.

```text
External API
    ↓
Source Adapter
    ↓
Source Record
    ↓
Normalizer
    ↓
Canonical Entity
```

A source API change must normally require changes only inside that source adapter and its tests.

The front-end must not contain service-specific parsing logic.

---

## 2.3 Canonical schema stability

PGL should keep one stable internal schema even if:

- Bangumi adds fields;
- NeoDB changes its OpenAPI;
- Steam changes API responses;
- metadata sources disagree;
- a new media source is added later.

Raw source payloads may be cached separately, but UI and Jekyll integration must consume canonical PGL records.

---

## 2.4 Bangumi-first semantics

**LOCKED**

Whenever Bangumi and NeoDB both provide the same logical information for the same canonical entity, **Bangumi is the default first source of truth**.

General precedence:

```text
Bangumi > NeoDB
```

This applies to:

- category evidence when Bangumi provides trustworthy type information;
- status;
- rating;
- title;
- alternate title;
- cover;
- summary/description;
- release year/date;
- general metadata.

NeoDB fills missing Bangumi fields.

This precedence must be configurable so that users may switch it, but the shipped/default PGL configuration is Bangumi-first.

Steam is different: Steam has dedicated game telemetry fields that do not compete with Bangumi status/rating.

---

## 2.5 No destructive merging

If two sources disagree, the canonical selected value may follow precedence, but source-specific values should still be retained under `sources`.

Example:

```json
{
  "rating": {
    "value": 9,
    "scale": 10,
    "normalized_10": 9.0,
    "source": "bangumi"
  },
  "sources": {
    "bangumi": {
      "rating": {
        "value": 9,
        "scale": 10
      }
    },
    "neodb": {
      "rating": {
        "value": 4.5,
        "scale": 5
      }
    }
  }
}
```

This allows future precedence changes without refetching or losing provenance.

---

# 3. Supported media taxonomy

## 3.1 Top-level categories

**LOCKED**

PGL V1 exposes exactly these seven primary categories:

```text
Book
Comic
Movie
Drama
Anime
Game
Music
```

Canonical machine values:

```text
book
comic
movie
drama
anime
game
music
```

A canonical item belongs to **exactly one** primary category.

No item may appear in multiple primary categories merely because multiple source services classify it differently.

---

## 3.2 Book and Comic are mutually exclusive

**LOCKED**

`Book` and `Comic` MUST NOT overlap.

- novels;
- nonfiction;
- essays;
- academic books;
- conventional prose publications;

belong to `book`.

- manga;
- manhua;
- manhwa;
- comics;
- graphic novels when confidently identified as comic-format media;

belong to `comic`.

Bangumi classification evidence takes priority over NeoDB when both are present.

NeoDB `Book` records may ultimately resolve to either `book` or `comic`.

---

## 3.3 Anime

**LOCKED**

`anime` includes:

- anime television series;
- anime web series;
- anime OVA/OAD where represented as an entity;
- anime films.

An anime movie is **Anime only**.

It MUST NOT also appear under Movie.

NeoDB movie/TV records determined to be animation may therefore be canonicalized into `anime`.

---

## 3.4 Movie

**LOCKED**

`movie` contains:

- live-action films;
- films not canonicalized as anime;
- Performance records representing opera, stage play, or musical.

There is **no secondary hierarchy** such as:

```text
Movie
└── Opera
```

Instead, performance works carry an optional tag:

```text
performance
```

A normal movie does not receive a `movie` tag merely for being a movie.

Examples:

```text
Oppenheimer
category = movie
tags = [...]

Hamlet stage production
category = movie
tags = [..., performance]

La Traviata performance
category = movie
tags = [..., performance]
```

The public UI may render `Performance` / `舞台` as a small badge when the tag exists.

The internal schema SHOULD allow richer source-specific performance metadata, but the top-level taxonomy remains flat.

---

## 3.5 Drama

**LOCKED**

`drama` means live-action episodic series / television drama.

Examples:

- live-action TV drama;
- live-action streaming series;
- miniseries;
- other serialized live-action screen works.

Anime series MUST NOT be placed here.

---

## 3.6 Game

**LOCKED**

`game` includes video games and related playable software represented by Bangumi and/or Steam.

Bangumi controls subjective collection semantics.

Steam enriches game telemetry.

---

## 3.7 Music

**LOCKED**

`music` contains music releases/items represented by supported source services.

Bangumi remains first source by default; NeoDB fills missing data.

---

# 4. Deterministic category classifier

## 4.1 Rule-based, not numeric-priority-only

**LOCKED**

PGL must implement category assignment as an explicit rule tree.

It must not rely on a single global integer priority that could create nonsensical cross-type conflicts.

Conceptually:

```python
if trusted_game_evidence:
    return GAME

if trusted_anime_evidence:
    return ANIME

if trusted_comic_evidence:
    return COMIC

if trusted_live_action_series_evidence:
    return DRAMA

if trusted_performance_evidence:
    return MOVIE with "performance" tag

if trusted_movie_evidence:
    return MOVIE

if trusted_book_evidence:
    return BOOK

if trusted_music_evidence:
    return MUSIC
```

The actual implementation must account for source authority.

---

## 4.2 Bangumi evidence

Bangumi subject types/categories and trustworthy item metadata should be used first when present.

Expected conceptual mapping:

```text
Bangumi Anime  -> anime
Bangumi Game   -> game
Bangumi Music  -> music

Bangumi Book
  ├── comic/manga category evidence -> comic
  └── otherwise                     -> book

Bangumi Real
  ├── live-action episodic evidence -> drama
  ├── performance evidence          -> movie + performance tag
  └── film evidence                 -> movie
```

Implementation must use the current official Bangumi schema rather than hardcoding assumptions from this document.

---

## 4.3 NeoDB evidence

Expected conceptual mapping:

```text
NeoDB Book
  ├── strong comic evidence -> comic
  └── otherwise             -> book

NeoDB Movie
  ├── strong animation evidence -> anime
  └── otherwise                 -> movie

NeoDB TV
  ├── strong animation evidence -> anime
  └── otherwise                 -> drama

NeoDB Performance
  -> movie + performance tag

NeoDB Game
  -> game

NeoDB Music
  -> music
```

---

## 4.4 Anime-film rule

If:

```text
NeoDB = Movie
Bangumi = Anime
```

canonical result MUST be:

```text
category = anime
```

not Movie.

---

## 4.5 Comic rule

If:

```text
NeoDB = Book
Bangumi = Comic/Manga
```

canonical result MUST be:

```text
category = comic
```

not Book.

---

## 4.6 Classification uncertainty

If PGL cannot determine a specialized category confidently:

- do not invent evidence;
- prefer the least destructive source-native fallback;
- record a diagnostic;
- permit a user override in mappings/config;
- do not create a duplicate item in another category.

For example, a NeoDB-only `Book` with weak comic-like signals should remain `book` until stronger evidence exists.

---

# 5. Source matrix

## 5.1 Default source support

**LOCKED**

```text
Book   = Bangumi + NeoDB
Comic  = Bangumi + NeoDB
Movie  = Bangumi + NeoDB
Drama  = Bangumi + NeoDB
Anime  = Bangumi + NeoDB
Game   = Bangumi + Steam (+ NeoDB optional enrichment if enabled later)
Music  = Bangumi + NeoDB
```

V1's required core source adapters:

```text
Bangumi
NeoDB
Steam
```

All adapters are optional at installation time.

Supported configurations include:

```text
Bangumi only
NeoDB only
Steam only
Bangumi + NeoDB
Bangumi + Steam
NeoDB + Steam
Bangumi + NeoDB + Steam
```

The system must remain functional with any enabled subset, within the limitations of the available source data.

---

## 5.2 Default precedence matrix

**LOCKED**

Default precedence is Bangumi-first wherever Bangumi competes with NeoDB.

```yaml
book:
  metadata: [bangumi, neodb]
  status: [bangumi, neodb]
  rating: [bangumi, neodb]

comic:
  metadata: [bangumi, neodb]
  status: [bangumi, neodb]
  rating: [bangumi, neodb]

movie:
  metadata: [bangumi, neodb]
  status: [bangumi, neodb]
  rating: [bangumi, neodb]

drama:
  metadata: [bangumi, neodb]
  status: [bangumi, neodb]
  rating: [bangumi, neodb]

anime:
  metadata: [bangumi, neodb]
  status: [bangumi, neodb]
  rating: [bangumi, neodb]

music:
  metadata: [bangumi, neodb]
  status: [bangumi, neodb]
  rating: [bangumi, neodb]
```

For Game:

```yaml
game:
  metadata: [bangumi, steam]
  status: [bangumi]
  rating: [bangumi]
  telemetry:
    playtime: steam
    recent_playtime: steam
    achievements: steam
    last_played: steam
    owned: steam
```

Users may change precedence in `_config.yml`.

A configuration switch must not require code changes.

---

# 6. Universal status model

## 6.1 Canonical statuses

**LOCKED**

Every item may have one canonical user status:

```text
wishlist
in_progress
completed
on_hold
dropped
```

Optional:

```text
null
```

when no compatible source has a user collection state.

---

## 6.2 Adapter mapping responsibility

Adapters convert native states into canonical states.

Example conceptual mapping:

```text
Bangumi "want"      -> wishlist
Bangumi "doing"     -> in_progress
Bangumi "collect"   -> completed
Bangumi "on hold"   -> on_hold
Bangumi "dropped"   -> dropped

NeoDB wishlist      -> wishlist
NeoDB in progress   -> in_progress
NeoDB complete      -> completed
NeoDB dropped       -> dropped
```

Exact upstream enum values MUST be read from current official API specifications at implementation time.

Steam MUST NOT infer:

```text
completed
```

from playtime or achievement percentage.

Owning or playing a game is not equivalent to completing it.

---

# 7. Rating model

## 7.1 Preserve native rating and normalize

**LOCKED**

Canonical rating:

```json
{
  "value": 9,
  "scale": 10,
  "normalized_10": 9.0,
  "source": "bangumi"
}
```

Source-specific ratings remain preserved:

```json
{
  "sources": {
    "bangumi": {
      "rating": {
        "value": 9,
        "scale": 10
      }
    },
    "neodb": {
      "rating": {
        "value": 4.5,
        "scale": 5
      }
    }
  }
}
```

Normalization rule:

```text
normalized_10 = value / scale * 10
```

Do not round away meaningful source precision in stored data.

The UI may display a rounded value separately.

---

# 8. Canonical entity schema

## 8.1 Schema goals

The canonical schema must:

- preserve source provenance;
- support static rendering;
- support future adapters;
- avoid source-specific field names in UI;
- preserve enough identifiers for entity resolution;
- support history diffing;
- support article associations;
- remain JSON-serializable.

---

## 8.2 Recommended canonical record

```json
{
  "id": "game:7f5f74c5",
  "schema_version": 1,

  "category": "game",
  "tags": [],

  "title": "FINAL FANTASY",
  "title_original": "ファイナルファンタジー",
  "alternate_titles": [
    "Final Fantasy I"
  ],

  "year": 1987,
  "release_date": "1987-12-18",

  "cover": {
    "url": "https://...",
    "source": "bangumi",
    "cached": false
  },

  "summary": "...",

  "status": "completed",

  "rating": {
    "value": 8,
    "scale": 10,
    "normalized_10": 8.0,
    "source": "bangumi"
  },

  "progress": {
    "current": null,
    "total": null,
    "unit": null,
    "percent": null,
    "source": null
  },

  "telemetry": {
    "steam": {
      "owned": true,
      "playtime_minutes": 2556,
      "recent_playtime_minutes": 120,
      "last_played_at": "2026-08-17T10:00:00Z",
      "achievements": {
        "unlocked": 18,
        "total": 24,
        "percent": 75.0
      }
    }
  },

  "links": {
    "primary": "https://bgm.tv/subject/...",
    "bangumi": "https://bgm.tv/subject/...",
    "neodb": null,
    "steam": "https://store.steampowered.com/app/..."
  },

  "identifiers": {
    "isbn10": null,
    "isbn13": null,
    "bangumi_subject_id": 123,
    "neodb_item_id": null,
    "steam_appid": 39140
  },

  "sources": {
    "bangumi": {
      "present": true,
      "id": "123",
      "url": "https://bgm.tv/subject/123",
      "status": "completed",
      "rating": {
        "value": 8,
        "scale": 10
      },
      "updated_at": "..."
    },
    "neodb": {
      "present": false
    },
    "steam": {
      "present": true,
      "appid": 39140,
      "updated_at": "..."
    }
  },

  "articles": [
    {
      "url": "/posts/ff1-record/",
      "title": "游戏记录：Final Fantasy 1",
      "match_method": "title_alias",
      "confidence": 0.98
    }
  ],

  "privacy": {
    "hidden": false,
    "hide_sources": [],
    "stats_only": false
  },

  "timestamps": {
    "first_seen_at": "2026-08-18T00:00:00Z",
    "last_seen_at": "2026-08-18T00:00:00Z",
    "canonical_updated_at": "2026-08-18T00:00:00Z"
  }
}
```

---

## 8.3 Stable canonical IDs

PGL IDs must not be based solely on mutable titles.

Preferred strategy:

1. If an explicit mapping already exists, reuse its canonical ID.
2. Reuse the canonical ID from the prior library snapshot when any source identifier matches.
3. For first creation, generate a stable opaque suffix, e.g. UUID/short hash, namespaced by category.

Example:

```text
book:8e6028ba
anime:a21d5f13
game:7f5f74c5
```

Never regenerate IDs because a title changes.

---

# 9. Entity resolution

## 9.1 Objective

Entity resolution determines whether records from different sources represent the same real-world work.

Example:

```text
Bangumi: FINAL FANTASY
Steam:   FINAL FANTASY
```

should become one canonical game.

---

## 9.2 Resolution order

**LOCKED**

PGL should use the most automatic safe approach:

```text
1. Explicit mapping
2. Exact durable identifier
3. Known external-source cross-link
4. ISBN / ISBN13 for books
5. Exact normalized title + compatible category + year
6. Alias title + compatible category + year
7. High-confidence fuzzy match
8. Ambiguous => do not auto-merge
```

---

## 9.3 Explicit mappings

File:

```text
_data/prospero_great_library/mappings.yml
```

Example:

```yaml
entities:
  - id: game:7f5f74c5
    bangumi: 12345
    steam: 39140

  - id: book:2f93a601
    bangumi: 54321
    neodb: "abcXYZ"
```

Manual mapping is an escape hatch, not the normal workflow.

The system should require minimal manual mapping.

---

## 9.4 Normalization

Title normalization should include:

- Unicode NFKC normalization;
- lowercase where applicable;
- trimming;
- repeated whitespace collapse;
- punctuation normalization;
- full-width/half-width normalization;
- safe removal of edition markers only when explicitly modeled;
- preservation of CJK title semantics;
- alias matching.

Do not transliterate CJK titles into Latin as the sole matching method.

---

## 9.5 Confidence policy

Recommended V1 thresholds:

```text
>= 0.95  automatic merge allowed
0.80–0.9499  suggestion/review only
< 0.80   no merge suggestion
```

A deterministic exact identifier match is effectively confidence `1.0`.

Fuzzy matching must never merge entities solely because titles are vaguely similar.

Category compatibility is required.

---

## 9.6 Ambiguity reporting

Generate:

```text
_data/prospero_great_library/diagnostics/entity_resolution.json
```

Example:

```json
{
  "ambiguous": [
    {
      "source": "steam",
      "source_id": "39140",
      "candidates": [
        {
          "canonical_id": "game:...",
          "confidence": 0.87
        }
      ]
    }
  ]
}
```

Ambiguous items remain separate until resolved.

False merges are more harmful than temporary duplicates.

---

# 10. Source adapter contract

Every adapter must implement conceptually equivalent operations.

Python protocol shape:

```python
class SourceAdapter(Protocol):
    name: str

    def validate_config(self) -> list[Diagnostic]:
        ...

    def healthcheck(self) -> SourceHealth:
        ...

    def fetch_collections(self) -> list[SourceRecord]:
        ...

    def fetch_details(self, records: list[SourceRecord]) -> list[SourceRecord]:
        ...

    def normalize(self, raw: SourceRecord) -> NormalizedSourceRecord:
        ...
```

Optional:

```python
def fetch_telemetry(...)
def fetch_achievements(...)
def search_candidates(...)
def resolve_external_links(...)
```

Adapters must return normalized source records, not write canonical library items themselves.

Canonical merge logic belongs to the core.

---

# 11. Bangumi adapter

## 11.1 Role

Bangumi is the default primary source.

It is responsible for:

- collection status;
- user rating;
- user comment/review where exposed and appropriate;
- subject metadata;
- classification evidence;
- anime progress/episode context where practical;
- game subjective state;
- book/comic distinction evidence;
- metadata fallback search for NeoDB-only items when useful.

---

## 11.2 Authentication

Expected secret:

```text
BANGUMI_ACCESS_TOKEN
```

Expected public configuration:

```yaml
sources:
  bangumi:
    enabled: true
    username: "..."
```

The browser must never receive the token.

---

## 11.3 Current official API baseline

As of 2026-08-18, the official Bangumi v0 API exposes endpoints including:

```text
GET  /v0/users/{username}
GET  /v0/users/{username}/collections
GET  /v0/users/{username}/collections/{subject_id}
GET  /v0/subjects/{subject_id}
POST /v0/search/subjects
GET  /v0/episodes
```

Implementation must re-check:

```text
https://bangumi.github.io/api/
```

before coding or modifying the adapter.

Do not assume undocumented fields remain stable.

---

# 12. NeoDB adapter

## 12.1 Role

NeoDB is the secondary universal cultural-media source.

It fills Bangumi gaps and provides records for:

- books;
- movies;
- TV/drama;
- music;
- games;
- performances;
- user collection status/rating when Bangumi is absent.

NeoDB records may be reclassified by PGL's canonical classifier.

---

## 12.2 Public and authenticated modes

**LOCKED**

PGL supports:

```text
public
authenticated
```

Default:

```text
public
```

Configuration:

```yaml
sources:
  neodb:
    enabled: true
    instance: "https://neodb.social"
    mode: "public"
    username: "..."
```

Optional secret:

```text
NEODB_ACCESS_TOKEN
```

---

## 12.3 Critical implementation rule for public mode

PGL MUST NOT silently fall back to brittle HTML scraping simply to preserve "public mode".

NeoDB is federated and instance behavior/API versions can differ.

At implementation time:

1. probe the configured instance;
2. consult its current OpenAPI/developer interface;
3. use documented public API / federation endpoints where available;
4. if public personal-collection retrieval is unavailable without authentication, report a clear capability warning;
5. optionally allow a read-only authenticated token while keeping the data visibility semantics "public";
6. never send token credentials to the browser.

"Public mode" means the user intends to expose/read only public collection data. It does not guarantee that every NeoDB instance exposes every personal collection endpoint anonymously.

---

## 12.4 OAuth

NeoDB officially supports OAuth access tokens.

If authenticated mode is used, credentials must be stored only as repository/environment secrets.

At implementation time verify:

```text
https://neodb.net/api/
https://<instance>/developer/
```

NeoDB's API is instance-version-sensitive. Endpoint paths must be encapsulated in the adapter.

---

# 13. Steam adapter

## 13.1 Role

Steam is a Game-only telemetry source.

It supplies:

- owned status;
- lifetime playtime;
- recent playtime where available;
- last played where available;
- game metadata fallback;
- achievements;
- achievement totals/percentage.

Steam does NOT determine PGL subjective completion status.

---

## 13.2 Configuration

Public:

```yaml
sources:
  steam:
    enabled: true
    steam_id: "7656..."
```

Secret:

```text
STEAM_API_KEY
```

---

## 13.3 Official API baseline

As of 2026-08-18, relevant official methods include:

```text
IPlayerService/GetOwnedGames
IPlayerService/GetRecentlyPlayedGames
ISteamUserStats/GetPlayerAchievements
ISteamUserStats/GetSchemaForGame
```

Implementation must verify current official documentation:

```text
https://partner.steamgames.com/doc/webapi/IPlayerService
https://partner.steamgames.com/doc/webapi/ISteamUserStats
```

Owned-game details depend on Steam privacy visibility.

---

## 13.4 Achievement fetching strategy

Do not call achievement endpoints indiscriminately for every game on every sync.

Recommended strategy:

1. fetch owned games;
2. identify games represented in canonical library;
3. fetch achievements only if UI/config enables them;
4. cache achievement schemas;
5. refresh player achievement status on a slower cadence or only for recently played games;
6. obey errors/privacy restrictions without breaking the full sync.

---

# 14. Primary external link behavior

## 14.1 Locked defaults

Card click / primary external link:

```text
Anime -> Bangumi
Game  -> Bangumi

Book  -> NeoDB
Comic -> NeoDB
Movie -> NeoDB
Drama -> NeoDB
Music -> NeoDB
```

---

## 14.2 Fallback

**LOCKED**

If the preferred target is unavailable:

```text
preferred source exists
    -> preferred URL

preferred source missing
    -> another available source URL

no external source URL
    -> no broken link; disable external-link action
```

Example:

```text
Comic:
NeoDB missing
Bangumi present

=> click Bangumi
```

Source badges may still expose each available source separately.

---

# 15. History model

## 15.1 V1 includes history

**LOCKED**

History/Event Log is a V1 feature.

PGL must support:

- timeline;
- status changes;
- rating changes;
- progress changes;
- category changes when improved classification evidence appears;
- source linking/unlinking;
- Steam playtime increments;
- achievement changes;
- completion observations;
- first-seen events.

History begins when PGL starts tracking unless an upstream source provides trustworthy historical dates.

PGL must never fabricate historical events predating available evidence.

---

## 15.2 Do not archive full daily snapshots forever

Recommended design:

- keep current source snapshots for diffing;
- generate append-only compact events;
- partition event history by year;
- avoid storing a complete raw copy of every source response every day.

This minimizes repository growth.

---

## 15.3 Storage layout

Recommended:

```text
_data/
└── prospero_great_library/
    ├── library.json
    ├── stats.json
    ├── sync_status.json
    ├── associations.json
    ├── mappings.yml
    │
    ├── sources/
    │   ├── bangumi.json
    │   ├── neodb.json
    │   └── steam.json
    │
    └── diagnostics/
        ├── entity_resolution.json
        └── associations.json

assets/
└── data/
    └── prospero_great_library/
        ├── manifest.json
        └── history/
            ├── 2026.json
            ├── 2027.json
            └── ...
```

Rationale:

- current canonical data is available to Jekyll through `_data`;
- large append-only historical arrays do not need to inflate `site.data`;
- history is fetched as local static JSON by the Library UI.

---

## 15.4 Event schema

Example:

```json
{
  "id": "evt_...",
  "observed_at": "2026-08-18T01:23:45Z",
  "local_date": "2026-08-18",
  "entity_id": "game:7f5f74c5",
  "category": "game",
  "event": "steam_playtime_delta",
  "source": "steam",
  "data": {
    "from_minutes": 2400,
    "to_minutes": 2556,
    "delta_minutes": 156
  }
}
```

Other event names:

```text
entity_first_seen
status_changed
rating_changed
progress_changed
steam_playtime_delta
steam_achievement_unlocked
category_changed
source_attached
source_detached
metadata_major_change
```

Do not create timeline noise for trivial non-user-facing metadata changes unless configured.

---

## 15.5 Steam playtime semantics

Steam's lifetime playtime is a cumulative observation.

PGL calculates:

```text
delta = current_lifetime_minutes - previous_lifetime_minutes
```

if positive.

This represents:

> playtime increase observed between two successful syncs

It does NOT necessarily prove the exact minute/date on which the play occurred.

UI language should avoid implying exact per-day telemetry unless upstream data genuinely supports it.

---

## 15.6 Negative Steam deltas

If lifetime playtime decreases:

- do not treat it as negative gameplay;
- emit a diagnostic/correction event;
- reset the baseline to the newest trustworthy value;
- do not subtract hours from yearly "played" statistics unless an explicit correction algorithm is enabled and documented.

---

## 15.7 Yearly Steam statistics

PGL may calculate:

```text
Observed Steam playtime gained during 2026
```

by summing positive `steam_playtime_delta` events whose observation date belongs to that year.

Because syncs are periodic, this is an observed-period approximation around year boundaries.

The UI/docs should be transparent about that semantic.

---

# 16. Statistics

V1 may expose:

```text
Total canonical items
Items by category
Items by status
Rating distribution
Current in-progress items
Completed items by observed/completion year where supported
Steam lifetime playtime total
Steam lifetime playtime ranking
Observed Steam playtime gained by year
Achievement totals
Timeline event counts
```

Statistics should be precomputed at sync/build time when possible so the browser does not repeatedly aggregate very large datasets.

Generated:

```text
_data/prospero_great_library/stats.json
```

---

# 17. Synchronization pipeline

## 17.1 Standard pipeline

```text
1. Load configuration
2. Validate enabled adapters
3. Load previous successful source snapshots
4. Fetch Bangumi
5. Fetch NeoDB
6. Fetch Steam
7. Normalize source records
8. Classify media
9. Resolve cross-source entities
10. Apply source precedence
11. Build canonical library
12. Diff against previous canonical/source state
13. Append history events
14. Scan blog posts and resolve article associations
15. Compute statistics
16. Apply privacy filters
17. Validate schemas/invariants
18. Write generated files atomically
19. Write sync_status.json
20. Optionally persist generated data to repository
21. Jekyll build
22. GitHub Pages deploy
```

---

## 17.2 Default cadence

**LOCKED**

Recommended default:

```text
manual workflow_dispatch
+
daily scheduled sync
+
optional sync before normal blog deploy
```

No requirement for hourly synchronization.

---

## 17.3 Timezone

Config:

```yaml
sync:
  timezone: "Asia/Shanghai"
```

History should store:

```text
observed_at = UTC ISO 8601
local_date  = derived configured timezone date
```

This avoids ambiguous yearly/monthly statistics.

---

# 18. Failure behavior

## 18.1 Non-fatal source failure

**LOCKED**

If one source fails:

```text
Bangumi failed
NeoDB succeeded
Steam succeeded
```

PGL must:

- preserve the last known good Bangumi snapshot;
- use fresh NeoDB and Steam data;
- never replace Bangumi data with an empty set because of a failed request;
- record a warning;
- mark freshness/staleness in `sync_status.json`;
- continue the build if the canonical output remains valid.

There is no user-facing `strict mode` in V1.

---

## 18.2 Atomic writes

Generated files should be written:

```text
temporary file -> schema validation -> atomic rename
```

Do not partially overwrite the last good dataset.

---

## 18.3 Source status schema

Example:

```json
{
  "last_run": "2026-08-18T01:00:00Z",
  "overall": "degraded",
  "sources": {
    "bangumi": {
      "status": "stale",
      "last_success": "2026-08-17T01:00:00Z",
      "error": "HTTP 503"
    },
    "neodb": {
      "status": "ok",
      "last_success": "2026-08-18T01:00:05Z"
    },
    "steam": {
      "status": "ok",
      "last_success": "2026-08-18T01:00:08Z"
    }
  }
}
```

---

# 19. API caching and rate-limit strategy

PGL must implement conservative request behavior.

Required principles:

- paginate rather than request pathological page sizes;
- retry transient failures with exponential backoff + jitter;
- respect HTTP 429 and `Retry-After` when provided;
- cache source detail records;
- avoid refetching static metadata unnecessarily;
- fetch volatile user state more often than static metadata;
- cap concurrent requests;
- provide source-specific request budgets;
- avoid scanning every Bangumi/Steam/NeoDB item globally.

Suggested cache classes:

```text
user collection state: short-lived
subject metadata: medium/long-lived
Steam achievement schema: long-lived
Steam player achievement state: medium-lived
cover metadata: long-lived
```

Do not hardcode undocumented provider rate limits as facts.

---

# 20. Repository architecture

Recommended upstream PGL repository:

```text
Prospero_Great_Library/
├── README.md
├── LICENSE
├── PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md
├── CHANGELOG.md
├── pyproject.toml
├── action.yml
│
├── pgl/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── schema.py
│   ├── models.py
│   ├── diagnostics.py
│   │
│   ├── adapters/
│   │   ├── base.py
│   │   ├── bangumi.py
│   │   ├── neodb.py
│   │   └── steam.py
│   │
│   ├── normalize/
│   │   ├── titles.py
│   │   ├── ratings.py
│   │   ├── statuses.py
│   │   └── categories.py
│   │
│   ├── resolve/
│   │   ├── entities.py
│   │   ├── confidence.py
│   │   └── mappings.py
│   │
│   ├── history/
│   │   ├── diff.py
│   │   ├── events.py
│   │   └── stats.py
│   │
│   ├── associations/
│   │   ├── posts.py
│   │   ├── exact.py
│   │   └── fuzzy.py
│   │
│   ├── privacy/
│   │   └── filters.py
│   │
│   └── output/
│       ├── jekyll.py
│       └── json_writer.py
│
├── jekyll/
│   ├── _plugins/
│   │   └── prospero_great_library.rb
│   │
│   ├── _includes/
│   │   └── pgl/
│   │       ├── library.html
│   │       ├── card.html
│   │       ├── drawer.html
│   │       ├── filters.html
│   │       ├── stats.html
│   │       └── post-card.html
│   │
│   ├── assets/
│   │   └── pgl/
│   │       ├── pgl.css
│   │       ├── pgl.js
│   │       └── components/
│   │
│   └── locales/
│       ├── en.yml
│       └── zh-CN.yml
│
├── adapters/
│   └── chirpy/
│       ├── install.py
│       ├── library-page.md
│       ├── integration/
│       └── pgl-chirpy.css
│
├── workflows/
│   ├── pgl-sync.yml
│   └── pgl-pages-example.yml
│
├── demo/
│   ├── fixtures/
│   └── site/
│
└── tests/
    ├── fixtures/
    ├── adapters/
    ├── resolution/
    ├── history/
    ├── associations/
    └── jekyll/
```

---

# 21. Language/tool boundaries

## 21.1 Python

**LOCKED preference: code ecosystem first**

Python owns:

- API communication;
- parsing;
- normalization;
- canonical schema generation;
- entity resolution;
- history diff;
- statistics;
- post association analysis;
- diagnostics;
- CLI.

Recommended minimum version should be selected at first implementation based on GitHub Actions support, preferably a currently maintained Python version.

---

## 21.2 Ruby/Jekyll

Ruby owns only Jekyll integration that genuinely benefits from Jekyll lifecycle access.

Examples:

- custom Liquid tags/filters;
- exposing helper functions;
- optional render hooks;
- safe integration glue.

Do not duplicate Python's API/client logic in Ruby.

---

## 21.3 Vanilla JavaScript

Front-end uses Vanilla JS.

V1 must not require React/Vue.

Web Components may be used where they reduce coupling, but must remain optional and lightweight.

The user must not need a Node front-end build pipeline merely to use PGL.

---

## 21.4 GitHub Actions

Actions orchestrate:

- Python environment;
- sync;
- generated data persistence;
- Jekyll build;
- GitHub Pages deployment.

Custom GitHub Actions Pages deployment is a supported/expected installation path.

---

# 22. Jekyll integration

## 22.1 Universal core

The Jekyll integration must not assume Chirpy-specific DOM for the core data API.

Core Liquid access concept:

```liquid
site.data.prospero_great_library.library
site.data.prospero_great_library.stats
site.data.prospero_great_library.sync_status
site.data.prospero_great_library.associations
```

---

## 22.2 Library page

Default URL:

```text
/library/
```

Single main page.

Query parameters may select views:

```text
/library/?type=game
/library/?type=book&status=in_progress
/library/?sort=rating
```

Do not require separate generated URLs for every category in V1.

---

## 22.3 Graceful no-JS behavior

The initial page should render useful content with Jekyll/Liquid.

JavaScript enhances:

- filters;
- sorting;
- searching;
- drawer;
- pagination/lazy rendering;
- timeline/statistics interactions.

If JS fails, the page should not become completely empty.

---

# 23. Chirpy adapter

## 23.1 Compatibility target

**LOCKED policy**

V1 officially supports the **two most recent tested Chirpy release lines** at the time of each PGL release.

Do not promise universal compatibility with every historical Chirpy version.

Maintain a compatibility matrix in README/release notes:

```text
PGL version | Chirpy tested versions | Jekyll tested versions
```

---

## 23.2 Chirpy-specific responsibilities

The adapter may provide:

- `/library/` page starter;
- spacing/layout alignment;
- light/dark variable inheritance;
- post-card insertion integration;
- Chirpy navigation/tab examples;
- responsive breakpoints compatible with Chirpy;
- CSS selectors isolated from PGL core.

Do not fork the full Chirpy theme.

---

## 23.3 Upstream change resilience

Chirpy supports custom styles and GitHub Actions-based deployment.

PGL should minimize layout overrides because full layout copies increase upgrade conflicts.

Prefer:

```text
include
small hook
CSS variables
isolated JS
```

over replacing `_layouts/default.html` or `_layouts/post.html`.

---

# 24. UI specification

## 24.1 Main controls

V1 UI supports:

- category filtering;
- status filtering;
- source filtering;
- title search;
- year filtering;
- rating sorting;
- updated-time sorting;
- Steam playtime sorting;
- Grid/List toggle;
- pagination and/or lazy rendering;
- current in-progress section;
- yearly statistics;
- rating distribution;
- Steam playtime statistics;
- timeline.

---

## 24.2 Category tabs

Suggested:

```text
All | Book | Comic | Movie | Drama | Anime | Game | Music
```

Localization controls labels.

Machine values remain English slugs.

---

## 24.3 Card fields

Default card may show:

```text
Cover
Title
Alternate title
Year
Category
Performance badge when applicable
Status
Rating
Progress
Source badges
Steam lifetime playtime for Game
Article link indicator
```

Avoid showing every possible source field directly on the card.

---

## 24.4 Drawer/modal

Clicking a card opens a Drawer/Modal first when detail presentation is enabled.

Drawer can show:

- larger cover;
- canonical metadata;
- source badges/links;
- source-specific ratings;
- user status;
- progress;
- Steam playtime;
- achievements summary;
- related blog posts;
- timeline excerpt.

The primary external action follows the source-link rules in section 14.

No individual static detail page is generated in V1.

---

# 25. Article association

## 25.1 Requirement

**LOCKED**

PGL must support bidirectional conceptual association:

```text
Library item -> related blog posts
Blog post    -> related library item
```

This is a key feature.

---

## 25.2 Level 1: exact automatic association

Scan post front matter and Markdown for:

```text
canonical PGL ID
Bangumi subject URL
NeoDB item URL
Steam store URL/AppID
ISBN/ISBN13
```

Exact durable identifier matches bind automatically.

Recommended front matter escape hatch:

```yaml
library:
  id: game:7f5f74c5
```

The user should not need this for posts that already contain a recognizable exact source identifier.

---

## 25.3 Level 2: high-confidence automatic association

Use:

- normalized post title;
- category/title prefixes;
- post tags;
- entity alternate titles;
- year;
- known aliases.

Example:

```text
Post:
游戏记录：Final Fantasy 1

Entity aliases:
FINAL FANTASY
Final Fantasy I

=> confidence >= 0.95
=> automatic association
```

---

## 25.4 Level 3: ambiguous suggestions

If confidence is below automatic threshold but above suggestion threshold:

```text
0.80 <= confidence < 0.95
```

do not auto-bind.

Generate a diagnostic.

Example:

```text
Possible association:
_posts/2025-08-22-FF1记录.md

Candidate:
game:7f5f74c5 FINAL FANTASY

confidence: 0.86
```

User may add front matter or mapping.

---

## 25.5 Never rewrite posts automatically

PGL should not silently edit users' Markdown/front matter to insert IDs.

Automatic associations are stored in generated association data.

Manual front matter is optional stabilization.

This reduces surprising repository mutations.

---

## 25.6 Post-side display strategy

Preferred architecture:

1. generated `associations.json` maps post URLs to entity IDs;
2. Chirpy adapter provides one small integration hook/include;
3. matching posts receive an automatic PGL mini-card;
4. users can disable post-side display independently.

Avoid requiring a full `_layouts/post.html` fork if possible.

If the safest implementation for a particular Chirpy version requires a one-line include, the installer may patch/add that integration explicitly and reversibly.

---

# 26. Privacy

## 26.1 Minimum V1 controls

Support:

```text
exclude
private/hidden
source_visibility
stats_only
```

Recommended config:

```yaml
privacy:
  hide_items: []
  hide_sources: []
  stats_only_items: []
```

Mapping-level override:

```yaml
privacy:
  game:7f5f74c5:
    hidden: true
```

---

## 26.2 Apply privacy before public artifacts

Secrets are never public.

Additionally, privacy filtering must occur before generated public JSON is written.

Do not write hidden private item details into `assets/data/...` and merely hide them with CSS.

---

# 27. Localization

## 27.1 V1 languages

**LOCKED**

Ship:

```text
zh-CN
en
```

All UI strings must be externalized.

Example:

```yaml
library:
  title: "个人图书馆"
filters:
  all: "全部"
  status: "状态"
```

No hardcoded Chinese or English UI strings in JavaScript templates where avoidable.

---

## 27.2 Data language

Canonical metadata may retain source languages.

`title`, `title_original`, and `alternate_titles` should make it possible to present multilingual names without translating data artificially.

---

# 28. Theme contract

## 28.1 Base styling

PGL ships neutral, functional base styles.

Personal blog branding must be layered on top.

---

## 28.2 CSS variables

Minimum contract:

```css
--pgl-bg
--pgl-surface
--pgl-surface-alt
--pgl-border
--pgl-text
--pgl-muted
--pgl-heading
--pgl-accent
--pgl-link
--pgl-shadow
--pgl-radius
```

Status variables may be provided separately.

Do not hardcode a site author's personal palette into public PGL.

---

## 28.3 Chirpy light/dark

The Chirpy adapter should inherit theme values when practical.

A user's custom site may override:

```css
:root {
  --pgl-bg: ...;
}

html[data-mode="dark"] {
  --pgl-bg: ...;
}
```

The exact Chirpy dark-mode selector must be tested against supported versions rather than assumed permanently.

---

# 29. Configuration contract

Recommended `_config.yml`:

```yaml
prospero_great_library:
  enabled: true
  locale: zh-CN

  page:
    permalink: /library/

  sources:
    bangumi:
      enabled: true
      username: ""
      priority: 100

    neodb:
      enabled: true
      instance: "https://neodb.social"
      mode: public
      username: ""
      priority: 50

    steam:
      enabled: true
      steam_id: ""

  precedence:
    book: [bangumi, neodb]
    comic: [bangumi, neodb]
    movie: [bangumi, neodb]
    drama: [bangumi, neodb]
    anime: [bangumi, neodb]
    music: [bangumi, neodb]

  categories:
    order:
      - book
      - comic
      - movie
      - drama
      - anime
      - game
      - music

  sync:
    timezone: "Asia/Shanghai"
    on_deploy: true
    daily: true
    preserve_last_good: true

  history:
    enabled: true
    partition: year
    steam_playtime_deltas: true

  association:
    enabled: true
    exact: true
    fuzzy: true
    auto_threshold: 0.95
    suggest_threshold: 0.80
    auto_edit_posts: false

  privacy:
    enabled: true

  ui:
    layout: grid
    allow_grid_list_toggle: true
    drawer: true
    lazy_render: true
    show_stats: true
    show_timeline: true
    show_sources: true
    show_steam_playtime: true
    show_achievements: true
```

Environment secrets:

```text
BANGUMI_ACCESS_TOKEN
NEODB_ACCESS_TOKEN        # optional in public-capable mode
STEAM_API_KEY
```

Never place secrets in `_config.yml`.

---

# 30. Generated-data ownership

## 30.1 Repository persistence

Because V1 history is required, generated state must persist across workflow runs.

Default persistence:

```text
blog Git repository
```

The PGL workflow may commit:

- current source snapshots;
- canonical library;
- stats;
- history events;
- diagnostics that are intentionally persisted.

---

## 30.2 Generated commit policy

Recommended commit format:

```text
chore(pgl): sync personal library [2026-08-18]
```

Avoid a commit when generated public state is byte-for-byte unchanged.

History append must be deterministic to prevent duplicate events on rerun.

---

## 30.3 Workflow recursion

The implementation must explicitly avoid deployment/sync loops.

The reference workflow should combine or coordinate:

```text
sync -> persist -> build -> deploy
```

rather than assuming a generated commit will always trigger a second GitHub Actions workflow.

Workflow behavior caused by `GITHUB_TOKEN` must be verified against current GitHub documentation during implementation.

---

# 31. GitHub Actions model

## 31.1 Supported triggers

```yaml
on:
  push:
    branches: [main]
  schedule:
    - cron: "..."
  workflow_dispatch:
```

Exact cron should remain user-configurable.

---

## 31.2 Permissions

Use least privilege.

Likely required:

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

Only request permissions actually needed by the final workflow.

---

## 31.3 Build model

Reference concept:

```text
checkout
setup Python
install PGL
sync
persist generated data if appropriate
setup Ruby/Jekyll
build Chirpy
upload Pages artifact
deploy Pages
```

GitHub officially supports custom Pages workflows; PGL should use that mechanism rather than relying on the restricted default GitHub Pages Jekyll plugin environment.

---

# 32. Local development

Developer commands should converge toward:

```bash
pgl doctor
pgl sync
pgl build-data
pgl associate-posts
pgl stats
pgl install --adapter chirpy
```

Local credentials from environment or `.env` ignored by Git.

A dry-run mode should show intended changes without writing.

Example:

```bash
pgl sync --dry-run
```

---

# 33. Installation experience

Target: approximately a short, straightforward setup rather than a theme migration.

Ideal flow:

```text
1. Add PGL Action / install PGL integration
2. Add prospero_great_library config to _config.yml
3. Add enabled-source usernames/IDs
4. Add required GitHub Secrets
5. Enable custom GitHub Actions Pages workflow
6. Add/install /library/ page
7. Run manual sync
```

Installation should not require:

- database provisioning;
- Docker;
- Node front-end tooling;
- migrating away from Jekyll;
- forking Chirpy.

---

# 34. Demo site

V1 deliverable includes a demo.

Requirements:

- fake fixture data;
- no personal credentials;
- all seven categories represented;
- all five statuses represented;
- multiple-source merged entities;
- Bangumi-only item;
- NeoDB-only item;
- Steam-only item;
- performance-tag Movie;
- anime movie demonstrating Anime-only classification;
- Comic vs Book distinction;
- article association;
- timeline;
- Steam playtime statistics;
- Light/Dark presentation.

---

# 35. Testing policy

Detailed CI design is not part of this architecture document, but V1 implementation must include at minimum:

```text
Schema validation
Adapter unit tests
Fixture-based API parsing tests
Entity-resolution tests
Category classifier tests
History-diff tests
Association tests
Jekyll build smoke test
Chirpy Light/Dark visual checks
GitHub Actions integration check
Mock source failure tests
Privacy-output tests
```

No feature should be considered complete solely because sample code compiles.

---

# 36. Important invariants

The implementation must validate these invariants:

1. One canonical entity has exactly one primary category.
2. `book` and `comic` never overlap.
3. Anime movies are `anime`, not `movie`.
4. Performance items are `movie` with `performance` tag.
5. Bangumi wins conflicting Bangumi/NeoDB fields by default.
6. Steam does not decide subjective completion status.
7. Hidden items never enter public output.
8. A failed source never becomes an accidental empty collection.
9. Canonical IDs remain stable across title changes.
10. Ambiguous fuzzy matches never auto-merge.
11. History events are idempotent.
12. Secrets never enter generated site files.
13. Preferred external links fall back safely.
14. Browser operation does not require third-party API credentials.
15. Article fuzzy association never silently edits Markdown.

---

# 37. Performance expectations

PGL should comfortably support a personal library of several thousand items.

Front-end strategy:

- precomputed facets/statistics;
- client-side indexing once;
- lazy card rendering;
- debounced search;
- avoid one DOM node per history event at initial load;
- fetch yearly history partitions on demand;
- cache parsed data in memory.

Do not optimize prematurely for millions of items.

---

# 38. Accessibility

V1 UI should include:

- keyboard-accessible controls;
- focus management for drawer/modal;
- visible focus states;
- semantic buttons;
- meaningful alt text when provided;
- screen-reader labels for icon-only source badges;
- reduced-motion consideration;
- sufficient contrast through theme variables.

---

# 39. SEO and indexing

The `/library/` page may be indexed as ordinary site content.

However:

- client-side filter URLs do not need separate SEO pages in V1;
- primary item detail pages are not generated;
- external source links should be ordinary safe links;
- hidden/privacy-filtered records must not leak into structured data.

---

# 40. Release and compatibility policy

## 40.1 SemVer

Use semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
1.0.0
1.1.0
1.1.1
```

---

## 40.2 Schema version

Canonical data also has an independent:

```text
schema_version
```

A PGL code release may change without changing the schema.

If schema migration is necessary:

- provide migration code;
- document it;
- keep old history readable or migrate it atomically.

---

## 40.3 Adapter API changes

External API breakage normally produces a PATCH release if PGL public behavior does not change.

---

# 41. V1 scope

V1 includes:

```text
✓ Bangumi adapter
✓ NeoDB adapter
✓ Steam adapter

✓ Book
✓ Comic
✓ Movie
✓ Drama
✓ Anime
✓ Game
✓ Music

✓ Bangumi-first precedence
✓ Rule-based canonical classifier
✓ Automatic entity resolution
✓ Explicit mapping escape hatch
✓ Unified status
✓ Normalized ratings
✓ Current canonical library

✓ History/Event Log
✓ Steam playtime deltas
✓ Timeline
✓ Yearly observed Steam playtime statistics

✓ Article exact association
✓ High-confidence fuzzy association
✓ Ambiguity diagnostics

✓ /library/
✓ Filters/search/sorting
✓ Grid/List
✓ Drawer
✓ Statistics
✓ i18n zh-CN/en
✓ privacy filters
✓ Chirpy adapter
✓ CSS-variable theme contract
✓ Demo
✓ GitHub Actions reference deployment
```

---

# 42. V1 non-goals

V1 does NOT include:

```text
✗ runtime server/backend
✗ database service
✗ React/Vue requirement
✗ automatic write-back to Bangumi
✗ automatic write-back to NeoDB
✗ automatic write-back to Steam
✗ manual creation of source-less media items
✗ per-item generated detail pages
✗ multi-category membership
✗ separate Opera top-level category
✗ separate Performance hierarchy
✗ browser-side API secrets
✗ arbitrary historical backfill without evidence
✗ support guarantee for every Jekyll theme
✗ support guarantee for every historical Chirpy release
```

---

# 43. V2 candidates

Possible V2 features, not V1 contracts:

```text
More Jekyll theme adapters
Optional generic theme adapter
Source plugin SDK
Additional sources
Cover proxy/cache
Offline asset localization
Advanced analytics
Reading/watching streaks
Richer anime episode progress
Achievement timeline visualization
Data export/import
Optional standalone static library app
Optional PWA enhancements
Optional federated public library export
```

No V2 feature should break V1 invariants casually.

---

# 44. V3 candidates

Possible longer-term direction:

```text
Theme-independent Universal Personal Library standard
Schema export as JSON Feed / ActivityStreams-compatible records
Non-Jekyll static site adapters
Hugo/Eleventy/Astro adapter packages
Source marketplace
Cross-site portable Personal Library package
```

The core schema should therefore avoid unnecessary Chirpy-specific concepts.

---

# 45. Security contract

Required:

- secrets in environment/GitHub Secrets;
- no secret values in logs;
- redact authorization headers;
- timeouts on network requests;
- TLS verification on;
- no arbitrary code execution from source metadata;
- sanitize rich text/HTML;
- escape Liquid/HTML output;
- validate image URLs;
- guard against malicious source strings used as DOM HTML;
- pin or constrain dependencies;
- principle of least privilege for Actions.

Source reviews/descriptions should be treated as untrusted input.

---

# 46. Data provenance

Every important canonical field should be traceable to its source.

Recommended internal helper:

```json
{
  "_provenance": {
    "title": "bangumi",
    "cover.url": "bangumi",
    "summary": "neodb",
    "status": "bangumi",
    "rating": "bangumi"
  }
}
```

This may be omitted from public output if `sources` already provides enough provenance, but internal generation/tests should retain provenance awareness.

---

# 47. Source freshness

A stale source must be distinguishable from a fresh source.

Each source snapshot stores:

```text
fetched_at
last_success_at
adapter_version
source_api_version if discoverable
record_count
```

This makes debugging data disagreements possible.

---

# 48. Diagnostics philosophy

PGL should be highly diagnosable without being noisy.

`pgl doctor` should report:

```text
Configuration
Enabled adapters
Missing secrets
API reachability
NeoDB instance version/capabilities
Bangumi user reachability
Steam profile/library visibility
Current data freshness
Ambiguous entity matches
Ambiguous article matches
History writeability
Jekyll integration presence
```

A newcomer should not need to read source code to diagnose a blank library.

---

# 49. NeoDB federation consideration

NeoDB is not a single fixed service implementation.

The adapter must allow:

```yaml
instance: "https://neodb.social"
```

or another NeoDB instance.

Do not hardcode `neodb.social` except as a default/example.

The adapter should perform capability/version discovery when practical.

---

# 50. Source-specific metadata vs canonical metadata

Source-native extra fields can live under:

```text
sources.<source>.extra
```

Do not continuously expand the canonical schema for every provider-specific field.

Promote a source field to canonical only if:

- multiple sources can conceptually provide it; or
- it is a core PGL UI concept;
- the field has stable semantics.

Steam telemetry is explicitly canonicalized under `telemetry.steam` because it is a first-class Game feature.

---

# 51. Cover/image strategy

V1 may initially use remote image URLs.

The schema must allow future localization:

```json
{
  "cover": {
    "url": "...",
    "source": "bangumi",
    "cached": false,
    "local_path": null
  }
}
```

If cover caching is added later:

- obey source terms;
- maintain attribution/provenance;
- do not make cached cover existence a requirement for core operation.

---

# 52. Timeline UI

Timeline must load incrementally.

Suggested:

```text
2026
  Aug
    Completed X
    Steam +2h 36m on FINAL FANTASY
    Rating changed ...
```

Filters:

```text
All
Status
Rating
Progress
Game time
Achievements
```

Do not load the entire multi-year history into initial DOM.

---

# 53. Article association output

Recommended generated file:

```json
{
  "by_entity": {
    "game:7f5f74c5": [
      {
        "url": "/posts/ff1-record/",
        "title": "游戏记录：Final Fantasy 1",
        "confidence": 0.98,
        "method": "title_alias"
      }
    ]
  },
  "by_post": {
    "/posts/ff1-record/": [
      {
        "entity_id": "game:7f5f74c5",
        "confidence": 0.98,
        "method": "title_alias"
      }
    ]
  }
}
```

One post may explicitly reference multiple library items if needed.

The "one category per item" rule does not mean "one item per post".

---

# 54. Mapping overrides

`mappings.yml` should support:

```yaml
entities:
  - id: "game:7f5f74c5"
    bangumi: 12345
    steam: 39140

classifications:
  - source: neodb
    source_id: "..."
    category: comic

articles:
  - post: "_posts/2025-08-22-FF1记录.md"
    entity: "game:7f5f74c5"

privacy:
  - entity: "book:..."
    hidden: true
```

This remains optional.

The user previously chose not to support manually creating arbitrary source-less media entities. Mapping an existing source record is allowed.

---

# 55. Data migration from earlier builds

Even V1 should prepare for generated data migrations.

CLI:

```bash
pgl migrate
```

Rules:

- back up generated files before destructive migration;
- schema migration must be deterministic;
- do not refetch all APIs merely because schema layout changes unless unavoidable;
- preserve stable canonical IDs and history event identity.

---

# 56. Canonical sorting

Default visual sort should be configurable.

Suggested default:

```text
recent canonical/user update descending
```

Other sort keys:

```text
title
year
rating
status
steam_playtime
first_seen
last_seen
```

Stable tie-break:

```text
canonical ID
```

to avoid card order flicker between builds.

---

# 57. Search

Client-side search index should include:

```text
title
title_original
alternate_titles
year
tags
source names
category label
```

Do not index private/hidden items.

Search normalization should support CJK text without requiring Latin tokenization.

---

# 58. Progress

Canonical progress:

```json
{
  "current": 8,
  "total": 12,
  "unit": "episode",
  "percent": 66.67,
  "source": "bangumi"
}
```

Possible units:

```text
episode
chapter
volume
track
percent
unknown
```

Do not force Steam playtime into `progress`.

Steam playtime belongs to telemetry.

---

# 59. Performance tag

**LOCKED**

Performance is a tag, not a top-level category and not a subtype hierarchy requirement.

Canonical example:

```json
{
  "category": "movie",
  "tags": ["performance"]
}
```

Optional source-native tags may additionally indicate:

```text
opera
stage play
musical
```

but PGL V1 UI only requires the general `performance` distinction.

Normal movies do not need a `movie` tag.

---

# 60. Default source-link labels

Recommended:

```text
Bangumi
NeoDB
Steam
```

Icons/badges may be styled but must retain accessible text labels.

---

# 61. Open-source packaging strategy

Initial release:

```text
GitHub repository
├── Python core
├── composite/reusable GitHub Action
├── Jekyll integration assets
└── Chirpy adapter
```

Later, if useful:

```text
PyPI package
RubyGem helper
GitHub Marketplace Action
```

Do not delay core V1 solely to publish across every package registry.

---

# 62. License

PGL project code target license:

```text
MIT
```

Third-party code must not be copied into PGL unless license compatibility and attribution requirements are satisfied.

Using a public API does not grant permission to copy upstream application code without respecting its license.

NeoDB itself is AGPLv3; PGL should consume its API through an independent adapter rather than copy NeoDB server code.

---

# 63. Official upstream references

These are implementation references, not frozen API contracts.

## Bangumi

```text
https://bangumi.github.io/api/
```

Current verified capabilities at design time include user collections, subject metadata/search, and episodes.

## NeoDB

```text
https://neodb.net/
https://neodb.net/features/
https://neodb.net/api/
https://neodb.social/developer/
```

Current design-time documentation states NeoDB provides APIs for user collections/reviews and OAuth, with instance developer/OpenAPI documentation.

## Steam

```text
https://partner.steamgames.com/doc/webapi/IPlayerService
https://partner.steamgames.com/doc/webapi/ISteamUserStats
```

Current design-time documentation includes owned games, recently played games, and player achievements.

## Chirpy

```text
https://chirpy.cotes.page/posts/getting-started/
https://github.com/cotes2020/jekyll-theme-chirpy
https://github.com/cotes2020/chirpy-starter
```

Chirpy currently documents custom styles and GitHub Actions deployment.

## GitHub Pages custom workflow

```text
https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
```

GitHub Pages supports custom Actions workflows for build/deployment.

---

# 64. Implementation-time verification checklist

Before implementing each adapter, a future developer/agent must verify:

## Bangumi

```text
[ ] current API version/schema
[ ] auth mechanism
[ ] collection pagination
[ ] collection enum mappings
[ ] subject categories
[ ] episode/progress fields
[ ] error/rate-limit behavior
```

## NeoDB

```text
[ ] configured instance version
[ ] current OpenAPI availability
[ ] public collection retrieval capability
[ ] OAuth flow
[ ] collection status fields
[ ] rating scale
[ ] item type mapping
[ ] external source links
[ ] pagination
```

## Steam

```text
[ ] current Web API key behavior
[ ] profile/game-details visibility
[ ] owned-game fields
[ ] recent-play fields
[ ] last-played availability
[ ] achievement access
[ ] per-game schema caching
```

Never skip this checklist based only on prior model memory.

---

# 65. Recommended implementation phases

## Phase 0 — Skeleton

Deliver:

```text
repository
Python package
config parser
schema
CLI
fixture pipeline
Jekyll output writer
```

Acceptance:

```text
pgl build-data --fixtures
```

creates a valid static library.

---

## Phase 1 — Bangumi vertical slice

Deliver:

```text
Bangumi fetch
status mapping
rating mapping
category classification
canonical output
/library/ basic grid
```

Why first:

Bangumi is the default primary source and exercises most canonical concepts.

Acceptance:

```text
Bangumi-only user -> valid Book/Comic/Movie/Drama/Anime/Game/Music where data permits
```

---

## Phase 2 — NeoDB + merge

Deliver:

```text
NeoDB public/auth modes
NeoDB normalization
Bangumi > NeoDB precedence
entity resolution
Book/Comic merge
Anime movie reclassification
Performance tag behavior
```

Acceptance:

```text
same work from Bangumi + NeoDB => one canonical entity
```

---

## Phase 3 — Steam

Deliver:

```text
owned games
playtime
recent playtime
achievements
Bangumi+Steam game matching
game telemetry UI
```

Acceptance:

```text
Bangumi subjective record + Steam telemetry => one Game card
```

---

## Phase 4 — History

Deliver:

```text
source snapshot diff
append-only events
year partitions
Steam positive playtime deltas
timeline
yearly observed playtime stats
```

Acceptance:

Two consecutive fixture syncs generate exactly the expected idempotent events.

---

## Phase 5 — Article associations

Deliver:

```text
post scanner
exact ID/URL/ISBN matching
title/alias high-confidence matching
diagnostics
Library -> Post links
Post -> Library mini-card
```

Acceptance:

Exact identifiers bind at confidence 1.0; ambiguous fuzzy cases never auto-bind.

---

## Phase 6 — Production UI

Deliver:

```text
filters
search
sort
Grid/List
drawer
stats
timeline
lazy render
zh-CN/en
privacy
accessibility
```

---

## Phase 7 — Chirpy hardening + demo

Deliver:

```text
two-current-release compatibility matrix
light/dark checks
starter installer
demo site
reference workflow
release packaging
```

---

# 66. V1 acceptance criteria

PGL V1 is not complete until all of the following are true:

```text
[ ] A new Chirpy user can install it without migrating theme.
[ ] At least Bangumi, NeoDB, and Steam adapters work from Actions.
[ ] Secrets are absent from generated site files.
[ ] /library/ is usable as static output.
[ ] Seven categories exist and are mutually deterministic.
[ ] Book/Comic do not overlap.
[ ] Anime movies do not leak into Movie.
[ ] Performance appears as Movie + performance tag.
[ ] Bangumi wins NeoDB conflicts by default.
[ ] Precedence is user-configurable.
[ ] Entity IDs remain stable.
[ ] Bangumi+NeoDB duplicate works merge safely.
[ ] Bangumi+Steam duplicate games merge safely.
[ ] Ambiguous matches remain unmerged.
[ ] Universal statuses work.
[ ] Ratings preserve native and normalized values.
[ ] History persists between workflows.
[ ] Timeline works.
[ ] Steam yearly observed delta statistics work.
[ ] Source failures preserve last-good data.
[ ] Article exact association works.
[ ] High-confidence auto association works.
[ ] Fuzzy ambiguity creates diagnostics.
[ ] No automatic post rewriting occurs.
[ ] Privacy removes hidden item data before public output.
[ ] zh-CN and en both work.
[ ] Chirpy light/dark both remain usable.
[ ] Demo has no personal secrets.
```

---

# 67. Decisions that must NOT be accidentally reverted

Future maintainers should pay particular attention to these choices:

```text
PGL is an Extension/Starter Kit, not merely a Ruby Gem.

Core is Jekyll-generic.
V1 official adapter is Chirpy.

Seven categories:
Book / Comic / Movie / Drama / Anime / Game / Music.

One item = one category.

Book != Comic.

Anime movie = Anime only.

Opera/stage play/musical:
Movie category + optional "performance" tag.
No extra top-level Opera.
No required secondary hierarchy.

Bangumi is first source globally when competing with NeoDB.
NeoDB fills Bangumi gaps.

Game:
Bangumi subjective state.
Steam telemetry.

Universal statuses:
wishlist / in_progress / completed / on_hold / dropped.

Ratings:
preserve native + normalized_10.

History is INCLUDED in V1.

Steam playtime deltas and timeline are INCLUDED in V1.

One /library/ page.
No V1 item detail pages.

Anime/Game preferred external link = Bangumi.
Other categories preferred external link = NeoDB.
Fallback automatically to an available source.

Article association:
exact automatic
high-confidence automatic
ambiguous suggestion only
never silently rewrite posts.

No manually created source-less media items in V1.

Public NeoDB mode is default.
Authenticated NeoDB mode is supported.

Front-end is static.
No runtime backend.

Vanilla JS.
Python owns data pipeline.
Jekyll/Ruby owns rendering integration.
GitHub Actions owns orchestration.

All source adapters optional.

zh-CN + en.

CSS variable theme contract.
Personal site branding is an override, not public-core styling.

MIT license.

Support the two most recent TESTED Chirpy release lines, not every historical release.
```

---

# 68. Prompt for future coding agents

When asked to implement or continue `Prospero_Great_Library`, follow this sequence:

```text
1. Read PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md completely.
2. Inspect the current repository and current implementation status.
3. Identify which implementation phase is currently incomplete.
4. Verify current official API documentation for every external source touched.
5. Do not redesign locked decisions unless explicitly instructed.
6. Implement the smallest coherent vertical slice.
7. Add/adjust tests for schema, classification, resolution, history, and failure behavior.
8. Run tests and a Jekyll/Chirpy build.
9. Validate generated JSON against schema.
10. Confirm no secrets are present in generated files.
11. Update implementation status/release notes.
12. If architecture changed, update this file in the same change and explain why.
```

Before claiming a feature works, distinguish:

```text
code exists
fixture test passes
integration test passes
live API verified
Chirpy runtime verified
```

Do not label unverified live behavior as verified.

---

# 69. Final architecture summary

```text
                         Prospero_Great_Library
                                  │
        ┌─────────────────────────┼────────────────────────┐
        │                         │                        │
     Bangumi                    NeoDB                    Steam
   primary semantics        secondary/fallback       game telemetry
        │                         │                        │
        └──────────────┬──────────┴───────────┬────────────┘
                       │                      │
                 Source Adapters       Capability/Health
                       │
                 Normalized Records
                       │
             Rule-based Classification
                       │
               Entity Resolution
                       │
             Bangumi-first Merge
                       │
                Canonical Library
                       │
             ┌─────────┼─────────┐
             │         │         │
          History    Stats    Associations
             │         │         │
             └─────────┼─────────┘
                       │
             Privacy + Validation
                       │
              Static Jekyll Data
                       │
                 Chirpy Adapter
                       │
                    /library/
                       │
          Vanilla JS progressive UI
```

PGL's central architectural promise is:

> **Users keep their records in the services they already use; PGL turns those records into a stable, private-by-construction, source-aware, history-capable, theme-extensible personal media library for a static Jekyll site.**

The user's own blog may apply a custom day/night visual override, but such personal branding must remain separate from the universal PGL base.

---

# 70. Change-control note

This design is intentionally opinionated.

If future implementation suggests a different approach, ask:

```text
Is this an implementation detail?
    -> change implementation, preserve this architecture.

Is this an external API change?
    -> change adapter, preserve canonical contract.

Is this a real product requirement change?
    -> update this document explicitly.

Is this merely easier to code?
    -> do NOT weaken the architecture for convenience.
```

This document should evolve deliberately, not accidentally.

# 71. Upstream-native privacy boundary (added after first live deployment)

## 71.1 Bangumi private collection handling

**LOCKED security behavior**

When an authenticated Bangumi response identifies a user collection entry as private and `sources.bangumi.hide_private_collections` is enabled, that source record MUST be excluded before:

```text
source snapshot persistence
entity resolution
canonical merge
statistics
article association
new history generation
public static output
```

The public repository/site must not rely on CSS or front-end filtering for this boundary.

PGL defaults this publication boundary to `true`. Advanced users may explicitly disable it, but authenticated public deployments SHOULD keep it enabled and tooling SHOULD warn when an authenticated Bangumi token is used with it disabled.

## 71.2 Retroactive privacy

Changing privacy later must not protect only the current snapshot while leaving old timeline data public. During a sync, PGL SHOULD use currently fetched private-source records only ephemerally to identify previously persisted canonical entities and sanitize old history.

Do NOT persist a separate list of private Bangumi subject IDs merely to support later scrubbing; such an index would itself disclose private collection membership.

If an entity disappears completely after its only private source is removed, all historical events for that entity must be removed from public history. If the canonical entity remains public through another source, remove private-source-specific events while retaining source-neutral history that is still valid for the public entity.

The same history boundary applies to PGL-level `hidden` and `stats_only` entities, and source-specific history events must respect `hide_sources`.

## 71.3 Privacy fail-closed invariant

Known-private records reaching a public source snapshot, canonical library, or public history are a publication invariant failure. This is separate from ordinary source-fetch strictness: a third-party outage may degrade gracefully, but a known privacy violation must not be silently published.

## 71.4 Git repository history is outside automatic artifact sanitization

**LOCKED security limitation**

PGL privacy filtering and history sanitization govern the current generated publication state. They cannot, by adding a later commit, erase sensitive data that was already committed into an earlier revision of a public Git repository.

Therefore:

```text
current/future generated artifacts -> PGL MUST sanitize automatically
old public Git commits              -> requires explicit repository-history maintenance
```

PGL MUST NOT automatically rewrite Git history, force-push branches, or destroy repository history. Tooling and documentation SHOULD warn users about this boundary when retroactive privacy cleanup is relevant.
## 71.5 Privacy diagnostic metadata

PGL SHOULD minimize persisted privacy metadata. The default `privacy.publish_diagnostics` value is `false`. Exact counts of upstream-private records and detailed scrub-reason counters may be available to the running audit/sync process, but SHOULD NOT be written into a public repository/site unless the owner explicitly opts in. Public status may state that the privacy filter is enabled and that sanitization occurred without publishing private-item counts.

