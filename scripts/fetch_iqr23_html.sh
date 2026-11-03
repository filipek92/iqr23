#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <host> [output_dir]" >&2
  exit 1
fi

HOST="$1"
OUT_DIR="${2:-tests/fixtures/iqr23_${HOST//./_}/html}"
TIMEOUT="${TIMEOUT:-15}"

PAGES=(
  "index.html"
  "nastaveni.html"
  "teploty.html"
)

mkdir -p "$OUT_DIR"

echo "Downloading HTML from: $HOST"
echo "Output directory: $OUT_DIR"

for page in "${PAGES[@]}"; do
  url="http://${HOST}/${page}"
  out_file="${OUT_DIR}/${page}"

  echo "-> ${url}"
  http_code="$(curl -sS --compressed --connect-timeout "$TIMEOUT" --max-time "$TIMEOUT" -o "$out_file" -w "%{http_code}" "$url" || true)"

  if [[ "$http_code" != "200" ]]; then
    echo "   ERROR: HTTP ${http_code} for ${page}"
    rm -f "$out_file"
    continue
  fi

  if ! grep -qi "<html" "$out_file"; then
    echo "   ERROR: content does not look like HTML in ${page}"
    rm -f "$out_file"
    continue
  fi

  echo "   OK: saved to ${out_file}"
done

echo "Done."
