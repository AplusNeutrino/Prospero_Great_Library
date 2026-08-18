# Compatibility — Prospero Great Library 0.1.0-alpha.2

The architecture policy is to support the **two most recent tested Chirpy release lines**, without promising all historical versions.

## Release matrix

| PGL | Chirpy target | Jekyll requirement from Chirpy | Light | Dark | Current evidence |
|---|---|---|---|---|---|
| 0.1.0-alpha.2 | v7.6.0 | `~> 4.3` | CI defined | CI defined | RUN_PENDING |
| 0.1.0-alpha.2 | v7.5.0 | `~> 4.3` | CI defined | CI defined | RUN_PENDING |

`RUN_PENDING` means the exact matrix exists in `.github/workflows/ci.yml`, but the packaging environment could not execute Bundler/Jekyll. Do not translate this status into “tested/passed” until GitHub Actions has actually completed those jobs.

## Adapter contract

PGL avoids copying Chirpy layouts. The adapter is limited to:

- a `/library/` tab starter;
- PGL includes;
- one small Ruby helper;
- isolated JS/CSS;
- a thin CSS-variable bridge.

For current Chirpy 7.6, the bridge uses stable public theme variables such as `--main-bg`, `--main-border-color`, `--text-color`, `--text-muted-color`, `--heading-color`, `--link-color`, `--card-bg`, and `--card-shadow`. CI resolves the installed Chirpy gem and checks both `_light.scss` and `_dark.scss` before building.

## CI matrix

The compatibility job checks:

```text
Chirpy v7.6.0 × light
Chirpy v7.6.0 × dark
Chirpy v7.5.0 × light
Chirpy v7.5.0 × dark
```

For each cell it installs PGL into a clean Chirpy Starter checkout, generates fixture data, verifies the theme-variable contract, builds Jekyll in production mode, then verifies that `/library/` and its static PGL assets exist.

This matrix is intentionally version-pinned so a future upstream Chirpy release cannot silently change the meaning of an older PGL release.
