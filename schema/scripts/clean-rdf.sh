#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${DATA_DIR:-${SCRIPT_DIR}/../data/playground}"
DRY_RUN="${DRY_RUN:-0}"

if [ ! -d "$DATA_DIR" ]; then
  echo "❌ DATA_DIR does not exist: $DATA_DIR"
  exit 1
fi

echo "Cleaning generated RDF artifacts in: $DATA_DIR"
if [ "$DRY_RUN" = "1" ]; then
  echo "(dry-run) Would remove:"
  find "$DATA_DIR" -type f \( -name "*.ttl" -o -name "*.jsonld" \) -print
  exit 0
fi

count="$(find "$DATA_DIR" -type f \( -name "*.ttl" -o -name "*.jsonld" \) | wc -l | tr -d ' ')"
if [ "$count" = "0" ]; then
  echo "Nothing to clean."
  exit 0
fi

find "$DATA_DIR" -type f \( -name "*.ttl" -o -name "*.jsonld" \) -delete
echo "✅ Removed $count files."