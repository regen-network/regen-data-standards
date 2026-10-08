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
- SHACL (gen-shacl) over the RDF graph of the authored JSON-LD and over the
  Turtle that gen-rdf publishes for the fixture, both parsed
  without rdflib's literal normalization so that lexical forms are checked as
  written (rdflib would otherwise rewrite an invalid Z in assertedAt as
  +00:00). One correction is applied to the generated shapes: gen-shacl adds
  sh:class to reference slots (a class range with an identifier, not inlined),
  but referenced IRIs are not typed in the data, so every valid claim would
  fail. The correction removes that sh:class and keeps sh:nodeKind sh:IRI.

Each example must be current, its JSON-LD graph isomorphic to the fixture's
published Turtle (run make gen-rdf first), and accepted by both validators.
Every examples/claim.INVALID-*.yaml document must be rejected by both: by JSON
Schema with the error named on its first line ("# expect: ..."), and by SHACL.

The examples are GenericClaims, whose shape is closed. The base Claim is
abstract, so its shape is open: it checks the base content of every claim type
and lets a claim type add fields. To check that, each example is also retyped
as a claim type defined outside this schema, with a field of its own and the
rdfs:subClassOf rfs:Claim triple that such a schema publishes with its data.
The Claim shape must accept it, and must reject it without assertedAt.
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
from rdflib.namespace import RDF, RDFS, SH
from linkml_runtime.utils.schemaview import SchemaView

SCHEMA = "src/schema.yaml"
CONTEXT_SOURCE = "src/Claim.yaml"
TARGET_CLASS = "GenericClaim"
EXAMPLES = {
    "data/playground/Claim/GenericClaim-001.yaml": "examples/generic-claim.jsonld",
    "data/playground/Claim/GenericClaim-002-revision.yaml": "examples/generic-claim-revision.jsonld",
}
INVALID_GLOB = "examples/claim.INVALID-*.yaml"
EXTENSION_CLASS = rdflib.URIRef("https://example.org/schema/ExtensionClaim")
EXTENSION_FIELD = rdflib.URIRef("https://example.org/schema/extensionField")

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


def lexical_graph(text, format):
    """Parse RDF keeping lexical forms as written (a Z stays Z, not +00:00)."""
    rdflib.NORMALIZE_LITERALS = False
    try:
        return rdflib.Graph().parse(data=text, format=format)
    finally:
        rdflib.NORMALIZE_LITERALS = True


def published_turtle(fixture):
    """Return the Turtle gen-rdf wrote for a fixture, which update-graph publishes."""
    path = Path(fixture).with_suffix(".ttl")
    if not path.exists():
        sys.exit(f"{path} is missing: run make gen-rdf")
    return path


def json_schema_check(document):
    """Validate an authored YAML document with JSON Schema (linkml-validate)."""
    result = run("linkml-validate", "-s", SCHEMA, "-C", TARGET_CLASS, document)
    return result.returncode == 0, result.stdout + result.stderr


def as_extension(view, graph, without=None):
    """Retype the claim as a claim type defined outside this schema, with a field of its own."""
    uri = lambda name: rdflib.URIRef(view.get_uri(view.get_element(name), expand=True))
    out = rdflib.Graph()
    for triple in graph:
        out.add(triple)
    root = next(out.subjects(RDF.type, uri(TARGET_CLASS)))
    out.remove((root, RDF.type, uri(TARGET_CLASS)))
    out.add((root, RDF.type, EXTENSION_CLASS))
    out.add((EXTENSION_CLASS, RDFS.subClassOf, uri("Claim")))
    out.add((root, EXTENSION_FIELD, rdflib.Literal("claim-type content")))
    if without:
        out.remove((root, uri(without), None))
    return out


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
        valid, output = json_schema_check(fixture)
        if valid:
            print(f"✅ {fixture}: conforms to JSON Schema")
        else:
            print(f"❌ {fixture}: JSON Schema violations\n{output}")
            failures += 1
        turtle = published_turtle(fixture)
        jsonld = rdflib.Graph().parse(data=text, format="json-ld")
        if isomorphic(jsonld, rdflib.Graph().parse(turtle, format="turtle")):
            print(f"✅ {example}: RDF matches {turtle}")
        else:
            print(f"❌ {example}: RDF differs from {turtle} (stale? run make gen-rdf)")
            failures += 1
        for document, graph in (
            (example, lexical_graph(text, "json-ld")),
            (turtle, lexical_graph(turtle.read_text(), "turtle")),
        ):
            conforms, messages = shacl_report(graph, shapes)
            if conforms:
                print(f"✅ {document}: conforms to SHACL")
            else:
                print(f"❌ {document}: SHACL violations {messages}")
                failures += 1
        graph = lexical_graph(text, "json-ld")
        conforms, messages = shacl_report(as_extension(view, graph), shapes)
        if conforms:
            print(f"✅ {example} as an outside claim type: conforms to the open Claim shape")
        else:
            print(f"❌ {example} as an outside claim type: SHACL violations {messages}")
            failures += 1
        conforms, _ = shacl_report(as_extension(view, graph, without="assertedAt"), shapes)
        if not conforms:
            print(f"✅ {example} as an outside claim type without assertedAt: the Claim shape rejects it")
        else:
            print(f"❌ {example} as an outside claim type without assertedAt: SHACL accepts it")
            failures += 1

    for invalid in sorted(glob.glob(INVALID_GLOB)):
        first_line = Path(invalid).read_text().splitlines()[0]
        expected = first_line.removeprefix("# expect:").strip()
        valid, output = json_schema_check(invalid)
        if not valid and expected in output:
            print(f"✅ {invalid}: JSON Schema rejects it ({expected})")
        else:
            print(f"❌ {invalid}: expected JSON Schema rejection with '{expected}'\n{output}")
            failures += 1
        conforms, messages = shacl_report(lexical_graph(build(view, context, invalid), "json-ld"), shapes)
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
