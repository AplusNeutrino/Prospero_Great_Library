# Alpha.6 implementation status

Baseline: PGL `main` `1a217d2b519780ef11f0aafce8208972f8eae00a` (`0.1.0-alpha.5`).

## Done

- tolerant-but-fail-closed Steam public visibility parser;
- AppID-only malformed-XML recovery path with explicit HTML/structure rejection;
- safe Steam reattachment baseline: no lifetime-as-delta or detach-as-negative-correction;
- unavailable Steam UI uses unknown (`—`) rather than false zero;
- PGL-owned screen-reader search label and compact desktop/mobile search styling;
- polished rating SVG: ghost histogram + gradient area + curve + points + summary + underline scopes;
- Jekyll / packaged Chirpy / Demo mirrors for every changed UI resource;
- alpha.6 version markers.

## Local evidence for this incremental overlay

- targeted pytest: PASS (Steam parser/privacy recovery, Steam history baseline, UI contracts);
- Python compileall: PASS;
- JavaScript `node --check`: PASS;
- locale YAML parsing: PASS;
- changed-resource mirror byte equality: PASS.

## Requires uploaded full-repository CI/runtime evidence

- complete existing PGL pytest suite after overlay;
- wheel build from the complete repository;
- Chirpy 7.6/7.5 Light/Dark build matrix;
- live Steam Community malformed-response recovery;
- first production alpha.6 Steam sync and subsequent genuine playtime-delta sync.

Do not promote those items to PASS before the uploaded repository/runtime provides evidence.
