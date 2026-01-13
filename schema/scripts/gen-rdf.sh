#!/bin/bash

# Root directory for data
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Root directory for data (overrideable)
DATA_DIR="${DATA_DIR:-${SCRIPT_DIR}/../data/playground}"
SCHEMA_PATH="${SCHEMA_PATH:-${SCRIPT_DIR}/../src/schema.yaml}"

# Use globbing to iterate through the nested structure
shopt -s nullglob # Handle cases where no files match pattern

# Initialize counters
failed_count=0
total_count=0

# Loop through nested directories of linkml classes
for linkml_class_dir in "$DATA_DIR"/*/; do
    echo "Processing directory: $linkml_class_dir"

    # Convert yaml files to RDF using linkml class schema
    for yaml_file in "$linkml_class_dir"*.yaml; do

        ((total_count++))
        # Create output filename by replacing .yaml extension with .jsonld
        output_file="${yaml_file%.yaml}.jsonld"
        if ! linkml-convert -s "$SCHEMA_PATH" --validate --input-format yaml --output-format json-ld --target-class-from-path --output "$output_file" "$yaml_file" ; then
            echo "❌ JSON-LD conversion failed for: $yaml_file"
            ((failed_count++))
        else
            echo "✅ JSON-LD conversion passed for: $yaml_file"
        fi

        # Create output filename by replacing .yaml extension with .ttl
        output_file="${yaml_file%.yaml}.ttl"
        ((total_count++))
        if ! linkml-convert -s "$SCHEMA_PATH" --validate --input-format yaml --output-format ttl --target-class-from-path --output "$output_file" "$yaml_file" ; then
            echo "❌ TTL conversion failed for: $yaml_file"
            ((failed_count++))
        else
            echo "✅ TTL conversion passed for: $yaml_file"
        fi
    done
done

echo "RDF conversion complete: $((total_count - failed_count)) passed, $failed_count failed out of $total_count total files"

# Exit with failure if any validations failed
[[ $failed_count -eq 0 ]] || exit 1