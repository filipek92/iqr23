#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-10.6.2.20}"
OUT_DIR="${2:-tests/fixtures/iqr23_${HOST//./_}/html}"
TIMEOUT="${TIMEOUT:-15}"

PAGES=(
  "index.html"
  "nastaveni.html"
  "teploty.html"
)

mkdir -p "$OUT_DIR"

echo "Stahuji HTML ze zarizeni: $HOST"
echo "Vystupni slozka: $OUT_DIR"

for page in "${PAGES[@]}"; do
  url="http://${HOST}/${page}"
  out_file="${OUT_DIR}/${page}"

  echo "-> ${url}"
  http_code="$(curl -sS --compressed --connect-timeout "$TIMEOUT" --max-time "$TIMEOUT" -o "$out_file" -w "%{http_code}" "$url" || true)"

  if [[ "$http_code" != "200" ]]; then
    echo "   CHYBA: HTTP ${http_code} pro ${page}"
    rm -f "$out_file"
    continue
  fi

  if ! grep -qi "<html" "$out_file"; then
    echo "   CHYBA: Obsah nevypada jako HTML v ${page}"
    rm -f "$out_file"
    continue
  fi

  echo "   OK: ulozeno do ${out_file}"
done

echo "Hotovo."
