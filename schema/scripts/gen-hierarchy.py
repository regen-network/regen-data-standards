#!/usr/bin/env python3
"""Generate and check the class and property hierarchy published with the data.

    python3 scripts/gen-hierarchy.py generate   # write data/playground/vocabulary/hierarchy.ttl
    python3 scripts/gen-hierarchy.py check      # fail if hierarchy queries miss anything

Run from the schema/ directory. Instance data carries only the most specific
class and property, for example a claim typed ex:CarbonEgClaim or evidence
linked with rfs:hasEvidence. Without the hierarchy, a query for every rfs:Claim
or every dcterms:references misses them. The hierarchy is read from the schema
(is_a and mixins of classes, is_a of slots) and written as rdfs:subClassOf and
rdfs:subPropertyOf triples, only for subjects in the rfs: namespace, so nothing
is said about other vocabularies' terms. update-graph publishes the file with
the playground data, and queries follow it with SPARQL property paths.

The check loads every Turtle file gen-rdf wrote plus the hierarchy, and
requires that, for every class and every specialized property in the schema,
the property-path query returns every node and triple the schema's hierarchy
implies. A class that, like all its subclasses, belongs to another vocabulary
(the Web Annotation selectors, for example) is skipped: that vocabulary
publishes its own hierarchy. Run gen-rdf first.
"""

import glob
import sys
from pathlib import Path

import rdflib
from rdflib.namespace import RDF, RDFS
from linkml_runtime.utils.schemaview import SchemaView

SCHEMA = "src/schema.yaml"
DATA = "data/playground"
OUTPUT = f"{DATA}/vocabulary/hierarchy.ttl"
RFS = "https://framework.regen.network/schema/"


def uri(view, element):
    return rdflib.URIRef(view.get_uri(element, expand=True))


def hierarchy(view):
    graph = rdflib.Graph()
    graph.bind("rfs", RFS)
    graph.bind("prov", "http://www.w3.org/ns/prov#")
    graph.bind("dcterms", "http://purl.org/dc/terms/")
    for cls in view.all_classes().values():
        subject = uri(view, cls)
        if not subject.startswith(RFS):
            continue
        for parent in ([cls.is_a] if cls.is_a else []) + list(cls.mixins):
            graph.add((subject, RDFS.subClassOf, uri(view, view.get_class(parent))))
    for slot in view.all_slots().values():
        subject = uri(view, slot)
        if slot.is_a and subject.startswith(RFS):
            graph.add((subject, RDFS.subPropertyOf, uri(view, view.get_slot(slot.is_a))))
    return graph


def check(view):
    if not Path(OUTPUT).exists():
        sys.exit(f"{OUTPUT} is missing: run make gen-hierarchy")
    graph = rdflib.Graph()
    for path in sorted(glob.glob(f"{DATA}/*/*.ttl")):
        graph.parse(path, format="turtle")
    failures = 0

    for name, cls in view.all_classes().items():
        types = {uri(view, view.get_class(d)) for d in view.class_descendants(name, mixins=True)}
        if len(types) > 1 and not any(t.startswith(RFS) for t in types):
            print(f"ℹ️  {name} ({uri(view, cls)}): its own vocabulary publishes its hierarchy")
            continue
        expected = {node for t in types for node in graph.subjects(RDF.type, t)}
        if not expected:
            continue
        found = {row[0] for row in graph.query(
            "SELECT ?x WHERE { ?x a/rdfs:subClassOf* ?c }",
            initNs={"rdfs": RDFS}, initBindings={"c": uri(view, cls)})}
        if expected - found:
            print(f"❌ query for every {name} misses {len(expected - found)} instance(s)")
            failures += 1
        else:
            print(f"✅ query for every {name} finds all {len(expected)} instance(s)")

    children = {}
    for slot in view.all_slots().values():
        if slot.is_a:
            children.setdefault(slot.is_a, []).append(slot.name)
    for name in sorted(children):
        properties = {uri(view, view.get_slot(n)) for n in [name] + children[name]}
        expected = {(s, o) for p in properties for s, o in graph.subject_objects(p)}
        found = {(row[0], row[1]) for row in graph.query(
            "SELECT ?s ?o WHERE { ?s ?p ?o . ?p rdfs:subPropertyOf* ?q }",
            initNs={"rdfs": RDFS}, initBindings={"q": uri(view, view.get_slot(name))})}
        if expected - found:
            print(f"❌ query for every {name} misses {len(expected - found)} triple(s)")
            failures += 1
        else:
            print(f"✅ query for every {name} finds all {len(expected)} triple(s)")

    if failures:
        sys.exit(f"{failures} hierarchy check(s) failed")


def main(mode):
    view = SchemaView(SCHEMA)
    if mode == "generate":
        Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        hierarchy(view).serialize(OUTPUT, format="turtle")
    else:
        check(view)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("generate", "check"):
        sys.exit(__doc__)
    main(sys.argv[1])
