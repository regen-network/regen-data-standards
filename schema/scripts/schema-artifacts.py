#!/usr/bin/env python3
"""Generate, version and check the published schema artifacts.

    python3 scripts/schema-artifacts.py generate [context|json-schema|shacl|linkml ...]
    python3 scripts/schema-artifacts.py bundle
    python3 scripts/schema-artifacts.py check [--base REF]

Run from the schema/ directory. Artifacts are generated from src/schema.yaml
and its imports, for the version that src/schema.yaml declares, into
versions/<version>/:

- context.jsonld: the JSON-LD context (gen-jsonld-context --xsd-anyuri-as-iri,
  so uri and uriorcurie values are IRI nodes), with the corrections described
  in corrected_context;
- json-schema.json: the JSON Schema (gen-json-schema
  --include-range-class-descendants, the options linkml-validate uses);
- shacl.ttl: the SHACL shapes (gen-shacl), unchanged except that the graph is
  serialized canonically, so that regenerating it gives the same bytes;
- linkml.yaml: the schema with its imports merged (gen-linkml --mergeimports),
  so that generation and validation can be reproduced without fetching
  imports.

`bundle` copies the JSON-LD examples (examples/*.jsonld) into
versions/<version>/examples/ with the version's context, and writes the
version's entry in versions/manifest.json: the source revision (the git tree
hash of src/), the generator versions, the files and their SHA-256 digests,
the validation entry points and the examples.

`check` checks the bundle offline: every file the manifest lists exists and
has its digest; every entry point exists in the version's JSON Schema and
SHACL shapes; every example of every version is accepted, or, if invalid,
rejected only on the paths the manifest names, by both validators, with no
network access. For the version src/schema.yaml declares, it also checks
that src/ is the source the manifest records and that regenerating the
artifacts gives the same bytes. With --base REF, every version in REF's
manifest must be unchanged: a published version is immutable, so changed
definitions need a new version.

An older version is generated from a checkout of its source:

    git archive <commit> schema | tar -x -C <dir>
    python3 scripts/schema-artifacts.py generate --source <dir>/schema --version <v>
    python3 scripts/schema-artifacts.py bundle --source <dir>/schema --version <v> --commit <commit>
"""

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from collections import Counter
from importlib.metadata import version as package_version
from pathlib import Path

import jsonschema
import rdflib
from jsonschema.exceptions import best_match
from linkml_runtime.utils.schemaview import SchemaView
from pyshacl import validate as shacl_validate
from rdflib.compare import to_canonical_graph
from rdflib.namespace import SH

VERSIONS = Path("versions")
MANIFEST = VERSIONS / "manifest.json"
ARTIFACTS = {
    "context": "context.jsonld",
    "json-schema": "json-schema.json",
    "shacl": "shacl.ttl",
    "linkml": "linkml.yaml",
}
GENERATORS = ("linkml", "linkml-runtime")
# The slots each invalid JSON-LD example is expected to violate, and no other.
INVALID_EXAMPLES = {
    "c06-mvp-claim-domain-invalid.jsonld": ["practices"],
}
# Generators iterate over sets: fix the hash seed so their output order is
# stable.
GENERATOR_ENV = {**os.environ, "PYTHONHASHSEED": "0"}


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True, env=GENERATOR_ENV)
    if result.returncode != 0:
        sys.exit(f"{' '.join(args)} failed\n{result.stderr}")
    return result.stdout


def schema_version(source):
    version = SchemaView(str(source / "src/schema.yaml")).schema.version
    if not version:
        sys.exit(f"{source}/src/schema.yaml declares no version")
    return version


# --- JSON-LD context ---------------------------------------------------------


