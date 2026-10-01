#!/usr/bin/env python3
"""Generate and check the Claim, Attestation and C06 claim JSON-LD examples.

    python3 scripts/claim-examples.py generate   # rewrite examples/*.jsonld
    python3 scripts/claim-examples.py check      # fail if anything is stale or wrong

Run from the schema/ directory. Each example is built from a playground
fixture (validated by gen-rdf in CI) plus an inline JSON-LD context generated
from the module that defines the example's class (src/Claim.yaml for Claim,
src/C06Claim.yaml for the C06 classes, and so on) with --xsd-anyuri-as-iri, so that uri- and
uriorcurie-valued terms, such as wasRevisionOf, map to "@type": "@id" (an IRI
node, as in the Turtle output) instead of an xsd:anyURI literal. Two
corrections are applied to the generated context, because this LinkML
version's JSON-LD output does not produce the same RDF as its Turtle output:

- enum-valued terms get "@type": "@vocab" and a scoped context mapping each
  permissible value to its `meaning`, so "COMMUNITY" expands to rfs:Community
  instead of a string literal. A slot whose range a class narrows to an enum
  (slot_usage) is mapped the same way;
- nested inlined objects get an explicit "@type", as in the Turtle output.

The check validates every document with both validators the schema generates:

- JSON Schema (linkml-validate) over the authored YAML;
- SHACL (gen-shacl, closed shapes) over the RDF graph of the authored JSON-LD,
  parsed without rdflib's literal normalization so that lexical forms, such as
  the Z suffix of assertedAt, are checked as written. The generated shapes are
  used unchanged.

Each example must be current, its JSON-LD graph isomorphic to the fixture's
Turtle output, and accepted by both validators. The class of a fixture is the
part of its file name before the first "-", as in gen-rdf. Every
examples/*.INVALID-*.yaml document must be rejected by both validators: by JSON
Schema with the error named on its first line ("# expect: ..."), and by SHACL.
Its class is named on a "# class: ..." line, and is Claim when there is none.

The generic examples are GenericClaims, whose shape is closed. The base Claim
is abstract, so its shape is open: it checks the base content of every claim
type and lets a claim type add fields. To check that, each GenericClaim example
is also retyped as a claim type defined outside this schema, with a field of its
own and the rdfs:subClassOf rfs:Claim triple that such a schema publishes with
its data. The Claim shape must accept it, and must reject it without assertedBy.
Each example's JSON-LD graph must also be isomorphic to the Turtle that gen-rdf
publishes for its fixture (run make gen-rdf first), and both are checked with
SHACL, parsed without rdflib's literal normalization.
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
# The module that defines each class: its JSON-LD context and SHACL shapes are
# generated from that module and its imports.
MODULES = {
    "GenericClaim": "src/Claim.yaml",
    "Attestation": "src/Attestation.yaml",
    "RegistryReviewAttestation": "src/RegistryReviewAttestation.yaml",
    "C06ProjectClaim": "src/C06Claim.yaml",
    "C06CohortClaim": "src/C06Claim.yaml",
    "C06SiteClaim": "src/C06Claim.yaml",
    "C06PlotClaim": "src/C06Claim.yaml",
    "C06ProjectStatementClaim": "src/C06Claim.yaml",
}
EXAMPLES = {
    "data/playground/Claim/GenericClaim-001.yaml": "examples/generic-claim.jsonld",
    "data/playground/Claim/GenericClaim-002-revision.yaml": "examples/generic-claim-revision.jsonld",
    "data/playground/C06SiteClaim/C06SiteClaim-mvp-001.yaml": "examples/c06-mvp-claim.jsonld",
    "data/playground/RegistryReviewAttestation/RegistryReviewAttestation-confirmation-001.yaml": "examples/registry-review-attestation.jsonld",
}
INVALID_GLOB = "examples/*.INVALID-*.yaml"
EXTENSION_CLASS = rdflib.URIRef("https://example.org/schema/ExtensionClaim")
EXTENSION_FIELD = rdflib.URIRef("https://example.org/schema/extensionField")

# Ill-typed literals in the invalid examples are expected; they are reported
# by the validators, not as parser warnings.
logging.getLogger("rdflib.term").setLevel(logging.ERROR)


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def enum_ranges(view):
    """Yield (slot name, enum) for every slot whose range is an enum, including
    a range a class narrows with slot_usage."""
    for slot in view.all_slots().values():
        if slot.range and view.get_enum(slot.range):
            yield slot.name, view.get_enum(slot.range)
    for class_name in view.all_classes():
        for slot in view.class_induced_slots(class_name):
            if slot.range and view.get_enum(slot.range):
                yield slot.name, view.get_enum(slot.range)


def inline_context(view, source):
    result = run("gen-jsonld-context", "--xsd-anyuri-as-iri", source)
    if result.returncode != 0:
        sys.exit(result.stderr)
    context = json.loads(result.stdout)["@context"]
    for name, enum in enum_ranges(view):
        if name not in context:
            continue
        term = context[name]
        context[name] = {
            "@id": term["@id"] if isinstance(term, dict) else term,
            "@type": "@vocab",
            "@context": {
                text: pv.meaning for text, pv in enum.permissible_values.items()
            },
        }
    return context


def shacl_shapes(source):
    result = run("gen-shacl", source)
    if result.returncode != 0:
        sys.exit(result.stderr)
    return rdflib.Graph().parse(data=result.stdout, format="turtle")


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


def build(module, class_name, source):
    data = yaml.safe_load(Path(source).read_text())
    document = {"@context": module["context"], **typed(module["view"], class_name, data)}
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


def json_schema_check(document, class_name):
    """Validate an authored YAML document with JSON Schema (linkml-validate)."""
    result = run("linkml-validate", "-s", SCHEMA, "-C", class_name, document)
    return result.returncode == 0, result.stdout + result.stderr


def as_extension(view, graph, class_name, without=None):
    """Retype the claim as a claim type defined outside this schema, with a field of its own."""
    uri = lambda name: rdflib.URIRef(view.get_uri(view.get_element(name), expand=True))
    out = rdflib.Graph()
    for triple in graph:
        out.add(triple)
    root = next(out.subjects(RDF.type, uri(class_name)))
    out.remove((root, RDF.type, uri(class_name)))
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


def fixture_class(fixture):
    return Path(fixture).name.split("-", 1)[0]


def invalid_class(text):
    for line in text.splitlines():
        if line.startswith("# class:"):
            return line.removeprefix("# class:").strip()
    return "GenericClaim"


def main(mode):
    modules = {}

    def module_for(class_name):
        source = MODULES[class_name]
        if source not in modules:
            view = SchemaView(source)
            modules[source] = {
                "view": view,
                "context": inline_context(view, source),
                "shapes": shacl_shapes(source),
            }
        return modules[source]

    failures = 0

    for fixture, example in EXAMPLES.items():
        class_name = fixture_class(fixture)
        module = module_for(class_name)
        text = build(module, class_name, fixture)
        if mode == "generate":
            Path(example).write_text(text)
        elif not Path(example).exists() or Path(example).read_text() != text:
            print(f"❌ {example} is stale: run make gen-claim-examples")
            failures += 1
            continue
        valid, output = json_schema_check(fixture, class_name)
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
            conforms, messages = shacl_report(graph, module["shapes"])
            if conforms:
                print(f"✅ {document}: conforms to SHACL")
            else:
                print(f"❌ {document}: SHACL violations {messages}")
                failures += 1
        if class_name == "GenericClaim":
            graph = lexical_graph(text, "json-ld")
            conforms, messages = shacl_report(as_extension(module["view"], graph, class_name), module["shapes"])
            if conforms:
                print(f"✅ {example} as an outside claim type: conforms to the open Claim shape")
            else:
                print(f"❌ {example} as an outside claim type: SHACL violations {messages}")
                failures += 1
            conforms, _ = shacl_report(as_extension(module["view"], graph, class_name, without="assertedBy"), module["shapes"])
            if not conforms:
                print(f"✅ {example} as an outside claim type without assertedBy: the Claim shape rejects it")
            else:
                print(f"❌ {example} as an outside claim type without assertedBy: SHACL accepts it")
                failures += 1

    for invalid in sorted(glob.glob(INVALID_GLOB)):
        content = Path(invalid).read_text()
        expected = content.splitlines()[0].removeprefix("# expect:").strip()
        class_name = invalid_class(content)
        module = module_for(class_name)
        valid, output = json_schema_check(invalid, class_name)
        if not valid and expected in output:
            print(f"✅ {invalid}: JSON Schema rejects it ({expected})")
        else:
            print(f"❌ {invalid}: expected JSON Schema rejection with '{expected}'\n{output}")
            failures += 1
        graph = lexical_graph(build(module, class_name, invalid), "json-ld")
        conforms, messages = shacl_report(graph, module["shapes"])
        if not conforms:
            print(f"✅ {invalid}: SHACL rejects it ({messages[0][:80]})")
        else:
            print(f"❌ {invalid}: SHACL accepts it")
            failures += 1

    if failures:
        sys.exit(f"{failures} example check(s) failed")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("generate", "check"):
        sys.exit(__doc__)
    main(sys.argv[1])
