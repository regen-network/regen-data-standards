#!/bin/bash

# Configuration
FUSEKI_URL="http://localhost:3030"
DATASET_NAME="ds"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <file> <graph=default>"
    exit 1
fi

file=$1
graph=$2
if [ $# -ne 2 ]; then
  graph="default"
fi

# Default graph
echo "Loading $file to $graph"
if [ "$graph" = "default" ]; then
    curl -X POST \
         -H "Content-Type: application/ld+json" \
         --data-binary "@$file" \
         "${FUSEKI_URL}/${DATASET_NAME}/data"
else
    curl -X POST \
         -H "Content-Type: application/ld+json" \
         --data-binary "@$file" \
         "${FUSEKI_URL}/${DATASET_NAME}/data?graph=${graph}"
fi

echo "Loading complete!"