#!/bin/bash
set -euo pipefail

# Root directory for data
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${DATA_DIR:-${SCRIPT_DIR}/../data/playground}"

# TARGET: OXIGRAPH (default) or FUSEKI
TARGET="${TARGET:-OXIGRAPH}"

if [ "$TARGET" = "FUSEKI" ]; then
    # ========================================================================
    # Fuseki target — upload to a named graph on Apache Jena Fuseki
    # ========================================================================

    # Required environment variables (no defaults — fail with clear error)
    if [ -z "${FUSEKI_GRAPH:-}" ]; then
        echo "ERROR: FUSEKI_GRAPH must be set when TARGET=FUSEKI (e.g., urn:regen:graph:standards)" && exit 1
    fi
    if [ -z "${FUSEKI_USER:-}" ] || [ -z "${FUSEKI_PASSWORD:-}" ]; then
        echo "ERROR: FUSEKI_USER and FUSEKI_PASSWORD must be set when TARGET=FUSEKI" && exit 1
    fi
    if [ -z "${FUSEKI_URL:-}" ] || [ -z "${FUSEKI_DATASET:-}" ]; then
        echo "ERROR: FUSEKI_URL and FUSEKI_DATASET must be set when TARGET=FUSEKI" && exit 1
    fi

    GRAPH_STORE_URL="${FUSEKI_URL}/${FUSEKI_DATASET}/data"
    AUTH="--user ${FUSEKI_USER}:${FUSEKI_PASSWORD}"
    # URL-encode graph parameter (safe for all URI formats including non-URN graphs)
    ENCODED_GRAPH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${FUSEKI_GRAPH}', safe=''))")
    GRAPH_QS="?graph=${ENCODED_GRAPH}"

    # Delete existing named graph content (safe: only affects this graph)
    echo "Deleting existing content in named graph: ${FUSEKI_GRAPH}"
    if ! curl -s -X DELETE -f $AUTH "${GRAPH_STORE_URL}${GRAPH_QS}" 2>/dev/null; then
        echo "Note: Named graph did not exist or was already empty (this is OK for first upload)"
    fi

    # Check for TTL files
    shopt -s nullglob
    ttl_files=("$DATA_DIR"/*/*.ttl)
    if [ ${#ttl_files[@]} -eq 0 ]; then
        echo "ERROR: No TTL files found in $DATA_DIR" && exit 1
    fi

    # POST each TTL file to append to the named graph
    failed_count=0
    total_count=0

    for file in "${ttl_files[@]}"; do
        ((total_count++))
        if ! curl -s -X POST -f \
            -H 'Content-Type: text/turtle' \
            -T "$file" \
            $AUTH \
            "${GRAPH_STORE_URL}${GRAPH_QS}"; then
            echo "❌ Failed to upload: $file"
            ((failed_count++))
        else
            echo "✅ Uploaded: $file"
        fi
    done

    echo "Fuseki upload complete: $((total_count - failed_count)) passed, $failed_count failed out of $total_count total files"
    echo "Named graph: ${FUSEKI_GRAPH}"
    [[ $failed_count -eq 0 ]] || exit 1

else
    # ========================================================================
    # Oxigraph target (default) — existing behavior preserved
    # ========================================================================

    # Only set default values if environment variables are not set
    : "${GRAPH_STORE_URL:=http://localhost:7878/store}"
    : "${GRAPH:=default}"

    # Build auth variable if GRAPH_STORE_AUTH is present.
    # GRAPH_STORE_AUTH should be in format user:pass
    if [ -n "${GRAPH_STORE_AUTH:-}" ]; then
        AUTH="--user $GRAPH_STORE_AUTH"
    else
        AUTH=""
    fi

    # Set METHOD and GRAPH_PARAM based on GRAPH value
    # Use POST to append to default graph, and PUT to replace named graphs
    if [ "$GRAPH" = "default" ]; then
        METHOD=POST
        GRAPH_PARAM="?default"
    else
        METHOD=PUT
        GRAPH_PARAM="?graph=$GRAPH"
    fi

    # First, clear the graph.
    if ! curl -s -X DELETE -f $AUTH "$GRAPH_STORE_URL$GRAPH_PARAM" ; then
        echo "❌ Failed to delete content in graph: $GRAPH"
    else
        echo "✅ Deleted content in graph: $GRAPH"
    fi

    # Use globbing to iterate through the nested structure
    shopt -s nullglob # Handle cases where no files match pattern

    # Initialize counters
    failed_count=0
    total_count=0

    # Loop through turtle files
    for file in "$DATA_DIR"/*/*.ttl; do
        ((total_count++))

        if ! curl -s -X $METHOD -f -H 'Content-Type: text/turtle' -T "$file" $AUTH "$GRAPH_STORE_URL$GRAPH_PARAM" ; then
          echo "❌ Failed to update graph: $GRAPH with $file"
            ((failed_count++))
        else
            echo "✅ Updated graph: $GRAPH with $file"
        fi
    done

    echo "Updating graph complete: $((total_count - failed_count)) passed, $failed_count failed out of $total_count total files"

    # Exit with failure if any validations failed
    [[ $failed_count -eq 0 ]] || exit 1
fi