def corrected_context(view, context):
    """Return the generated context, corrected so that it gives the same RDF
    as the Turtle output for every class of the composed schema.

    gen-jsonld-context writes one term per slot name. Where classes give a
    slot name different meanings (File.description is dcterms:description,
    every other description is schema:description), the term keeps one of
    them. Each slot name keeps the meaning most classes give it; a class that
    gives it another gets a type-scoped context (JSON-LD 1.1) redefining the
    term for nodes of that type. Enum-valued terms get "@type": "@vocab" and a
    scoped context mapping each permissible value to its meaning, so that
    "COMMUNITY" expands to rfs:Community instead of a string literal. An enum
    with no meanings stays a string, as in the Turtle output. An enum where
    only some values have a meaning is refused: JSON-LD would make every value
    an IRI, where the Turtle output keeps a value without a meaning a string.
    """
    prefixes = {k: v for k, v in context.items() if isinstance(v, str) and not k.startswith("@")}
    vocab = context["@vocab"]

    def expand(curie):
        if curie.startswith(("http://", "https://")):
            return curie
        prefix, _, local = curie.partition(":")
        if local and prefix in prefixes:
            return prefixes[prefix] + local
        return vocab + curie

    def generated(term):
        term = term if isinstance(term, dict) else {"@id": term}
        kind = term.get("@type")
        return expand(term["@id"]), kind if kind in (None, "@id") else expand(kind)

    def meaning(slot):
        """(IRI, kind) of a slot as a class induces it: kind is an enum name,
        "@id", an XSD datatype IRI, or None for a plain string."""
        iri = expand(slot.slot_uri) if slot.slot_uri else vocab + slot.name
        enum = view.get_enum(slot.range)
        if enum:
            # An enum without meanings is written as strings in Turtle.
            without = [text for text, pv in enum.permissible_values.items() if not pv.meaning]
            if len(without) == len(enum.permissible_values):
                return iri, None
            if without:
                sys.exit(
                    f"enum {enum.name}: {', '.join(without)} has no meaning while other values do. "
                    "A JSON-LD term turns every value of such an enum into an IRI, where the Turtle "
                    "output keeps a value without a meaning as a string: give every value a meaning."
                )
            return iri, ("enum", slot.range)
        if slot.range in view.all_classes():
            return iri, "@id"
        datatype = view.induced_type(slot.range).uri
        if datatype == "xsd:string":
            return iri, None
        if datatype == "xsd:anyURI":
            return iri, "@id"
        return iri, expand(datatype)

    def definition(slot, kind):
        term = {"@id": slot.slot_uri or slot.name}
        if isinstance(kind, tuple):
            enum = view.get_enum(kind[1])
            term["@type"] = "@vocab"
            term["@context"] = {
                text: pv.meaning for text, pv in enum.permissible_values.items()
            }
        elif kind == "@id":
            term["@type"] = "@id"
        elif kind:
            term["@type"] = view.induced_type(slot.range).uri
        return term

    uses = {}  # slot name -> {meaning: [(class, induced slot)]}
    for class_name in view.all_classes():
        for slot in view.class_induced_slots(class_name):
            # Identifier slots are aliases of @id ("id": "@id").
            if slot.name in context and not slot.identifier:
                uses.setdefault(slot.name, {}).setdefault(meaning(slot), []).append((class_name, slot))

    corrected = {"@version": 1.1, **context}
    scoped = {}  # class name -> {slot name: term definition}
    for name, meanings in uses.items():
        current = generated(context[name])
        counts = Counter({m: len(classes) for m, classes in meanings.items()})
        # Most classes first; on a tie, the generated meaning, then by name.
        chosen = sorted(counts, key=lambda m: (-counts[m], m != current, repr(m)))[0]
        if chosen != current:
            corrected[name] = definition(meanings[chosen][0][1], chosen[1])
        for other, classes in meanings.items():
            if other != chosen:
                for class_name, slot in classes:
                    scoped.setdefault(class_name, {})[name] = definition(slot, other[1])
    for class_name, terms in sorted(scoped.items()):
        term = corrected[class_name]
        term = dict(term) if isinstance(term, dict) else {"@id": term}
        term["@context"] = dict(sorted(terms.items()))
        corrected[class_name] = term
    return corrected


# --- Generation --------------------------------------------------------------


