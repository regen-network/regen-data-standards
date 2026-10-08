# Schema

[LinkML](https://linkml.io/) semantic schemas for Regen Network framework.

These schemas define the structure and semantics for credit class and project metadata in the Regen Network ecosystem. They provide a standardized way to describe:

- **Credit Class Information**: Metadata for carbon and biodiversity credit classes, including protocols, methodologies, eligible activities, and environment types
- **Project Information**: Geospatial and descriptive data for projects enrolled in a given credit class
- **Impact Tracking**: Primary impacts and co-benefits associated with projects
- **Taxonomies**: Controlled vocabularies for activities, environment types, and impact types

The schemas are designed to be converted to RDF/JSON-LD formats for semantic web integration and SPARQL querying.

> **Note**: Current on-chain datasets may not fully reflect this schema. The schemas in this repository (and the playground folder) represent the latest up-to-date versions of all Regen Network datasets in a format consistent with current Regen Data Standards.

## Requirements

[Install LinkML](https://linkml.io/linkml/intro/install.html) to use the helper and generator commands for interacting with LinkML schemas and data.

## Structure

- LinkML schemas are created in `schema/src`.
- Create separate schema files for each logical schema class and `import` into the root `schemas.yaml` file.
- Generated markdown from schemas:
  ```shell
  make gen-doc
  ```
- Generate linkml enums for taxonomy terms:
  ```shell
  make gen-taxonomy
  ```

## Playground

Datasets are provided inside `schema/data/playground/{Credit-Class}/{LinkML-Class}-*.yaml` files. All datasets are managed in github as YAML files as this is more lightweight and easier to manage (as the standardized source for LinkML datasets) than storing JSON-LD or TTL files in version control.

There is a designated make task (`gen-rdf`) for validating and generating RDF data in formats besides YAML. This creates `.ttl` and `.jsonld` files for each dataset. To run the script, use the following command:

```shell
make gen-rdf
```

## Claim examples and checks

The base Claim is described in [`docs/claim-base.md`](../docs/claim-base.md).

| File | Shows |
|---|---|
| [`generic-claim.jsonld`](examples/generic-claim.jsonld) | A self-attested stewardship claim with an inline context. It has no credit class, impact or attestation. |
| [`generic-claim-revision.jsonld`](examples/generic-claim-revision.jsonld) | An immutable revision that names the earlier version by a labelled placeholder ClaimIRI. |
| [`claim.INVALID-*.yaml`](examples/) | Documents the base must reject: a candidate without a claimant, review state, the Claim's own hash/IRI, an empty claimant set, a date-only, local-offset or `Z` assertion time, bare-IRI subject and evidence, and domain fields on the base. |

The JSON-LD files are generated from the playground fixtures in
[`data/playground/Claim/`](data/playground/Claim/), which `gen-rdf` validates, by
`make gen-claim-examples`. CI runs `make check-claim-examples`, which runs both validators the schema
generates on every document:

- JSON Schema (`linkml-validate`) over the authored YAML;
- SHACL (`gen-shacl`, run with pyshacl) over the RDF graph of the authored JSON-LD and over the
  Turtle that `gen-rdf` writes for the fixture, which `update-graph` publishes. Both are parsed
  without rdflib's literal normalization, so lexical forms are checked as written. `gen-shacl` adds
  `sh:class` to reference slots, but referenced IRIs are not typed in the data, so the check removes
  that `sh:class` and keeps `sh:nodeKind sh:IRI`.
- SHACL over each example retyped as a claim type defined outside this repository, with a field of
  its own and its `rdfs:subClassOf rfs:Claim` triple. The open `Claim` shape must accept it, and
  must reject it without `assertedBy`.

The check reads that Turtle, so `gen-rdf` must run first, as it does in CI. It fails if an example
is stale, if its JSON-LD graph is not isomorphic to the fixture's published Turtle, if either
validator rejects a valid example or its published Turtle, or if either accepts an invalid one.
JSON Schema must reject each invalid document with the error named on its first line.

The inline context is generated from `Claim.yaml` alone, with two corrections applied because
`linkml-convert -t json-ld` output in LinkML 1.8.6 does not produce the same RDF as its Turtle output.
Enum terms use `@type: @vocab` with each value mapped to its `meaning`, so a claimant's `"COMMUNITY"`
becomes `rfs:Community`, not a string. Nested objects carry `@type`. The context is not generated from
`schema.yaml` because there `ProjectPost`'s `description` (`dcterms:description`) replaces
`schema:description` for every class. Both issues affect all JSON-LD generated in this repository and
are recorded for [#74](https://github.com/regen-network/regen-data-standards/issues/74) (WP1-07).

### Timestamps

`assertedAt` is written in UTC with whole seconds and the offset `+00:00`, for example
`2026-05-02T07:30:00+00:00`. RDF literals are compared by their exact text, so the same instant
written two ways (`Z` and `+00:00`, or `…:00` and `…:00.0`) would give the same assertion two
identities, and one spelling is required. XSD 1.1 names these redundancies
([lexical mappings][XSD-LEX]); its canonical representation for a zero offset is `Z`
([timezone canonical mapping][XSD-TZ]), but canonical representations "are not required for schema
processing itself" ([definition and note][XSD-CANON]). The base requires `+00:00` because LinkML and
rdflib write that form: LinkML objects rewrite `Z` as `+00:00` when they load data, and rdflib does
the same unless `NORMALIZE_LITERALS` is off. So the authored fixtures and the RDF that `gen-rdf`
publishes both conform, with no rewriting step. A tool that writes `Z` by default, such as
JavaScript's `Date.prototype.toISOString()`, must write `+00:00` instead. A pattern enforces the
format in both JSON Schema and SHACL, so `Z` is rejected
([example](examples/claim.INVALID-z-suffix-assertion-time.yaml)), and so is a local offset such as
`+02:00` ([example](examples/claim.INVALID-local-offset-assertion-time.yaml)). This applies to
timestamps only: date-only values elsewhere stay dates and are not shifted to UTC.

Because LinkML and rdflib would turn a rejected `Z` into an accepted `+00:00`, tools must check the
text as written. So CI validates the authored files with `linkml-validate` rather than with
`linkml-convert --validate`, and `check-claim-examples` parses RDF with literal normalization off. How
the identity recipe treats timestamp literals is decided in
[claims#1](https://github.com/regen-network/claims/issues/1).

[XSD-LEX]: https://www.w3.org/TR/xmlschema11-2/#rf-lexicalMappings-datetime
[XSD-CANON]: https://www.w3.org/TR/xmlschema11-2/#dt-canonical-representation
[XSD-TZ]: https://www.w3.org/TR/xmlschema11-2/#f-tzCanFragMap

## SPARQL Integration

If you are running a SPARQL endpoint, you can use the following command to push datasets via a GRAPH_STORE API to update datasets to a live SPARQL store. This adds all `.ttl` files to the graph. Override the `GRAPH_STORE_URL` env var:

```shell
export GRAPH_STORE_URL=http://localhost:7878/store
make update-graph
```
