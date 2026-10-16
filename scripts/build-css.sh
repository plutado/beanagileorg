#!/bin/sh
# Rebuild src/beanagileorg/core/static/app.css from app.src.css with the Tailwind v4 standalone CLI.
# Download the CLI once into .tools/ (see src/beanagileorg/core/static/vendor/VENDOR.md).
set -e
cd "$(dirname "$0")/.."
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) bin=tailwindcss-macos-arm64 ;;
  Darwin-x86_64) bin=tailwindcss-macos-x64 ;;
  Linux-x86_64) bin=tailwindcss-linux-x64 ;;
  Linux-aarch64) bin=tailwindcss-linux-arm64 ;;
  *) echo "No Tailwind CLI mapping for this platform" >&2; exit 1 ;;
esac
[ -x ".tools/$bin" ] || { echo "Missing .tools/$bin. Download Tailwind v4.3.3's $bin into .tools/ and verify it against sha256sums.txt." >&2; exit 1; }
".tools/$bin" -i src/beanagileorg/core/static/app.src.css -o src/beanagileorg/core/static/app.css --minify "$@"
