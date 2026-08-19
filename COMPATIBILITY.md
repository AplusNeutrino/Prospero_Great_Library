# Compatibility — Prospero Great Library 0.1.0-alpha.5

The architecture policy is to support the **two most recent tested Chirpy release lines** without promising every historical version.

## Release matrix

| PGL code | Chirpy target | Light | Dark | Evidence |
|---|---|---|---|---|
| 0.1.0-alpha.4 r2 | v7.6.0 | PASS | PASS | GitHub Actions run `32202478262` |
| 0.1.0-alpha.4 r2 | v7.5.0 | PASS | PASS | GitHub Actions run `32202478262` |
| 0.1.0-alpha.5 delivery | v7.6.0 | RUN_PENDING | RUN_PENDING | exact alpha.5 code must be uploaded first |
| 0.1.0-alpha.5 delivery | v7.5.0 | RUN_PENDING | RUN_PENDING | exact alpha.5 code must be uploaded first |

Alpha.4 r2 completed its full GitHub Actions workflow successfully. Alpha.5 keeps the same Chirpy DOM/CSS integration model but changes the rendered tab title, data adapters, Current ordering, and rating chart data. The exact alpha.5 matrix therefore remains pending until the owner uploads the package and CI executes it.

## Adapter contract

PGL avoids copying Chirpy layouts. The adapter remains limited to a `/library/` tab, PGL includes, one small Ruby helper/hook, isolated Vanilla JS/CSS, and a thin CSS-variable/theme bridge.

The installed `_tabs/library.md` is now rendered by `pgl install` from the target site's `_config.yml` instead of shipping the literal title `Library`. For zh locales the default sidebar label is `[site.title]大图书馆`; other locales use `[site.title] Great Library`. Explicit `prospero_great_library.ui.title` overrides the generated title.

Alpha.4's scoped heading suppression remains unchanged:

```css
article:has(#prospero-great-library) > .dynamic-title {
  display: none;
}
```

## CI matrix

For each supported Chirpy version and Light/Dark mode, `.github/workflows/ci.yml` installs PGL into a clean Chirpy Starter checkout, generates fixture data, verifies theme/page contracts, builds Jekyll in production mode, and verifies `/library/` plus static PGL assets.
