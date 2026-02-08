#!/bin/bash
set -euo pipefail

# Upload LinkML-generated OWL ontology to Fuseki as a named graph.
# Uses gen-owl to convert schema.yaml → TTL, then PUT to replace the ontology graph.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_DIR="${SCRIPT_DIR}/.."
GENERATED_DIR="${SCHEMA_DIR}/generated"

# Required environment variables (no defaults)
if [ -z "${FUSEKI_GRAPH:-}" ]; then
    echo "ERROR: FUSEKI_GRAPH must be set (e.g., urn:regen:graph:ontology)" && exit 1
fi
if [ -z "${FUSEKI_USER:-}" ] || [ -z "${FUSEKI_PASSWORD:-}" ]; then
    echo "ERROR: FUSEKI_USER and FUSEKI_PASSWORD must be set" && exit 1
fi
if [ -z "${FUSEKI_URL:-}" ] || [ -z "${FUSEKI_DATASET:-}" ]; then
    echo "ERROR: FUSEKI_URL and FUSEKI_DATASET must be set" && exit 1
fi

# Generate OWL ontology from LinkML schema
mkdir -p "$GENERATED_DIR"
echo "Generating OWL ontology from schema.yaml..."
gen-owl "${SCHEMA_DIR}/src/schema.yaml" > "${GENERATED_DIR}/regen-ontology.ttl"

if [ ! -s "${GENERATED_DIR}/regen-ontology.ttl" ]; then
    echo "ERROR: gen-owl produced empty output" && exit 1
fi

GRAPH_STORE_URL="${FUSEKI_URL}/${FUSEKI_DATASET}/data"
ENCODED_GRAPH=$(python3 -c "import urllib.parse, os; print(urllib.parse.quote(os.environ['FUSEKI_GRAPH'], safe=''))")

echo "Uploading ontology to Fuseki named graph: ${FUSEKI_GRAPH}"
# PUT replaces the entire named graph (correct for single-file full replacement)
curl -s -X PUT -f \
    -H 'Content-Type: text/turtle' \
    -T "${GENERATED_DIR}/regen-ontology.ttl" \
    --user "${FUSEKI_USER}:${FUSEKI_PASSWORD}" \
    "${GRAPH_STORE_URL}?graph=${ENCODED_GRAPH}"

echo "✅ Ontology uploaded to ${FUSEKI_GRAPH}"
