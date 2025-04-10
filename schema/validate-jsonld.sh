#!/bin/bash

set -euo pipefail

# Check if a JSON-LD file is provided as an argument
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <path-to-jsonld-file>"
    exit 1
fi

JSONLD_FILE="$1"

# Validate that the provided file exists
if [[ ! -f "$JSONLD_FILE" ]]; then
    echo "Error: File '$JSONLD_FILE' does not exist."
    exit 1
fi

# Create a temporary file for the .ttl and .yaml output
TEMP_DIR=$(mktemp -d)
TEMP_TTL="$TEMP_DIR/temp.ttl"
TEMP_YAML="$TEMP_DIR/temp.yaml"

# Convert JSON-LD to TTL
python -m rdflib.tools.rdfpipe "$JSONLD_FILE" > "$TEMP_TTL"

# Convert TTL to YAML using the schema
linkml-convert -s src/schema.yaml -C CreditClassInfo -o "$TEMP_YAML" "$TEMP_TTL"

# Validate the YAML file
linkml-validate -s src/schema.yaml -C CreditClassInfo "$TEMP_YAML"