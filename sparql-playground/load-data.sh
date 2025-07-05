#!/bin/bash

# Configuration
FUSEKI_URL="http://localhost:3030"
DATASET_NAME="ds"

process_file() {
    local file="$1"
    local dir=$(dirname "$file")
    local base_dir=$(basename "$dir")
    local graph

    # If parent directory is 'default', use default graph
    if [ "$base_dir" = "default" ]; then
        graph="default"
        curl -X POST \
             -H "Content-Type: application/ld+json" \
             --data-binary "@$file" \
             "${FUSEKI_URL}/${DATASET_NAME}/data"
    else
        # Use parent directory name as graph name
        graph=$base_dir
        curl -X POST \
             -H "Content-Type: application/ld+json" \
             --data-binary "@$file" \
             "${FUSEKI_URL}/${DATASET_NAME}/data?graph=${base_dir}"
    fi

    # Check the HTTP status code
    if [ $? -eq 0 ]; then
        echo "Successfully loaded $file into $graph"
    else
        echo "Failed to load $file"
    fi
}

# Allow specifying a single graph dir to load.
graph_dir="*"
if [ $1 ]; then
    graph_dir=$1
fi

# Load all .jsonld files graph directories.
echo "Loading data/$graph_dir/*.jsonld files..."
for file in data/$graph_dir/*.jsonld; do
    [[ -e "$file" ]] || continue
    process_file "$file"
done

echo "Loading complete!"