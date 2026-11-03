#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <host> [output_dir]" >&2
  exit 1
fi

HOST="$1"
OUT_DIR="${2:-tests/fixtures/iqr23_${HOST//./_}}"
TIMEOUT="${TIMEOUT:-15}"

ENDPOINTS=(
  "data.xml"
  "data_i_all.xml"
  "data_t_zas.xml"
  "data_n_txo.xml"
  "data_n_tix.xml"
  "data_t_ek1.xml"
  "data_t_ek2.xml"
  "data_t_krb.xml"
  "data_t_sol.xml"
  "data_t_baz.xml"
  "data_t_chl.xml"
)

mkdir -p "$OUT_DIR"

echo "Downloading data from: $HOST"
echo "Output directory: $OUT_DIR"

for endpoint in "${ENDPOINTS[@]}"; do
  url="http://${HOST}/${endpoint}"
  out_file="${OUT_DIR}/${endpoint}"

  echo "-> ${url}"
  http_code="$(curl -sS --compressed --connect-timeout "$TIMEOUT" --max-time "$TIMEOUT" -o "$out_file" -w "%{http_code}" "$url" || true)"

  if [[ "$http_code" != "200" ]]; then
    echo "   ERROR: HTTP ${http_code} for ${endpoint}"
    rm -f "$out_file"
    continue
  fi

  if ! grep -q "<response" "$out_file"; then
    echo "   ERROR: invalid XML content in ${endpoint}"
    rm -f "$out_file"
    continue
  fi

  echo "   OK: saved to ${out_file}"
done

echo "Done."
