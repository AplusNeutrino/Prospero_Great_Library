# Compatibility — Prospero Great Library 0.1.0-alpha.4

The architecture policy is to support the **two most recent tested Chirpy release lines** without promising every historical version.

## Release matrix

| PGL code | Chirpy target | Light | Dark | Evidence |
|---|---|---|---|---|
| 0.1.0-alpha.3 baseline | v7.6.0 | PASS | PASS | GitHub Actions run `32114762265` |
| 0.1.0-alpha.3 baseline | v7.5.0 | PASS | PASS | GitHub Actions run `32114762265` |
| 0.1.0-alpha.4 delivery | v7.6.0 | RUN_PENDING | RUN_PENDING | exact alpha.4 code must be uploaded first |
| 0.1.0-alpha.4 delivery | v7.5.0 | RUN_PENDING | RUN_PENDING | exact alpha.4 code must be uploaded first |

The alpha.3 GitHub run completed successfully and each compatibility cell installed PGL into a clean Chirpy Starter checkout, generated fixture data, verified the theme-variable contract, built Jekyll in production mode, and verified the built Library page.

`RUN_PENDING` for alpha.4 is deliberate: this delivery changes the page structure, JavaScript router, CSS, and Chirpy heading integration. Prior alpha.3 runtime evidence is strong baseline evidence but is not represented as proof that new alpha.4 code has executed on GitHub.

## Alpha.4 adapter contract

PGL still avoids copying Chirpy layouts. The adapter is limited to:

- a `/library/` tab starter;
- PGL includes;
- one small Ruby helper/hook;
- isolated Vanilla JS/CSS;
- a thin CSS-variable/theme bridge.

Alpha.4 additionally provides its own Library heading/search header. To avoid rendering Chirpy's normal page heading twice, the adapter uses the narrowly scoped selector:

```css
article:has(#prospero-great-library) > .dynamic-title {
  display: none;
}
```

The supported Chirpy `v7.6.0` and `v7.5.0` `_layouts/page.html` files were checked during development and both currently contain the expected direct `dynamic-title` heading plus `.content` wrapper. CI now verifies that layout contract before building. If Chirpy changes that structure in a future release, the compatibility job should fail instead of silently hiding unrelated headings.

## CI matrix

For each supported Chirpy version and Light/Dark mode, `.github/workflows/ci.yml` is expected to:

```text
checkout PGL
checkout clean Chirpy Starter
install PGL
install the Chirpy adapter
generate fixture data
verify theme + page-layout contracts
build Jekyll in production mode
verify /library/ and static PGL assets
```

The matrix is version-pinned so upstream changes cannot silently rewrite the evidence attached to an older PGL release.