def generate_artifact(kind, schema):
    if kind == "context":
        context = json.loads(run("gen-jsonld-context", "--xsd-anyuri-as-iri", str(schema)))["@context"]
        document = {"@context": corrected_context(SchemaView(str(schema)), context)}
        return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    if kind == "json-schema":
        return run("gen-json-schema", "--include-range-class-descendants", str(schema))
    if kind == "shacl":
        graph = rdflib.Graph().parse(data=run("gen-shacl", str(schema)), format="turtle")
        canonical = rdflib.Graph()
        for triple in to_canonical_graph(graph):
            canonical.add(triple)
        for prefix, namespace in graph.namespaces():
            canonical.bind(prefix, namespace)
        return canonical.serialize(format="turtle")
    if kind == "linkml":
        return run("gen-linkml", "--mergeimports", "--no-metadata", "-f", "yaml", str(schema))
    raise ValueError(kind)


def generate(source, version, kinds):
    out = VERSIONS / version
    out.mkdir(parents=True, exist_ok=True)
    for kind in kinds:
        (out / ARTIFACTS[kind]).write_text(generate_artifact(kind, source / "src/schema.yaml"))
        print(f"✅ {out / ARTIFACTS[kind]}")


# --- Manifest ----------------------------------------------------------------


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def git_tree(directory):
    """The git tree hash of a flat directory of regular files, as
    `git rev-parse <commit>:<directory>` prints it for a commit containing
    exactly these files."""
    entries = b""
    for path in sorted(Path(directory).iterdir()):
        if not path.is_file():
            sys.exit(f"{path}: only regular files are expected in {directory}")
        entries += b"100644 " + path.name.encode() + b"\0" + bytes.fromhex(git_blob(path.read_bytes()))
    return hashlib.sha1(b"tree %d\0" % len(entries) + entries).hexdigest()


def source_record(source, commit):
    src = source / "src"
    record = {
        "path": "schema/src",
        "gitTree": git_tree(src),
        "files": {p.name: git_blob(p.read_bytes()) for p in sorted(src.iterdir())},
    }
    if commit:
        record["commit"] = commit
    return record


def entry_points(view, version):
    """Claim and every concrete class that specializes it."""
    points = {}
    for name in sorted(view.class_descendants("Claim")):
        if view.get_class(name).abstract:
            continue
        points[name] = {
            "class": view.get_uri(name, expand=True),
            "jsonSchema": f"{version}/{ARTIFACTS['json-schema']}#/$defs/{name}",
            "shaclShape": view.get_uri(name, expand=True),
        }
    return points


def bundle(source, version, commit):
    out = VERSIONS / version
    context = json.loads((out / ARTIFACTS["context"]).read_text())["@context"]
    examples_dir = out / "examples"
    if examples_dir.exists():
        shutil.rmtree(examples_dir)
    examples_dir.mkdir()
    examples = []
    for example in sorted((source / "examples").glob("*.jsonld")):
        document = json.loads(example.read_text())
        document["@context"] = context
        target = examples_dir / example.name
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
        record = {"path": f"{version}/examples/{example.name}", "entryPoint": document["@type"]}
        if example.name in INVALID_EXAMPLES:
            record["valid"] = False
            record["violates"] = INVALID_EXAMPLES[example.name]
        else:
            record["valid"] = True
        record["sha256"] = sha256(target)
        examples.append(record)

    view = SchemaView(str(out / ARTIFACTS["linkml"]))
    entry = {
        "source": source_record(source, commit),
        "generators": {name: package_version(name) for name in GENERATORS},
        "files": {
            kind: {"path": f"{version}/{name}", "sha256": sha256(out / name)}
            for kind, name in ARTIFACTS.items()
        },
        "entryPoints": entry_points(view, version),
        "examples": examples,
    }
    manifest = read_manifest()
    manifest["versions"][version] = entry
    manifest["versions"] = dict(sorted(manifest["versions"].items(), key=lambda kv: version_key(kv[0])))
    manifest["latest"] = list(manifest["versions"])[-1]
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"✅ {MANIFEST}: {version}")


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def read_manifest(text=None):
    if text is None:
        if not MANIFEST.exists():
            return {"schema": "https://framework.regen.network/schema/", "latest": None, "versions": {}}
        text = MANIFEST.read_text()
    return json.loads(text)


# --- Validation --------------------------------------------------------------


