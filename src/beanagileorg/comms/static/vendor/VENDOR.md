# Vendored libraries

Bundled so decks work offline. Downloaded from the npm registry; each tarball matched the registry's sha512 integrity.

| Library | Version | License | Files |
| --- | --- | --- | --- |
| reveal.js | 5.1.0 | MIT | `reveal/reveal.js`, `reveal/reveal.css`, `reveal/reset.css`, `reveal/plugin/notes.js` |
| lottie-web | 5.12.2 | MIT | `lottie/lottie_light.min.js` |

lottie-web's "light" SVG player is used on purpose: it leaves out After Effects expression support, so a Lottie file can't run code.
