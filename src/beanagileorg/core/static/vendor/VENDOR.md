# Vendored design assets

Bundled so the apps look the same offline. Downloaded from the npm registry; each tarball matched the registry's sha512 integrity.

| Asset | Version | License | Files |
| --- | --- | --- | --- |
| Inter (variable, Latin, via @fontsource-variable/inter) | 5.3.0 | OFL-1.1 | `inter-latin-wght-normal.woff2`, `LICENSE-inter` |
| Lucide icons (via lucide-static) | 1.49.0 | ISC | `icons.svg` (subset built by `scripts/build_icons.py`), `LICENSE-lucide` |
| highlight.js (common languages, via @highlightjs/cdn-assets) | 11.9.0 | BSD-3-Clause | `highlight.min.js`, `LICENSE-highlightjs` |

Tailwind CSS v4.3.3 builds `../app.css` from `../src/app.css` with its standalone CLI (see `scripts/build-css.sh`). The CLI binary is not committed; its SHA-256 was checked against the release's `sha256sums.txt`.