def block_network():
    """Fail any attempt to open a network connection: contexts, imports and
    shapes must all come from the bundle."""

    def refuse(*args, **kwargs):
        raise RuntimeError("network access attempted during offline validation")

    socket.socket.connect = refuse
    socket.create_connection = refuse


def strip_keywords(value):
    """The LinkML data form of a JSON-LD document: JSON-LD keywords removed."""
    if isinstance(value, dict):
        return {k: strip_keywords(v) for k, v in value.items() if not k.startswith("@")}
    if isinstance(value, list):
        return [strip_keywords(v) for v in value]
    return value


def json_schema_errors(schema, entry_point, document):
    """(message, top-level field) of each error, as linkml-validate reports it."""
    validator = jsonschema.Draft201909Validator(
        {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{entry_point}"},
        format_checker=jsonschema.Draft201909Validator.FORMAT_CHECKER,
    )
    errors = []
    for error in validator.iter_errors(document):
        error = best_match([error])
        path = list(error.absolute_path)
        errors.append((error.message, path[0] if path else None))
    return errors


def shacl_results(shapes, jsonld_text):
    """(message, path) of each SHACL result. Lexical forms are kept as written
    (no Z -> +00:00)."""
    rdflib.NORMALIZE_LITERALS = False
    try:
        graph = rdflib.Graph().parse(data=jsonld_text, format="json-ld")
    finally:
        rdflib.NORMALIZE_LITERALS = True
    conforms, results, _ = shacl_validate(graph, shacl_graph=shapes)
    found = []
    for result in results.subjects(rdflib.RDF.type, SH.ValidationResult):
        message = results.value(result, SH.resultMessage)
        path = results.value(result, SH.resultPath)
        found.append((str(message), str(path) if path is not None else None))
    return conforms, found


def check_examples(version, entry, failures):
    out = VERSIONS / version
    schema = json.loads((out / ARTIFACTS["json-schema"]).read_text())
    shapes = rdflib.Graph().parse(out / ARTIFACTS["shacl"], format="turtle")
    view = SchemaView(str(out / ARTIFACTS["linkml"]))
    for example in entry["examples"]:
        path = VERSIONS / example["path"]
        text = path.read_text()
        entry_point = example["entryPoint"]
        if entry_point not in entry["entryPoints"]:
            failures.append(f"{path}: entry point {entry_point} is not in the manifest")
            continue
        errors = json_schema_errors(schema, entry_point, strip_keywords(json.loads(text)))
        conforms, results = shacl_results(shapes, text)
        if example["valid"]:
            if errors:
                failures.append(f"{path}: JSON Schema rejects it: {errors[0][0]}")
            if not conforms:
                failures.append(f"{path}: SHACL rejects it: {results[0][0][:100]}")
            if not errors and conforms:
                print(f"✅ {path}: valid for {entry_point} (JSON Schema, SHACL)")
            continue
        allowed = set(example["violates"])
        allowed_iris = {view.get_uri(view.induced_slot(s, entry_point), expand=True) for s in allowed}
        outside = [e for e in errors if e[1] not in allowed]
        outside += [r for r in results if r[1] not in allowed_iris]
        if not errors:
            failures.append(f"{path}: JSON Schema accepts it")
        if conforms:
            failures.append(f"{path}: SHACL accepts it")
        if outside:
            failures.append(f"{path}: violations outside {sorted(allowed)}: {outside[:3]}")
        if errors and not conforms and not outside:
            print(f"✅ {path}: rejected for {entry_point} on {sorted(allowed)} only (JSON Schema, SHACL)")


def check_files(version, entry, failures):
    out = VERSIONS / version
    for record in [*entry["files"].values(), *entry["examples"]]:
        path = VERSIONS / record["path"]
        if not path.exists():
            failures.append(f"{path}: missing")
        elif sha256(path) != record["sha256"]:
            failures.append(f"{path}: SHA-256 differs from the manifest")
    schema = json.loads((out / ARTIFACTS["json-schema"]).read_text())
    shapes = rdflib.Graph().parse(out / ARTIFACTS["shacl"], format="turtle")
    for name, point in entry["entryPoints"].items():
        if name not in schema["$defs"]:
            failures.append(f"{version}: entry point {name} is not in {ARTIFACTS['json-schema']}")
        if (rdflib.URIRef(point["shaclShape"]), rdflib.RDF.type, SH.NodeShape) not in shapes:
            failures.append(f"{version}: entry point {name} has no shape in {ARTIFACTS['shacl']}")


def check_current(version, entry, failures):
    """The version src/ declares must be generated from src/ as it is now."""
    if entry["source"]["gitTree"] != git_tree(Path("src")):
        failures.append(
            f"src/ differs from the source of {version} in {MANIFEST}: run make gen-schema-artifacts, "
            f"or, if {version} is published, declare a new version in src/schema.yaml first"
        )
        return
    installed = {name: package_version(name) for name in GENERATORS}
    if installed != entry["generators"]:
        failures.append(f"{version} was generated with {entry['generators']}, installed: {installed}")
        return
    out = VERSIONS / version
    for kind, name in ARTIFACTS.items():
        if generate_artifact(kind, Path("src/schema.yaml")) != (out / name).read_text():
            failures.append(f"{out / name} is stale: run make gen-schema-artifacts")
    context = json.loads((out / ARTIFACTS["context"]).read_text())["@context"]
    for example in sorted(Path("examples").glob("*.jsonld")):
        snapshot = out / "examples" / example.name
        document = json.loads(example.read_text())
        document["@context"] = context
        expected = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
        if not snapshot.exists() or snapshot.read_text() != expected:
            failures.append(f"{snapshot} differs from {example}: run make gen-schema-artifacts")


def check_base(base, manifest, failures):
    result = subprocess.run(["git", "show", f"{base}:schema/{MANIFEST}"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ℹ️  {base} has no {MANIFEST}: nothing published to compare")
        return
    for version, entry in read_manifest(result.stdout)["versions"].items():
        if manifest["versions"].get(version) != entry:
            failures.append(f"{version} is published in {base} and must not change: declare a new version")
        else:
            print(f"✅ {version}: unchanged from {base}")


def check(base):
    if not MANIFEST.exists():
        sys.exit(f"{MANIFEST} is missing: run make gen-schema-artifacts")
    block_network()
    manifest = read_manifest()
    current = schema_version(Path("."))
    failures = []
    if current not in manifest["versions"]:
        failures.append(f"{current} (declared in src/schema.yaml) is not in {MANIFEST}: run make gen-schema-artifacts")
    if manifest["latest"] != max(manifest["versions"], key=version_key):
        failures.append(f"{MANIFEST}: latest is not the highest version")
    for version, entry in manifest["versions"].items():
        check_files(version, entry, failures)
        check_examples(version, entry, failures)
        if version == current:
            check_current(version, entry, failures)
    if base:
        check_base(base, manifest, failures)
    for failure in failures:
        print(f"❌ {failure}")
    if failures:
        sys.exit(f"{len(failures)} schema artifact check(s) failed")
    count = len(manifest["versions"])
    print(f"✅ {MANIFEST}: {count} version{'s' if count != 1 else ''}, current {current}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("kinds", nargs="*", metavar="ARTIFACT", help=f"one of {', '.join(ARTIFACTS)} (default: all)")
    for command in (gen, sub.add_parser("bundle")):
        command.add_argument("--source", type=Path, default=Path("."), help="schema directory to generate from")
        command.add_argument("--version", help="version to generate (default: src/schema.yaml's)")
        if command is not gen:
            command.add_argument("--commit", help="commit the source was taken from")
    chk = sub.add_parser("check")
    chk.add_argument("--base", help="git ref whose published versions must be unchanged")
    args = parser.parse_args()

    if args.command == "check":
        check(args.base)
        return
    version = args.version or schema_version(args.source)
    if args.command == "generate":
        unknown = set(args.kinds) - set(ARTIFACTS)
        if unknown:
            parser.error(f"unknown artifact(s) {sorted(unknown)}: choose from {', '.join(ARTIFACTS)}")
        generate(args.source, version, args.kinds or list(ARTIFACTS))
    else:
        bundle(args.source, version, args.commit)


if __name__ == "__main__":
    main()
