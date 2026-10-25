#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-10.6.2.20}"
OUT_DIR="${2:-tests/fixtures/iqr23_${HOST//./_}}"
TIMEOUT="${TIMEOUT:-15}"

ENDPOINTS=(
  "data.xml"
  "data_i_all.xml"
  "data_t_zas.xml"
  "data_n_txo.xml"
  "data_n_tix.xml"
)

mkdir -p "$OUT_DIR"

echo "Stahuji data ze zarizeni: $HOST"
echo "Vystupni slozka: $OUT_DIR"

for endpoint in "${ENDPOINTS[@]}"; do
  url="http://${HOST}/${endpoint}"
  out_file="${OUT_DIR}/${endpoint}"

  echo "-> ${url}"
  http_code="$(curl -sS --compressed --connect-timeout "$TIMEOUT" --max-time "$TIMEOUT" -o "$out_file" -w "%{http_code}" "$url" || true)"

  if [[ "$http_code" != "200" ]]; then
    echo "   CHYBA: HTTP ${http_code} pro ${endpoint}"
    rm -f "$out_file"
    continue
  fi

  if ! grep -q "<response" "$out_file"; then
    echo "   CHYBA: Neplatny XML obsah v ${endpoint}"
    rm -f "$out_file"
    continue
  fi

  echo "   OK: ulozeno do ${out_file}"
done

echo "Hotovo."
