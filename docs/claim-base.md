# The base Claim

The base [`Claim`](../schema/src/Claim.yaml) holds the asserted content every claim shares. Claim
makers author it; validators, reviewers and applications read it. Claim-type schemas extend it with
domain content. Shared relations live in [`ClaimVocabulary`](../schema/src/ClaimVocabulary.yaml), which
claim-type schemas import rather than restate.

This document is the operational reference: the fields, how to extend the base, how to validate and
query claims, and the record of changes against the earlier schema. The decisions and their
rationale are in [ADR 0001][ADR]. Each slot's description in [`Claim.yaml`](../schema/src/Claim.yaml) states
its meaning. Building the examples and running the checks is described in
[`schema/README.md`](../schema/README.md#claim-examples-and-checks).

Implements [#71 (WP1-05)](https://github.com/regen-network/regen-data-standards/issues/71). Vocabulary
reuse follows the [WP1-01 recommendations at `c133c146`][RESEARCH] (#67). The use cases in
[#68](https://github.com/regen-network/regen-data-standards/issues/68#issuecomment-5779800070) were used
to check which fields are shared.

## What one Claim covers

ADR 0001 defines a Claim. These rules decide where one Claim ends and another begins:

- **One assertion.** A Claim is one unit that can be accepted, rejected, evidenced or revised on its
  own. It is not one sentence or one RDF triple: the statements naming a planting activity, its plot,
  its period and its area together assert that the planting took place, and form one Claim. A
  further statement that the planting increased soil carbon is normally another Claim, because a
  reviewer could accept the planting and reject the carbon calculation. Parts that a reviewer could
  judge separately are separate Claims.
- **One unit of responsibility.** Each listed claimant takes responsibility for the whole assertion.
  When different agents take responsibility for different parts, those parts are separate Claims, not
  one Claim with all of them as claimants.
- **Not every grouping or resource is a Claim.** A report or an application can group many Claims
  without becoming one large Claim. Not every RDF resource, observation, dataset or triple needs a
  Claim around it: a Claim is used where assertion-level attribution, evidence and review are needed.

## Base fields

| Slot | RDF term | Range | Cardinality | Meaning |
|---|---|---|---|---|
| `name` | `schema:name` | string | 0..1 | A title, for display. It is not the assertion. |
| `claimStatement` | `rfs:claimStatement` ⊑ `schema:description` | string | 1 | The assertion in the claimants' words. It is asserted content, not a summary. |
| `inLanguage` | `schema:inLanguage` | BCP 47 tag with a 2- or 3-letter ISO 639 primary subtag | 0..1 | Language of `claimStatement`. A tag that is only private use, such as `x-regen`, is not accepted. The form is checked, not registration, so some deprecated grandfathered tags such as `zh-min` pass. |
| `url` | `schema:url` | uri | 0..1 | A page for readers. It is not evidence. |
| `assertedBy` | `rfs:assertedBy` ⊑ `prov:wasAttributedTo` | `Entity` (inlined) | 1..*, set | Who takes responsibility for asserting the content. It does not establish their authority. |
| `assertedAt` | `rfs:assertedAt` | `xsd:dateTime`, UTC, whole seconds, `+00:00` | 1 | When the claimants make the assertion. |
| `hasSubject` | `rfs:hasSubject` | `ClaimSubject` (inlined, with IRI) | 1 | The one focal resource the claim is about, as a typed subject node. |
| `hasEvidence` | `rfs:hasEvidence` ⊑ `dcterms:references` | `Evidence` (inlined, with IRI) | 0..*, set | Sources the claimant presents as evidence, each a typed Evidence node. |
| `wasRevisionOf` | `prov:wasRevisionOf` | IRI | 0..1 | The exact earlier Claim version this one revises. |

**Statement and structured fields.** A claim type may formalize the assertion, or add detail to it,
in structured fields, such as an area and its unit. The statement and those fields are one assertion
and must agree. Generated validators cannot compare prose with values, so agreement is checked where
people see both: when the claimants confirm the Claim during authoring, and in review. When they
disagree, neither overrides the other: the Claim is internally inconsistent and is corrected by a
new version (`wasRevisionOf`) before its evidence is evaluated.

Every resource a claim points to is written as a node with its own IRI and an RDF type, never as a
bare IRI, so the generated JSON Schema and SHACL can validate it as generated and claims can be
queried by what they point to. `wasRevisionOf` is the one exception (see
[Shared vocabulary](#shared-vocabulary)). Claim-type schemas define the kinds of subject they need as
subclasses of [`ClaimSubject`](../schema/src/ClaimSubject.yaml), for example `Plot is_a ClaimSubject`.
The [`Evidence`](../schema/src/Evidence.yaml) skeleton has only an IRI, a title and a description;
[#73](https://github.com/regen-network/regen-data-standards/issues/73) adds content hash and resolver,
locator, producer, sources, place and licence terms.

## Shared vocabulary

[`ClaimVocabulary.yaml`](../schema/src/ClaimVocabulary.yaml) defines terms that the base Claim,
claim-type schemas and attestations reuse. Importing it attaches nothing; a class carries only the
slots it lists.

| Slot | RDF term | Used by |
|---|---|---|
| `wasAttributedTo` | `prov:wasAttributedTo` | Parent of `assertedBy`. |
| `references` | `dcterms:references` | Parent of `hasEvidence`: a plain citation. |
| `hasEvidence`, `wasRevisionOf` | `rfs:hasEvidence`, `prov:wasRevisionOf` | Base Claim; reusable by attestations. |
| `wasAssociatedWith` | `prov:wasAssociatedWith` | Not used by the base Claim. Provided for claim-type schemas such as CarbonEg ([#73](https://github.com/regen-network/regen-data-standards/issues/73)) to name the operator of a domain activity, e.g. a restoration activity. |

One slot of the base Claim is still a plain IRI reference: `wasRevisionOf`, which ranges over
`Resource`, an abstract class with only an `id`. Its value is always an earlier Claim version, so
"must be an IRI" is the only rule that makes sense for it. The generated SHACL additionally requires a
`rfs:Resource` type that the data never states, so `check-claim-examples` removes that one rule.
LinkML 1.11 generates the right rule for `range: uriorcurie` (an IRI, no class), so both the
`Resource` class and the correction go away with the upgrade in
[#84](https://github.com/regen-network/regen-data-standards/issues/84).

## PROV-O in the schema

ADR 0001 decides the PROV-O alignment. In the schema it is implemented as follows:

- The mixins in [`ProvAlignment.yaml`](../schema/src/ProvAlignment.yaml) make the published hierarchy
  state `rfs:Claim rdfs:subClassOf prov:Entity` and `rfs:Entity rdfs:subClassOf prov:Agent`, and the
  `ProvActivity` mixin does the same for the activity classes of claim-type schemas. The mixins add
  no slots and do not change instance data.
- Specialized relations declare `is_a` on the PROV or Dublin Core slot they narrow, for example
  `assertedBy` on `wasAttributedTo` and `hasEvidence` on `references`, which publishes
  `rdfs:subPropertyOf` triples ([Querying across the hierarchy](#querying-across-the-hierarchy)).
- The PROV slots declare no LinkML `domain:`, because `gen-owl` would turn it into an `rdfs:domain`
  axiom on PROV's own property (for example "every `prov:wasRevisionOf` subject is an `rfs:Claim`"),
  which is false outside our data.

**Generated OWL restates ranges on PROV and DCTerms properties.** `gen-owl --no-use-native-uris`
emits, for example, `prov:wasAttributedTo rdfs:range rfs:Entity` and
`prov:wasRevisionOf rdfs:range rfs:Resource`. That does not contradict PROV-O, but loading it would
narrow PROV's own properties for all data, not just ours. Without `--no-use-native-uris`, `gen-owl`
mints `rfs:`-namespaced copies of these properties instead. No OWL artifact is built, published or
planned: [#74](https://github.com/regen-network/regen-data-standards/issues/74) generates contexts,
JSON Schema and SHACL only. If one is added, it should emit axioms only for `rfs:` terms, keeping
`rfs:assertedBy rdfs:subPropertyOf prov:wasAttributedTo`.

## Extending the base: claim-type schemas

A claim-type schema supplies whatever its kind of claim needs beyond the base: domain statements,
quantities with units, activities and their operators, methodologies, and stricter constraints. For
example, the CarbonEg schema in [#73](https://github.com/regen-network/regen-data-standards/issues/73)
will carry the fields moved out of the base (below).

```yaml
imports: [linkml:types, Claim, ClaimVocabulary, ClaimSubject]
default_range: string          # required: core slots such as name have no explicit range
classes:
  Plot:
    is_a: ClaimSubject
  HedgerowClaim:
    is_a: Claim
    slot_usage:
      hasSubject: {range: Plot}               # narrow a base slot; Plot is_a ClaimSubject
    attributes:
      hasActivity: {range: PlantingActivity, inlined: true, required: true}
```

- Reuse shared terms (`Entity`, `ClaimSubject`, `Evidence`, `ClaimVocabulary`) instead of redefining
  them. Put generic properties, such as a person's name, on the shared entity rather than on the Claim.
- Narrow base slots with `slot_usage`. Base slots are top-level slots so that this works: if they
  were class attributes, LinkML 1.8.6 generators would log `slot_usage for undefined slot` and
  silently drop the narrowing.
- Declare set or sequence semantics on every new multivalued slot.
- Put the period of a domain activity on the activity class, with `prov:startedAtTime` and
  `prov:endedAtTime` for timestamps or date-typed terms such as `schema:startDate` for dates.

The shape above was checked with a scratch schema: it validated and produced the expected RDF. A
scratch claim type also passed the open `Claim` shape, and its own closed shape rejected an
undeclared field. It is not committed, because domain schemas belong to #73.

## Validation entry points

- **Entry point:** the claim type a document declares. `Claim` is abstract, so a document is never
  typed with it directly. A claim with base content only is a `GenericClaim`
  (`linkml-validate -s schema/src/schema.yaml -C GenericClaim`, or `sh:targetClass rfs:GenericClaim`
  in `gen-shacl` output). A claim-type document uses its own class, such as `HedgerowClaim`.
- **Target node:** the root claim node, typed with its claim type. The data does not also state
  `rfs:Claim`; queries for all Claims follow the published class hierarchy instead
  ([Querying across the hierarchy](#querying-across-the-hierarchy)).
- **Base shape and claim-type shapes.** `gen-shacl` leaves the shape of an abstract class open, so
  the `rfs:Claim` shape checks the base content of every claim type and lets a claim type add
  fields, including one defined outside this repository. It applies to any node typed with a
  subclass of `rfs:Claim` when the `rdfs:subClassOf` triple is in the validated graph, as it is in
  the graph store. Each claim type's own shape is closed and includes the inherited fields.
- **Nested and imported definitions:** `Entity`, `Methodology` and other imported classes are checked
  only as values reached from the entry point. Importing a module does not make its classes separate
  whole-claim targets.
- **Additional fields are rejected by the claim type.** The generated JSON Schema and SHACL shapes of
  every claim type, `GenericClaim` included, are closed (`additionalProperties: false`,
  `sh:closed true`). New content requires a claim-type schema, which keeps domain-authoring
  requirements from leaking into the generic admission floor
  ([example](../schema/examples/claim.INVALID-domain-fields-on-base.yaml)).
- **Timestamps are checked as written.** LinkML and rdflib can rewrite a timestamp's lexical form
  before it is checked; see [`schema/README.md`](../schema/README.md#timestamps).
- **Service behaviour is not defined here.** Admission outcomes and error information are
  [claims#55](https://github.com/regen-network/claims/issues/55) (WP1-09). Runtime checks are
  [claims#18](https://github.com/regen-network/claims/issues/18) (WP3-03). Schema conformance is not a
  programme verdict.

## Querying across the hierarchy

Instance data carries only the most specific class and property: a specialized claim is typed with
its own class, for example `ex:CarbonEgClaim` or `rfs:GenericClaim`, and evidence is linked with
`rfs:hasEvidence`. The broader types and properties are not added to the data, because they would
enter the Claim's hashed content. So a plain query for every `rfs:Claim`, or every
`dcterms:references`, misses them.

`make -C schema gen-hierarchy` reads the class and property hierarchy from the schema (`is_a` and
mixins) and writes it as `rdfs:subClassOf` and `rdfs:subPropertyOf` triples to
`schema/data/playground/vocabulary/hierarchy.ttl`, which `update-graph` publishes with the playground
data. It covers only subjects in the `rfs:` namespace, so it says nothing about PROV or Dublin Core
terms themselves. Queries follow the hierarchy with SPARQL property paths, without a reasoner:

```sparql
PREFIX rfs: <https://framework.regen.network/schema/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>

# Every Claim, including specialized claims
SELECT ?claim WHERE { ?claim a/rdfs:subClassOf* rfs:Claim }

# Every citation, including hasEvidence
SELECT ?claim ?source WHERE { ?claim ?p ?source . ?p rdfs:subPropertyOf* dcterms:references }
```

A consumer that loads claims into another store loads `hierarchy.ttl` with them, or uses an RDFS
reasoner. `make -C schema check-hierarchy`, run in CI after `gen-rdf`, checks that for every class
and specialized property in the schema these queries return every instance and triple the schema's
hierarchy implies. The same gap existed before the base Claim: project and credit-class fixtures are
typed with their specific classes, such as `rfs:C01ProjectInfo`, which a query for every
`rfs:ProjectInfo` missed.

## Field record against `Claim.yaml` at `0a4ba12a`

Prior definitions: [Claim.yaml at `0a4ba12a`][OLD].

| Prior slot | Change | Now |
|---|---|---|
| `Claim` (class) | Changed | Abstract, with an open generated shape. A claim with base content only is a `GenericClaim`, whose shape is closed. |
| `name` | Retained, changed | Same term, now optional: a title is for display and is not the assertion. |
| `url` | Retained | Unchanged term, described as a pointer, not evidence. |
| `description` | Renamed, changed | Now `claimStatement` (`rfs:claimStatement`, a subproperty of `schema:description`), required, and documented as asserted content that structured fields must agree with. |
| — | Added | `inLanguage` (`schema:inLanguage`), the optional language of the statement, as a BCP 47 tag with a 2- or 3-letter ISO 639 primary subtag. |
| `hasClaimType` | Removed | A claim's kind is its class, such as `GenericClaim` or a claim-type class (following [#86](https://github.com/regen-network/regen-data-standards/issues/86)): a required subject-matter enum does not cover every assertion, for example an evaluation. The `ClaimType` enum is removed from `taxonomy.yaml` too, since nothing else used it. |
| `hasClaimant` | Renamed, changed | Now `assertedBy` (`rfs:assertedBy`), which pairs with `assertedAt` and reads correctly for every Claim subclass, including an evaluation's issuer. It is a set (1..*) and a subproperty of `prov:wasAttributedTo`. A single claimant is a one-element list. |
| `hasSubject` | Retained, changed | Range changed from inline `Entity` to an inline `ClaimSubject` node, which must have an IRI. |
| `claimStartDate`, `claimEndDate` | Moved | Off the base, to the domain activity that specialized claim schemas describe. |
| — | Added | `assertedAt`, and `hasEvidence` over a new [`Evidence`](../schema/src/Evidence.yaml) skeleton (IRI, title, description). |
| `supersedes` | Replaced | By `wasRevisionOf` (`prov:wasRevisionOf`). It must name an exact version, not a logical identifier. |
| `hasOperator` | Moved | Off the base, onto the domain activity in claim-type schemas via `wasAssociatedWith`. |
| `hasPrimaryImpact`, `hasCoBenefits`, `quantity`, `quantityUnit` (with the `QuantityUnit` enum and its rule), `hasCreditClass` | Moved | To specialized claim schemas, starting with #73. Their shape, including co-benefit collection semantics, is decided there. `Impact` and `SDG` remain available as shared modules. |
| `usesMethodology` | Moved | To specialized claim schemas, starting with #73. It names a methodology document, such as a sampling protocol, which only some kinds of claim use. |
| `verificationStatus` | Removed | Review state is not content. The unused `VerificationStatus` enum is removed from `taxonomy.yaml` too; review states will be defined with the review-state record. |
| `contentHash`, `dataIri` | Removed | Derived identity is not content. |

**Existing logical identifiers.** Earlier claim records, such as koi-processor `claim_rid` values and
ORN RIDs accepted by `supersedes`, name a *mutable record* that may have held several states. They
are not Claim version identifiers, and they do not appear in Claim content. Under this schema:

- each immutable version is identified by the ClaimIRI that [claims#1](https://github.com/regen-network/claims/issues/1)
  derives from its content;
- versions are linked by `wasRevisionOf`;
- the mapping from a legacy RID to the ClaimIRIs of the versions minted from its states, and the
  choice of current version, are service data outside the Claim.

A migrated claim that corrects its legacy predecessor states `wasRevisionOf` only when that
predecessor has itself been minted as an immutable version.

**Mapping verification (proposed; confirm in review):** @blushi (WP1-05 assignee) verifies the
schema-side mapping above. @DarrenZal (koi-processor, WP1-08) verifies it against the stored claim
records that use the prior fields and their RIDs.

## Open, and where it is tracked

- `Entity` has no identifier yet, so claimants remain blank nodes and cannot be joined across claims
  ([#58](https://github.com/regen-network/regen-data-standards/pull/58)). Renaming it to `Agent`, with
  PROV agent kinds, is [#95](https://github.com/regen-network/regen-data-standards/issues/95).
- Whether a claimant is authorized to assert for another party is not recorded by the Claim:
  [#96](https://github.com/regen-network/regen-data-standards/issues/96).
- Two items of the #71 checklist are deferred to #73, which has the first specialized schema to use
  them: verification-method terms and normative rule-set version references. Neither applies to
  every claim, so neither is on the base Claim.
- The review-state record and the full evidence shape also belong to #73. Generated JSON Schema,
  SHACL and context artifacts belong to #74; no OWL artifact is planned.

[ADR]: adr/0001-claim-rdf-shape-and-provenance-boundaries.md
[RESEARCH]: https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md
[OLD]: https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml
