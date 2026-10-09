#!/usr/bin/env python3
"""Generate and check the Claim, Evaluation and C06 claim JSON-LD examples.

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
- nested inlined objects get an explicit "@type", as in the Turtle output. A
  selector's "@type" is the class its selectorType names (oa:FragmentSelector
  or oa:TextQuoteSelector), which then replaces selectorType.

The check validates every document with both validators the schema generates:

- JSON Schema (linkml-validate) over the authored YAML;
- SHACL (gen-shacl, closed shapes) over the RDF graph of the authored JSON-LD,
  parsed without rdflib's literal normalization so that lexical forms, such as
  the Z suffix of assertedAt, are checked as written. The generated shapes are
  used unchanged. Claims and evaluations reference Evidence records by IRI,
  and the shapes require each to be an rfs:Evidence, so each of them is
  checked together with the Turtle gen-rdf wrote for the Evidence fixtures, as
  the graph store holds them. An Evidence record references no other record
  and is checked on its own.

Each example must be current, its JSON-LD graph isomorphic to the fixture's
Turtle output, and accepted by both validators. The class of a fixture is the
part of its file name before the first "-", as in gen-rdf. Every
examples/*.INVALID-*.yaml document must be rejected by both validators: by JSON
Schema with the error named on its first line ("# expect: ..."), and by SHACL.
Its class is named on a "# class: ..." line, and is Claim when there is none.
A document that breaks a LinkML rule carries a "# shacl: not enforced" line:
the generated SHACL does not express rules, so only JSON Schema must reject it,
and the check reports that SHACL accepts it. The line may give another reason
in parentheses. A document marked "# graph: with the Evidence records" is valid
on its own ("# expect: accepted alone"), and SHACL must reject it merged with
the Evidence records, as the graph store merges it.

For each example with citations, the check also changes a selector and
requires that the cited Evidence IRIs and the Evidence records stay the same,
while the citing document's graph changes.

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
    "Evidence": "src/Evidence.yaml",
    "Evaluation": "src/Evaluation.yaml",
    "EvidenceEvaluation": "src/Evaluation.yaml",
    "ClaimConsistencyEvaluation": "src/Evaluation.yaml",
    "RegistryReviewEvaluation": "src/RegistryReviewEvaluation.yaml",
    "RegistryRequirementEvaluation": "src/RegistryReviewEvaluation.yaml",
    "RegistryFindingEvaluation": "src/RegistryReviewEvaluation.yaml",
    "RegistryReportEvaluation": "src/RegistryReviewEvaluation.yaml",
    "C06ProjectClaim": "src/C06Claim.yaml",
    "C06CohortClaim": "src/C06Claim.yaml",
    "C06SiteClaim": "src/C06Claim.yaml",
    "C06PlotClaim": "src/C06Claim.yaml",
}
EXAMPLES = {
    "data/playground/Claim/GenericClaim-001.yaml": "examples/generic-claim.jsonld",
    "data/playground/Claim/GenericClaim-002-revision.yaml": "examples/generic-claim-revision.jsonld",
    "data/playground/C06SiteClaim/C06SiteClaim-mvp-001.yaml": "examples/c06-mvp-claim.jsonld",
    "data/playground/RegistryRequirementEvaluation/RegistryRequirementEvaluation-crediting-term-001.yaml": "examples/registry-requirement-evaluation.jsonld",
    "data/playground/RegistryFindingEvaluation/RegistryFindingEvaluation-cl-001.yaml": "examples/registry-finding-evaluation.jsonld",
    "data/playground/RegistryReportEvaluation/RegistryReportEvaluation-validation-001.yaml": "examples/registry-report-evaluation.jsonld",
    "data/playground/Evaluation/Evaluation-generic-001.yaml": "examples/generic-evaluation.jsonld",
    "data/playground/Evidence/Evidence-field-records-S-001-2019-2021.yaml": "examples/evidence.jsonld",
    "data/playground/EvidenceEvaluation/EvidenceEvaluation-generic-001.yaml": "examples/evidence-evaluation.jsonld",
    "data/playground/ClaimConsistencyEvaluation/ClaimConsistencyEvaluation-generic-001.yaml": "examples/claim-consistency-evaluation.jsonld",
    "data/playground/C06ProjectClaim/C06ProjectClaim-mvp-001.yaml": "examples/c06-project-claim.jsonld",
    "data/playground/C06CohortClaim/C06CohortClaim-mvp-001.yaml": "examples/c06-cohort-claim.jsonld",
    "data/playground/C06PlotClaim/C06PlotClaim-mvp-001.yaml": "examples/c06-plot-claim.jsonld",
    "data/playground/C06ProjectClaim/C06ProjectClaim-statement-001.yaml": "examples/c06-project-claim-statement.jsonld",
}
INVALID_GLOB = "examples/*.INVALID-*.yaml"
EVIDENCE_GLOB = "data/playground/Evidence/*.ttl"
GRAPH_MARK = "# graph: with the Evidence records"
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


def designated_class(view, class_name, data):
    """Return the subclass a type designator (such as selectorType) names."""
    for slot in view.class_induced_slots(class_name):
        if slot.designates_type and slot.name in data:
            for name in view.class_descendants(class_name):
                if view.get_uri(view.get_class(name)) == data[slot.name]:
                    return name, slot.name
    return class_name, None


def typed(view, class_name, data):
    """Return data with "@type" on this object and on nested inlined objects."""
    class_name, designator = designated_class(view, class_name, data)
    out = {"@type": class_name}
    for key, value in data.items():
        if key == designator:
            continue  # stated by "@type"
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


def build(module, class_name, source, data=None):
    if data is None:
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


def evidence_store():
    """The Evidence records as the graph store holds them: gen-rdf's Turtle."""
    paths = sorted(glob.glob(EVIDENCE_GLOB))
    if not paths:
        sys.exit("No Evidence Turtle found: run make gen-rdf")
    store = rdflib.Graph()
    for path in paths:
        store += lexical_graph(Path(path).read_text(), "turtle")
    return store


