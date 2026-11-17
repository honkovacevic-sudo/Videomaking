#!/usr/bin/env bash
# One-time setup for a fresh machine/session. Safe to re-run (skips what's done).
#   bash setup.sh
# Installs Python deps, then downloads the large assets from npm (the only
# registry reliably reachable in cloud sessions) and builds the caches:
#   - Natural Earth borders (world-atlas)       -> assets/raw/*.geojson, assets/countries_*.pkl
#   - NASA Blue Marble image (three-globe)      -> assets/basemap_mercator.png (legacy satellite style)
#   - Kokoro-82M voice model + voices           -> assets/voice/
set -euo pipefail
cd "$(dirname "$0")"

echo "== Python packages"
python3 -m pip install -q -r requirements.txt 2>&1 | grep -v -i "warning" || true
if ! python3 -c "import skia" 2>/dev/null; then
  echo "== System libraries for Skia (libEGL/libGL)"
  (apt-get install -y -q libegl1 libgl1 >/dev/null 2>&1 || (apt-get update -q >/dev/null 2>&1 && apt-get install -y -q libegl1 libgl1 >/dev/null 2>&1))
fi
python3 -c "import skia, kokoro_onnx, soundfile, scipy" || { echo "Python deps failed"; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p assets/raw assets/voice/voices

if [ ! -f assets/raw/countries-10m.geojson ] || [ ! -f assets/raw/earth-blue-marble.jpg ]; then
  echo "== Map data (npm: world-atlas, topojson-client, three-globe)"
  (cd "$TMP" && npm pack --silent world-atlas@2.0.2 topojson-client@3.1.0 three-globe@2.45.6 >/dev/null)
  for f in "$TMP"/*.tgz; do mkdir -p "${f%.tgz}"; tar xzf "$f" -C "${f%.tgz}"; done
  node -e '
    const [tmp, out] = process.argv.slice(1);
    const tc = require(tmp + "/topojson-client-3.1.0/package/dist/topojson-client.js");
    const fs = require("fs");
    for (const r of ["10m", "50m"]) {
      const t = JSON.parse(fs.readFileSync(`${tmp}/world-atlas-2.0.2/package/countries-${r}.json`));
      fs.writeFileSync(`${out}/countries-${r}.geojson`, JSON.stringify(tc.feature(t, t.objects.countries)));
    }' "$TMP" "$PWD/assets/raw"
  cp "$TMP/three-globe-2.45.6/package/example/img/earth-blue-marble.jpg" assets/raw/
  rm -f "$TMP"/*.tgz
fi

if [ ! -f assets/countries_10m.pkl ] || [ ! -f assets/basemap_mercator.png ]; then
  echo "== Building map caches"
  python3 -m strategist.prepare
fi

if [ ! -f assets/voice/kokoro-q8.onnx ]; then
  echo "== Voice model (npm: kokoro-q8-shards, kokoro-js, kokoro-local-runtime)"
  (cd "$TMP" && npm pack --silent kokoro-q8-shards@1.0.0 kokoro-js@1.2.1 kokoro-local-runtime@0.1.0 >/dev/null)
  for f in "$TMP"/kokoro*.tgz; do mkdir -p "${f%.tgz}"; tar xzf "$f" -C "${f%.tgz}"; done
  S="$TMP/kokoro-q8-shards-1.0.0/package"
  cat "$S"/kokoro-q8.part{0,1,2,3,4,5}.bin > assets/voice/kokoro-q8.onnx
  echo "fbae9257e1e05ffc727e951ef9b9c98418e6d79f1c9b6b13bd59f5c9028a1478  assets/voice/kokoro-q8.onnx" | sha256sum -c -
  cp "$TMP"/kokoro-js-1.2.1/package/voices/*.bin assets/voice/voices/
  cp -f "$TMP"/kokoro-local-runtime-0.1.0/package/voices/*.bin assets/voice/voices/
  rm -f assets/voice/voices.npz
fi

echo "== Smoke test"
python3 -c "
from strategist.voice import synth, SR
a = synth('Setup complete.', 'am_fenrir', 1.05)
print(f'voice OK ({len(a)/SR:.1f}s)')
" 2>&1 | grep -v -i warn
echo "Setup complete."
