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

        # Validate the file as authored. linkml-convert --validate would check
        # LinkML's re-serialized objects instead, which rewrite some values
        # (a datetime's Z suffix becomes +00:00) before validating.
        target_class="$(basename "$yaml_file")"
        target_class="${target_class%%-*}"
        if ! linkml-validate -s "$SCHEMA_PATH" -C "$target_class" "$yaml_file" ; then
            echo "❌ Validation failed for: $yaml_file (TTL conversion skipped)"
            ((total_count++))
            ((failed_count++))
            continue
        fi

        # Create output filename by replacing .yaml extension with .ttl
        output_file="${yaml_file%.yaml}.ttl"
        ((total_count++))
        if ! linkml-convert -s "$SCHEMA_PATH" --no-validate --input-format yaml --output-format ttl --target-class-from-path --output "$output_file" "$yaml_file" ; then
            echo "❌ TTL conversion failed for: $yaml_file"
            ((failed_count++))
        else
            echo "✅ TTL conversion passed for: $yaml_file"
        fi
    done
done

echo "TTL conversion complete: $((total_count - failed_count)) passed, $failed_count failed out of $total_count total files"
[[ $failed_count -eq 0 ]] || exit 1

# JSON-LD is built with the published context of the current schema version
# (linkml-convert's own context writes IRIs as xsd:anyURI literals), and must
# give the same graph as the Turtle.
cd "${SCRIPT_DIR}/.." && python3 scripts/claim-examples.py playground