def with_store(graph, store, class_name=None):
    if class_name == "Evidence":
        return graph
    merged = rdflib.Graph()
    merged += graph
    merged += store
    return merged


def change_selector(data):
    """Return a copy of data whose first citation's first selector is changed."""
    data = json.loads(json.dumps(data))
    selector = data["hasEvidenceCitation"][0]["selector"][0]
    key = "value" if "value" in selector else "exact"
    selector[key] = selector[key] + "-changed"
    return data


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
    store = evidence_store()

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
            conforms, messages = shacl_report(with_store(graph, store, class_name), module["shapes"])
            if conforms:
                print(f"✅ {document}: conforms to SHACL")
            else:
                print(f"❌ {document}: SHACL violations {messages}")
                failures += 1
        data = yaml.safe_load(Path(fixture).read_text())
        if data.get("hasEvidenceCitation"):
            graph = rdflib.Graph().parse(data=text, format="json-ld")
            changed = rdflib.Graph().parse(data=build(module, class_name, fixture, change_selector(data)), format="json-ld")
            cited = lambda g: set(g.objects(None, rdflib.URIRef(module["view"].get_uri(module["view"].get_slot("hasEvidence"), expand=True))))
            records = lambda g: {t for t in with_store(g, store) if t[0] in cited(graph)}
            if cited(changed) == cited(graph) and records(changed) == records(graph) and not isomorphic(changed, graph):
                print(f"✅ {example}: changing a selector changes the citation, not the cited Evidence IRIs or records")
            else:
                print(f"❌ {example}: changing a selector changed the cited Evidence, or nothing")
                failures += 1
        if class_name == "GenericClaim":
            graph = with_store(lexical_graph(text, "json-ld"), store)
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
        if GRAPH_MARK in content:
            if valid:
                print(f"✅ {invalid}: JSON Schema accepts it alone")
            else:
                print(f"❌ {invalid}: expected JSON Schema to accept it alone\n{output}")
                failures += 1
        elif not valid and expected in output:
            print(f"✅ {invalid}: JSON Schema rejects it ({expected})")
        else:
            print(f"❌ {invalid}: expected JSON Schema rejection with '{expected}'\n{output}")
            failures += 1
        graph = lexical_graph(build(module, class_name, invalid), "json-ld")
        merged = with_store(graph, store, None if GRAPH_MARK in content else class_name)
        conforms, messages = shacl_report(merged, module["shapes"])
        mark = next((line for line in content.splitlines() if line.startswith("# shacl: not enforced")), None)
        if mark:
            reason = mark.removeprefix("# shacl: not enforced").strip() or "(a LinkML rule; not expressed in SHACL)"
            if conforms:
                print(f"ℹ️  {invalid}: SHACL accepts it {reason}")
            else:
                print(f"❌ {invalid}: marked 'shacl: not enforced' but SHACL rejects it ({messages[0][:80]})")
                failures += 1
        elif not conforms:
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
