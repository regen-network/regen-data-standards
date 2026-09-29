#!/usr/bin/env python3
"""Generate and check the base Claim JSON-LD examples.

    python3 scripts/claim-examples.py generate   # rewrite examples/*.jsonld
    python3 scripts/claim-examples.py check      # fail if anything is stale or wrong

Run from the schema/ directory. Each example is built from a playground
fixture (validated by gen-rdf in CI) plus an inline JSON-LD context generated
from src/Claim.yaml. Two corrections are applied to the generated context,
because this LinkML version's JSON-LD output does not produce the same RDF as
its Turtle output:

- enum-valued terms get "@type": "@vocab" and a scoped context mapping each
  permissible value to its `meaning`, so "ECOLOGICAL" expands to rft:Ecological
  instead of a string literal;
- nested inlined objects get an explicit "@type", as in the Turtle output.

The check validates every document with both validators the schema generates:

- JSON Schema (linkml-validate) over the authored YAML;
- SHACL (gen-shacl, closed shapes) over the RDF graph of the authored JSON-LD,
  parsed without rdflib's literal normalization so that lexical forms, such as
  the Z suffix of assertedAt, are checked as written. One correction is applied
  to the generated shapes: gen-shacl adds sh:class to reference slots (a class
  range with an identifier, not inlined), but referenced IRIs are not typed in
  the data, so every valid claim would fail. The correction removes that
  sh:class and keeps sh:nodeKind sh:IRI.

Each example must be current, its JSON-LD graph isomorphic to the fixture's
Turtle output, and accepted by both validators. Every
examples/claim.INVALID-*.yaml document must be rejected by both: by JSON Schema
with the error named on its first line ("# expect: ..."), and by SHACL.
"""

import glob
import json
import logging
import subprocess
import sys
from pathlib import Path

import rdflib
import yaml
from pyshacl import validate as shacl_validate
from rdflib.compare import isomorphic
from rdflib.namespace import SH
from linkml_runtime.utils.schemaview import SchemaView

SCHEMA = "src/schema.yaml"
CONTEXT_SOURCE = "src/Claim.yaml"
TARGET_CLASS = "Claim"
EXAMPLES = {
    "data/playground/Claim/Claim-generic-001.yaml": "examples/generic-claim.jsonld",
    "data/playground/Claim/Claim-generic-002-revision.yaml": "examples/generic-claim-revision.jsonld",
}
INVALID_GLOB = "examples/claim.INVALID-*.yaml"

# Ill-typed literals in the invalid examples are expected; they are reported
# by the validators, not as parser warnings.
logging.getLogger("rdflib.term").setLevel(logging.ERROR)


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def inline_context(view):
    result = run("gen-jsonld-context", CONTEXT_SOURCE)
    if result.returncode != 0:
        sys.exit(result.stderr)
    context = json.loads(result.stdout)["@context"]
    for slot in view.all_slots().values():
        enum = view.get_enum(slot.range) if slot.range else None
        if enum is None or slot.name not in context:
            continue
        context[slot.name] = {
            "@id": context[slot.name]["@id"],
            "@type": "@vocab",
            "@context": {
                text: pv.meaning for text, pv in enum.permissible_values.items()
            },
        }
    return context


def shacl_shapes(view):
    result = run("gen-shacl", CONTEXT_SOURCE)
    if result.returncode != 0:
        sys.exit(result.stderr)
    shapes = rdflib.Graph().parse(data=result.stdout, format="turtle")
    for class_name in view.all_classes():
        for slot in view.class_induced_slots(class_name):
            if (
                slot.range in view.all_classes()
                and view.get_identifier_slot(slot.range) is not None
                and not slot.inlined
            ):
                path = rdflib.URIRef(view.get_uri(slot, expand=True))
                for prop in shapes.subjects(SH.path, path):
                    shapes.remove((prop, SH["class"], None))
    return shapes


def typed(view, class_name, data):
    """Return data with "@type" on this object and on nested inlined objects."""
    out = {"@type": class_name}
    for key, value in data.items():
        try:
            slot = view.induced_slot(key, class_name)
        except ValueError:
            slot = None  # not in the schema: kept, so validation can reject it
        if slot is not None and slot.range in view.all_classes() and slot.inlined:
            # Non-objects (such as a bare IRI) are kept as written, so
            # validation can reject them.
            if isinstance(value, list):
                value = [typed(view, slot.range, v) if isinstance(v, dict) else v for v in value]
            elif isinstance(value, dict):
                value = typed(view, slot.range, value)
        out[key] = value
    return out


def build(view, context, source):
    data = yaml.safe_load(Path(source).read_text())
    document = {"@context": context, **typed(view, TARGET_CLASS, data)}
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def authored_graph(jsonld_text):
    """Parse JSON-LD keeping lexical forms as written (no Z -> +00:00)."""
    rdflib.NORMALIZE_LITERALS = False
    try:
        return rdflib.Graph().parse(data=jsonld_text, format="json-ld")
    finally:
        rdflib.NORMALIZE_LITERALS = True


def turtle_graph(fixture):
    result = run(
        "linkml-convert", "-s", SCHEMA, "-C", TARGET_CLASS, "--validate",
        "-f", "yaml", "-t", "ttl", fixture,
    )
    if result.returncode != 0:
        sys.exit(f"{fixture}: conversion failed\n{result.stderr}")
    return rdflib.Graph().parse(data=result.stdout, format="turtle")


def shacl_report(graph, shapes):
    conforms, results, _ = shacl_validate(graph, shacl_graph=shapes)
    messages = [str(m) for m in results.objects(None, SH.resultMessage)]
    return conforms, messages


def main(mode):
    view = SchemaView(CONTEXT_SOURCE)
    context = inline_context(view)
    shapes = shacl_shapes(view)
    failures = 0

    for fixture, example in EXAMPLES.items():
        text = build(view, context, fixture)
        if mode == "generate":
            Path(example).write_text(text)
        elif not Path(example).exists() or Path(example).read_text() != text:
            print(f"❌ {example} is stale: run make gen-claim-examples")
            failures += 1
            continue
        jsonld = rdflib.Graph().parse(data=text, format="json-ld")
        if isomorphic(jsonld, turtle_graph(fixture)):
            print(f"✅ {example}: RDF matches {fixture}")
        else:
            print(f"❌ {example}: RDF differs from the Turtle output of {fixture}")
            failures += 1
        conforms, messages = shacl_report(authored_graph(text), shapes)
        if conforms:
            print(f"✅ {example}: conforms to SHACL")
        else:
            print(f"❌ {example}: SHACL violations {messages}")
            failures += 1

    for invalid in sorted(glob.glob(INVALID_GLOB)):
        first_line = Path(invalid).read_text().splitlines()[0]
        expected = first_line.removeprefix("# expect:").strip()
        result = run("linkml-validate", "-s", SCHEMA, "-C", TARGET_CLASS, invalid)
        output = result.stdout + result.stderr
        if result.returncode != 0 and expected in output:
            print(f"✅ {invalid}: JSON Schema rejects it ({expected})")
        else:
            print(f"❌ {invalid}: expected JSON Schema rejection with '{expected}'\n{output}")
            failures += 1
        conforms, messages = shacl_report(authored_graph(build(view, context, invalid)), shapes)
        if not conforms:
            print(f"✅ {invalid}: SHACL rejects it ({messages[0][:80]})")
        else:
            print(f"❌ {invalid}: SHACL accepts it")
            failures += 1

    if failures:
        sys.exit(f"{failures} Claim example check(s) failed")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("generate", "check"):
        sys.exit(__doc__)
    main(sys.argv[1])
