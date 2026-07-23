# Dossier architecture

`site/` is a hand-curated static artifact. It has no build-time connection to
private source, evidence stores, game data, or live telemetry.

## Content map

- `/infamous/` — current public snapshot and two-track overview
- `/infamous/devlog/` — dated, public-safe milestone notes
- `/infamous/method/` — proof vocabulary and clean-room boundaries
- `/infamous/roadmap/` — gate-by-gate route to playable gameplay
- `/infamous/data/status.json` — the same small dated snapshot in machine-readable form

The JSON file is static and reviewed. It is not a runtime payload.

## Hosting

This repository is a GitHub Pages **project site**, so its default URL is
`https://bucketcomps.github.io/infamous/`. GitHub documents that a custom domain
assigned to the organization site is inherited by public project sites by
default; after a separately approved cutover, the intended URL is
`https://decomp.deucebucket.com/infamous/`.

The dynamic stream/dashboard remains a separate locally hosted system. This
site only contains a clearly held link to the proposed
`https://live.decomp.deucebucket.com/infamous` endpoint.

Official reference:
[About custom domains and GitHub Pages](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages).
