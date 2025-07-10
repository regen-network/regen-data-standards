#!/bin/bash

# Root directory for data
DATA_DIR="data/playground"

# Only set default values if environment variables are not set
: "${GRAPH_STORE_URL:=http://localhost:7878/store}"
: "${GRAPH:=default}"

# Set METHOD and GRAPH_PARAM based on GRAPH value
# Use POST to append to default graph, and PUT to replace named graphs
if [ "$GRAPH" = "default" ]; then
    METHOD=POST
    GRAPH_PARAM="?default"
else
    METHOD=PUT
    GRAPH_PARAM="?graph=$GRAPH"
fi

# Use globbing to iterate through the nested structure
shopt -s nullglob # Handle cases where no files match pattern

# Initialize counters
failed_count=0
total_count=0

# Loop through turtle files
for file in "$DATA_DIR"/*/*/*.ttl; do
    ((total_count++))

    if ! curl -X $METHOD -H 'Content-Type: text/turtle' -T "$file" "$GRAPH_STORE_URL$GRAPH_PARAM" ; then
      echo "❌ Failed to update graph: $GRAPH with $file"
        ((failed_count++))
    else
        echo "✅ Updated graph: $GRAPH with $file"
    fi
done

echo "Updating graph complete: $((total_count - failed_count)) passed, $failed_count failed out of $total_count total files"

# Exit with failure if any validations failed
[[ $failed_count -eq 0 ]] || exit 1