#!/bin/bash

# Root directory for data
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${DATA_DIR:-${SCRIPT_DIR}/../data/playground}"

# Only set default values if environment variables are not set
: "${GRAPH_STORE_URL:=http://localhost:7878/store}"
: "${GRAPH:=default}"

# Build auth variable if GRAPH_STORE_AUTH is present.
# GRAPH_STORE_AUTH should be in format user:pass
if [ -n "$GRAPH_STORE_AUTH" ]; then
    AUTH="--user $GRAPH_STORE_AUTH"
else
    AUTH=""
fi

# Clear the graph once, then POST every file, which appends to it. PUT would
# replace the graph's content with each file, so only the last file would
# remain (SPARQL 1.1 Graph Store Protocol).
METHOD=POST
if [ "$GRAPH" = "default" ]; then
    GRAPH_PARAM="?default"
else
    GRAPH_PARAM="?graph=$GRAPH"
fi

# First, clear the graph. Stop if it may still hold old triples: uploading
# would leave them beside the new data. 404 means the graph does not exist
# yet, so it is empty.
status=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE $AUTH "$GRAPH_STORE_URL$GRAPH_PARAM")
case "$status" in
    200|204) echo "✅ Deleted content in graph: $GRAPH" ;;
    404) echo "✅ Graph $GRAPH does not exist yet; nothing to delete" ;;
    *)
        echo "❌ Failed to delete content in graph: $GRAPH (HTTP $status); nothing uploaded"
        exit 1
        ;;
esac

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