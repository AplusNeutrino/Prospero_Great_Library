# Delivery Notes — 0.1.0-alpha.3

## Baseline and provenance

This delivery was prepared against the latest deployed code/evidence available on 2026-08-18.

Upstream PGL baseline inspected before development:

```text
AplusNeutrino/Prospero_Great_Library
main: 115c7f2573033170d7ab72f0b3c18958899cb5dd
```

That baseline already includes the production-derived fixes for:

- paginated Bangumi collection responses;
- filtering Bangumi collection records whose upstream `private` flag is true when the filter is enabled.

Production blog runtime evidence inspected:

```text
AplusNeutrino/My_Blog
observed sync commit: 52b983c5007fb8eb8055d364046bcc87f7b7f2ed
```

The deployed sync reported all three configured source paths healthy and showed the Bangumi privacy filter operating on real collection data. This release treats that deployment evidence as the new real-world baseline rather than reverting to the original alpha.2 assumptions.

Installed PGL Jekyll/Chirpy resources in the blog (`_includes/pgl`, `_plugins/prospero_great_library.rb`, `assets/pgl`, and locale files) were compared by Git blob SHA with the PGL upstream resources and matched. Site-specific behavior therefore remains in blog configuration/workflow/theme overrides rather than being copied into the universal public UI core.

No GitHub write/push is performed by this delivery process.

## Release focus

`0.1.0-alpha.3` is a privacy-boundary and production-sync hardening release.

### Integrated from deployed production work

- Bangumi paginated collection handling.
- `hide_private_collections` interception before persistence/merge.
- Production-tested NeoDB authenticated shelf behavior remains intact.
- Production-tested explicit Pages-dispatch pattern informed the generalized reference workflow.

### Privacy hardening added in alpha.3

- Bangumi private-collection interception is **enabled by default**.
- Upstream-private records are removed before:
  - source snapshots;
  - entity resolution;
  - canonical merge;
  - statistics;
  - article associations;
  - new history generation;
  - public static output.
- Private source identifiers used for cleanup remain ephemeral in memory and are not persisted as a private-ID index.
- Existing yearly history partitions are retroactively sanitized when a currently-private source record can be tied to a previously public canonical entity.
- A private-only entity loses all public timeline events, including source-neutral `first_seen` history.
- A mixed-source entity may remain public through another source while Bangumi-specific private events are removed.
- PGL-level `hidden`, `stats_only`, global `hide_sources`, and per-entity source visibility now apply to persisted history as well as current cards.
- Known privacy violations fail closed instead of being treated like a normal degraded source outage.
- New `pgl privacy-audit` command:
  - read-only by default;
  - `--apply` performs the sanitized write;
  - uses the same live source credentials as a normal sync when upstream-private records must be discovered.
- Detailed private-record counts and scrub-reason counters are **not persisted by default**.
  - `privacy.publish_diagnostics: false` is the default.
  - full details remain available to the running `privacy-audit` process;
  - explicit `true` opt-in may persist detailed diagnostics.
- Public `sync_status.json` records that the filter is applied without publishing the private collection count by default.

## Git-history security boundary

PGL can sanitize the current working tree and all future generated artifacts. It cannot erase data from an earlier public Git commit by adding a later commit.

If a private record was committed before privacy interception existed, removing/resetting the current snapshot/history does **not** by itself remove that data from repository history. Cleaning such an old revision requires an explicit one-time Git history rewrite/removal by the repository owner.

PGL intentionally does not automate force-push/history rewriting because that operation is destructive and repository-wide.

## Workflow hardening

The reference `workflows/pgl-sync.yml` now:

- detects untracked generated files with `git status --porcelain` rather than relying on `git diff`;
- persists only PGL generated state;
- rebases before push;
- serializes sync jobs through a concurrency group;
- can dispatch a separate Pages workflow after data changes when repository variable `PGL_PAGES_WORKFLOW` is configured;
- does not hard-code a user's blog-specific Pages workflow filename.

## New/updated operator controls

```yaml
prospero_great_library:
  sources:
    bangumi:
      hide_private_collections: true   # alpha.3 default

  privacy:
    publish_diagnostics: false         # alpha.3 default
```

Commands:

```bash
pgl doctor --site-root .
pgl privacy-audit --site-root .
pgl privacy-audit --site-root . --apply
pgl sync --site-root .
```

## Evidence classification

### Live evidence inherited from the deployed baseline

```text
Bangumi collection sync                  LIVE_PASS
Bangumi paginated collection handling    LIVE_PASS
Bangumi private filtering                LIVE_PASS
NeoDB authenticated shelf sync           LIVE_PASS
Steam owned-library sync                 LIVE_PASS
Jekyll/Chirpy integration deployed       USER_DEPLOYED
sync -> persist -> Pages dispatch pattern USER_DEPLOYED
```

The deployed run completed all three enabled collection paths and the Bangumi filter intercepted a nonzero set of real private collection records. Exact production library/private-record counts are intentionally omitted from this public release documentation. Alpha.3 also stops persisting the private-record count by default.

### Still not promoted to live/runtime evidence

```text
NeoDB anonymous/public collection mode   LIVE_UNVERIFIED (instance-dependent)
Steam achievements                       LIVE_UNVERIFIED (disabled in deployed blog)
Exact Chirpy v7.6/v7.5 × Light/Dark CI   CI_DEFINED / RUN_PENDING
```

The local packaging environment has Ruby but no Bundler/Jekyll executable, so Ruby syntax checks are possible while exact Chirpy builds are not. No retrievable PGL commit workflow run was available through the GitHub connector while preparing alpha.3. Do not label the four-cell Chirpy matrix as passed until the uploaded repository actually executes it successfully.

## Upgrade notes for the production blog

After the user uploads alpha.3 to `AplusNeutrino/Prospero_Great_Library`:

1. commit/publish the PGL repository manually;
2. obtain the resulting alpha.3 commit SHA or release tag;
3. update the blog's `.github/workflows/pgl-sync.yml` `uses:` reference from `115c7f...` to the new pinned SHA/tag;
4. keep `hide_private_collections: true` (it is now also the default);
5. run `pgl privacy-audit`/the sync workflow with the normal source secrets;
6. inspect the new privacy status and normal library output;
7. let the blog Pages workflow deploy the generated data.

The current production blog already reset its snapshots/history after the first privacy fix, so its first alpha.3 scrub may legitimately report no legacy history to remove. The important improvement is that future upstream privacy changes will no longer require that manual reset for current generated history.

## Final-package verification

Pre-ZIP release QA for alpha.3:

```text
pytest                                      PASS — 54 tests
Python compileall                           PASS
Ruby plugin syntax                          PASS
JavaScript syntax                           PASS
JSON/YAML parse                             PASS
Demo fixture pipeline                       PASS
Identical-fixture history idempotency       PASS
Privacy migration/history scrub             PASS
Source-failure last-good fallback            PASS
Installer idempotency                       PASS
Wheel build + isolated install              PASS
Packaged Chirpy resources                   PASS
Account/secret leakage scan                 PASS
Exact Chirpy v7.6/v7.5 × Light/Dark runtime RUN_PENDING
```

The current compatibility matrix targets Chirpy `v7.6.0` and `v7.5.0`, which are the two most recent published RubyGem releases as of 2026-08-18. The local packaging environment lacks Bundler/Jekyll, so those full theme builds are intentionally left `CI_DEFINED / RUN_PENDING` rather than being claimed as passed.

The final delivery ZIP SHA-256 is written to the separate `.sha256` file generated after the ZIP is created. Per-file repository checksums are stored in `SHA256SUMS.txt`.
