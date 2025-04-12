#!/usr/bin/env python3

import sys
from pathlib import Path
from rdflib import Graph
from linkml.utils.datautils import get_loader, get_dumper
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin, RecommendedSlotsPlugin
from linkml_runtime.utils.schemaview import SchemaView
from linkml.generators.pythongen import PythonGenerator
import os

def validate_file(jsonld_file):
    print(f"Validating file: {jsonld_file}")

    # Load the schema using LinkML
    schema_path = "src/schema.yaml"
    schemaview = SchemaView(schema_path)

    # Determine the target class based on the file name
    file_name = os.path.basename(jsonld_file)
    if file_name.startswith("C"):
        target_class_name = 'CarbonCreditClassInfo'
    else:
        target_class_name = 'CreditClassInfo'

    python_module = PythonGenerator(schema_path).compile_module()
    target_class = python_module.__dict__[target_class_name]


    prefix_dict = {"rfs": "https://framework.regen.network/schema/","rft": "https://framework.regen.network/taxonomy/","schema": "http://schema.org/"}

    rdf_loader = get_loader("rdf")
    obj = rdf_loader.load(source=str(jsonld_file), target_class=target_class, schemaview=schemaview, fmt="json-ld", prefix_map=prefix_dict)


    print("Loaded object, now performing validation")
    # Validate the YAML object using LinkML
    # SOMETHING IS STRANGE HERE -- not sure what's going on but getting errors when running the Jsonscheam validation plugin
    validator = Validator(schema_path,
                          validation_plugins=[JsonschemaValidationPlugin(), RecommendedSlotsPlugin()])
    validation_result = validator.validate(obj, target_class=target_class_name)

    if validation_result:
        for result in validation_result.results:
            if result.severity == "ERROR":
                print(f"Error: {result.message}")
            elif result.severity == "WARNING":
                print(f"Warning: {result.message}")
            else:
                print(f"Info: {result.message}")
    else:
        print(f"Validation failed for file: {jsonld_file}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-jsonld-file-or-directory>")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"Error: Path '{input_path}' does not exist.")
        sys.exit(1)

    if input_path.is_file():
        # If a single file is provided, validate it
        validate_file(input_path)
    elif input_path.is_dir():
        # If a directory is provided, loop through all files and validate each
        for file in input_path.iterdir():
            if file.is_file():
                validate_file(file)
    else:
        print(f"Error: '{input_path}' is neither a file nor a directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
