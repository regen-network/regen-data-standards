#!/bin/bash

# Configuration
FUSEKI_URL="http://localhost:3030"
DATASET_NAME="ds"

# Check if query file is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <query-file>"
    exit 1
fi

# Run the query
curl -X POST \
     -H "Accept: application/sparql-results+json" \
     -H "Content-Type: application/sparql-query" \
     --data-binary "@queries/$1.sparql" \
     "${FUSEKI_URL}/${DATASET_NAME}/sparql"