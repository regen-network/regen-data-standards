#!/usr/bin/env python3
"""Preserve OutputRecord's nested model types with the pinned LinkML JSON dumper."""

import argparse
from copy import copy
from pathlib import Path

from jsonasobj2 import items
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.pythongen import PythonGenerator
from linkml.utils.validation import validate_object
from linkml_runtime.dumpers import json_dumper
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.utils.yamlutils import YAMLRoot


def with_node_types(value):
    """Copy typed model nodes; leave enum/scalar serialization to LinkML.

    linkml-runtime 1.9.5 injects @type only on the root. Using each already-loaded
    model class's URI also makes its nested objects explicit RDF class instances.
    No identifier, slot value, context mapping, or schema range is changed here.
    """
    if isinstance(value, YAMLRoot):
        class_uri = getattr(value, "class_class_uri", None)
        if class_uri is None:
            return value  # Enums are YAMLRoot too, but serialize as scalar values.
        result = copy(value)
        for key, nested in items(value):
            result[key] = with_node_types(nested)
        result["@type"] = str(class_uri)
        return result
    if isinstance(value, list):
        return [with_node_types(nested) for nested in value]
    if isinstance(value, dict):
        return {key: with_node_types(nested) for key, nested in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    if args.input.name.split("-")[0] != "OutputRecord":
        parser.error("this compatibility shim is scoped to OutputRecord-*.yaml")

    module = PythonGenerator(args.schema).compile_module()
    record = yaml_loader.load(str(args.input), target_class=module.OutputRecord)
    validate_object(record, args.schema)
    context = ContextGenerator(args.schema).serialize()
    # The ordinary dumper still handles root type, enum values, dates, numbers,
    # omitted empty fields and the generated context exactly as linkml-convert.
    output = json_dumper.dumps(with_node_types(record), contexts=[context])
    args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
