# Delivery Notes — 0.1.0-alpha.5

## Baseline

Alpha.5 is based on the merged alpha.4 r2 code on `AplusNeutrino/Prospero_Great_Library` main (`46bba99dca66bf8e3218c3f5ffb5ef7eded01a0d`). No GitHub write is performed by this delivery process.

## Purpose

This is a targeted corrective release for five issues observed after alpha.4 was deployed on a real Chirpy blog.

### 1. Chirpy sidebar title

The adapter source previously hard-coded `title: Library`. The Ruby pre-render hook could correct the page's internal title but was too late to reliably change Chirpy's sidebar navigation label. Alpha.5 makes the installer render `_tabs/library.md` from the target `_config.yml`:

```text
zh locale: [site.title]大图书馆
other locale: [site.title] Great Library
explicit ui.title: wins over both defaults
```

The source `library-page.md` is now a template, and the install manifest records the hash of the rendered site-specific file so future safe upgrades remain deterministic.

### 2. Observable Rating Distribution

Production ratings are integer observations. Alpha.4 inserted zero-valued half-step bins into the curve, which distorted monotone smoothing. Alpha.5 uses only integer bins `1..10`. Decimal input, if encountered from another source, is folded deterministically to the nearest integer with half-up behavior. The hidden screen-reader element that produced the long `0.5: 0; 1: ...` text dump is removed; accessible labels remain on the SVG interaction points.

### 3. Steam covers and privacy

Steam's authenticated owned-games response can be more permissive than what an anonymous site visitor should see. Alpha.5 therefore treats public visibility as a publication boundary:

```text
anonymous public Steam games visibility
        ↓
public AppID set + public logo metadata
        ↓
GetOwnedGames requested only for those public AppIDs
        ↓
canonical/public PGL data
```

In privacy-safe mode PGL does not call the unfiltered `GetRecentlyPlayedGames`; it uses the public filtered owned-game fields (`playtime_2weeks`, `rtime_last_played`) for Current Activity. If the upstream ignores AppID filtering, a defensive post-filter still drops any non-public record before SourceRecord creation.

For Steam-only images, PGL prefers public Community logo metadata, upgrades legacy `http://` media/store URLs to HTTPS, and falls back to the app icon derived from `img_icon_url`, eliminating the previous blank-cover default for most Steam-only Current entries.

If public visibility cannot be verified and `privacy_fail_closed` is true (default), PGL publishes no Steam data for that run instead of reusing a potentially privacy-stale last-good Steam snapshot. Previous Steam entries that disappear from the public set are treated as privacy-impacted only in memory so old public history can be sanitized without writing a private-AppID index.

### 4. Current Activity order

Current Activity now uses the canonical taxonomy as its primary order:

```text
Book → Comic → Movie → Drama → Anime → Game → Music
```

Within each category, explicit `in_progress` precedes observational Steam-recent entries, then recency orders rows locally.

### 5. Bangumi Book/Comic classification

The Bangumi collection embeds `SlimSubject`, whose current official schema includes the top 10 subject tags. Alpha.4 ignored those metadata tags and tried to read a `platform` field not present in the SlimSubject schema. Alpha.5 ingests `subject.tags` and preserves explicit `SubjectBookCategory=1001` evidence when present. Comic classifier evidence includes `漫画`, `マンガ`, `まんが`, `コミック`, `manga`, `comic`, `manhua`, and `manhwa`.

This avoids issuing one extra detail request per Bangumi book and should restore the Comic ledger on the next successful Bangumi sync. Live classification remains explicitly unverified until the user's production collection is resynced.

## Operator defaults added

```yaml
prospero_great_library:
  sources:
    steam:
      filter_private_games: true
      privacy_fail_closed: true

  ui:
    rating_chart:
      bin_size: 1
```

## Evidence boundary

- Bangumi/Steam implementation and privacy transitions are covered by deterministic tests.
- Steam public-visibility probing and real Bangumi comic counts require the next live user sync for `LIVE_PASS`.
- Alpha.4 r2 has full CI PASS (`32202478262`).
- Alpha.5 Chirpy CI remains pending until the package is uploaded.
