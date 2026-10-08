# The base Claim

The base [`Claim`](../schema/src/Claim.yaml) holds the asserted content every claim shares. Claim
makers author it; validators, reviewers and applications read it. Claim-type schemas extend it with
domain content. Shared relations live in [`ClaimVocabulary`](../schema/src/ClaimVocabulary.yaml), which
claim-type schemas import rather than restate.

Implements [#71 (WP1-05)](https://github.com/regen-network/regen-data-standards/issues/71). The content
boundary follows [ADR 0001 D1 at `0cfe1c52`][ADR-D1] (Proposed). Vocabulary reuse follows the
[WP1-01 recommendations at `c133c146`][RESEARCH] (#67). The use cases in
[#68](https://github.com/regen-network/regen-data-standards/issues/68#issuecomment-5779800070) were used
to check which fields are shared.

## What a Claim is

A Claim is an assertion made or adopted by one or more claimants about one subject, at a stated
time. It records what is asserted and may cite evidence.

- **One assertion.** A Claim is one unit that can be accepted, rejected, evidenced or revised on its
  own. It is not one sentence or one RDF triple: the statements naming a planting activity, its plot,
  its period and its area together assert that the planting took place, and form one Claim. A
  further statement that the planting increased soil carbon is normally another Claim, because a
  reviewer could accept the planting and reject the carbon calculation. Parts that a reviewer could
  judge separately are separate Claims.
- **One unit of responsibility.** Each listed claimant takes responsibility for the whole assertion
  (see [Claimant](#base-fields)). When different agents take responsibility for different parts,
  those parts are separate Claims, not one Claim with all of them as claimants.
- **Not every grouping or resource is a Claim.** A report or an application can group many Claims
  without becoming one large Claim. Not every RDF resource, observation, dataset or triple needs a
  Claim around it: a Claim is used where assertion-level attribution, evidence and review are needed.

- **Asserted by definition.** A Claim needs a claimant and an assertion time. An unasserted authoring
  candidate, such as an extraction draft, is not a Claim and does not validate as one
  ([example](../schema/examples/claim.INVALID-candidate-without-claimant.yaml)). How a confirmed Claim
  links back to its draft is authoring and submission history, which is recorded outside the Claim
  ([claims#55](https://github.com/regen-network/claims/issues/55)), because putting it in content would
  make the ClaimIRI depend on the draft's identifier ([research §3.2][R32]).
- **Self-attested without a third party.** Naming the claimant is the claimant's explicit assertion.
  A Claim with no review or attestation is valid, and it is not "pending" or "unverified" because of
  that ([example](../schema/examples/generic-claim.jsonld)).
- **Immutable.** A correction is a new Claim that names the exact version it revises
  ([example](../schema/examples/generic-claim-revision.jsonld)). The earlier version does not change.
  A separate, later assertion that builds on a Claim, such as a survival observation after a planting
  claim (#68 use case 1), is a new Claim, not a revision.

## Base fields

| Slot | RDF term | Range | Cardinality | Meaning |
|---|---|---|---|---|
| `name` | `schema:name` | string | 1 | Human-readable title. |
| `description` | `schema:description` | string | 0..1 | The assertion in the claimant's words. It is asserted content, not a summary. |
| `url` | `schema:url` | uri | 0..1 | A page for readers. It is not evidence. |
| `assertedBy` | `rfs:assertedBy` ⊑ `prov:wasAttributedTo` | `Entity` (inlined) | 1..*, set | Who takes responsibility for asserting the content. It does not establish their authority. |
| `assertedAt` | `rfs:assertedAt` | `xsd:dateTime`, UTC, whole seconds | 1 | When the claimants make the assertion. |
| `hasSubject` | `rfs:hasSubject` | `ClaimSubject` (inlined, with IRI) | 1 | What the claim is about, as a typed subject node. |
| `hasEvidence` | `rfs:hasEvidence` ⊑ `dcterms:references` | `Evidence` (inlined, with IRI) | 0..*, set | Sources the claimant presents as evidence, each a typed Evidence node. |
| `wasRevisionOf` | `prov:wasRevisionOf` | IRI | 0..1 | The exact earlier Claim version this one revises. |

The rows below explain the design choices that aren't obvious from the table.

**Collections.** Every multivalued slot is `list_elements_ordered: false`. Order carries no meaning,
and each one serializes as repeated RDF triples, not an `rdf:List` (ADR D2).

**Claimant.** Each listed claimant takes responsibility for the whole assertion. A collective that asserts
as one body, such as a cooperative or community, is **one** claimant of type `COMMUNITY` or
`ORGANIZATION`. Listing it does not make its members co-claimants. Taking responsibility for the
assertion is distinct from writing, extracting, generating, transforming or submitting the content:
a person, tool or service that only did that is not a claimant unless it takes responsibility for
the assertion itself ([research §3.1][R31]). A claimant's capacity, such as project proponent or
verifier, is a role in the context of the claim, not a subclass of `Entity`. Attribution records who
takes responsibility, not who is authorized: whether a claimant may assert on behalf of a project,
community or program is not stated by the Claim and needs its own record. The slot declares `is_a: wasAttributedTo`, published as
`rfs:assertedBy rdfs:subPropertyOf prov:wasAttributedTo`. Instance data carries only
`rfs:assertedBy`, so a generic PROV attribution query must follow the published hierarchy
([Querying across the hierarchy](#querying-across-the-hierarchy)).
PROV infers from an attribution that the agent was associated with an activity that generated the
entity ([PROV-CONSTRAINTS, Inference 13][PROVC]). For a Claim, that activity is the act of asserting,
which is why a service that only extracted or submitted the RDF is not a claimant.

**Assertion time.** `assertedAt` is when the claimants made the assertion. When they made it in a
source document, such as a project plan, and someone transcribed it later, it is when they made it
there: the transcriber is recorded in the authoring trail, not as claimant, and transcription time
is not assertion time. It is never observation time, which belongs to the observation or activity the
claim describes, nor the time the Claim record was generated, submitted, published or ingested, which
belong to the authoring, submission ([claims#55](https://github.com/regen-network/claims/issues/55))
and publication records. Content asserted at a different time is a different Claim. The research
asks for an explicit definition ([§3.4][R34]). `prov:atTime` cannot attach to a PROV attribution
([#70](https://github.com/regen-network/regen-data-standards/issues/70#issuecomment-5785207710)).
`prov:generatedAtTime` ("the time at which an entity was completely created and is available for use",
[PROV-O][PROVO]) is the nearest PROV term. It is not used, because other records use it for the time a
record was produced (OutputRecord maps `emittedAt` to it in
[#55](https://github.com/regen-network/regen-data-standards/pull/55)), and the research warns against
substituting file-generation time for assertion time. So the term is `rfs:assertedAt`.

**Timestamp format.** `assertedAt` is written in UTC with whole seconds and the offset `+00:00`, for
example `2026-05-02T07:30:00+00:00`. RDF literals are compared by their exact text, so the same
instant written two ways (`Z` and `+00:00`, or `…:00` and `…:00.0`) would give the same assertion
two identities. One spelling is therefore required. XSD 1.1 names these redundancies
([lexical mappings][XSD-LEX]); its canonical representation for a zero offset is `Z`
([timezone canonical mapping][XSD-TZ]), but canonical representations "are not required for schema
processing itself" ([definition and note][XSD-CANON]). The base requires `+00:00` because LinkML and
rdflib write that form: LinkML objects rewrite `Z` as `+00:00` when they load data, and rdflib does
the same unless `NORMALIZE_LITERALS` is off. So the authored fixtures and the RDF that `gen-rdf`
publishes both conform, with no rewriting step. A tool that writes `Z` by default, such as
JavaScript's `Date.prototype.toISOString()`, must write `+00:00` instead. A pattern enforces the
format in both JSON Schema and SHACL, so `Z` is rejected
([example](../schema/examples/claim.INVALID-z-suffix-assertion-time.yaml)), and so is a local offset
such as `+02:00` ([example](../schema/examples/claim.INVALID-local-offset-assertion-time.yaml)). This
applies to timestamps only: date-only values elsewhere stay dates and are not shifted to UTC.

Because LinkML and rdflib would turn a rejected `Z` into an accepted `+00:00`, tools must check the
text as written. So CI validates the authored files with `linkml-validate` rather than with
`linkml-convert --validate`, and `check-claim-examples` parses RDF with literal normalization off. How
the identity recipe treats timestamp literals is decided in
[claims#1](https://github.com/regen-network/claims/issues/1).

**References are typed nodes.** Every resource a claim points to is written as a node with its own
IRI and an RDF type, never as a bare IRI, so the generated JSON Schema and SHACL can validate it as
generated and claims can be queried by what they point to.

**Subject.** The subject is the one focal resource the claim is about, a
[`ClaimSubject`](../schema/src/ClaimSubject.yaml) node: its IRI, so claims about the same plot, project
or community can be joined, and optionally a name. It is not every participant the assertion
mentions. In a claim relating several parties, such as a lease between a landowner and a farmer,
the others appear in named roles that the claim-type schema defines, or the relationship itself
(the lease) is the subject. Its full
description lives on its own resource. Specialized claim schemas define the kinds of subject they
need as subclasses, for example `Plot is_a ClaimSubject` ([example](../schema/examples/claim.INVALID-bare-iri-subject.yaml)
of a bare IRI being rejected). The range admits places and projects, not only agents. This fixes the old contradiction
between the description ("entity or place … often a project") and the `Entity` range
([#82 discussion](https://github.com/regen-network/regen-data-standards/pull/82#issuecomment-5811850210)).
An observation's feature of interest inside a domain claim stays `sosa:hasFeatureOfInterest`.

**Evidence.** `hasEvidence` lists the sources the claimant presents as evidence for the assertion.
Each is an [`Evidence`](../schema/src/Evidence.yaml) node, not a bare IRI, so evidence is typed and can
be queried and validated ([example](../schema/examples/claim.INVALID-bare-iri-evidence.yaml) of a bare
IRI being rejected). The node's IRI names the exact version cited and may carry a fragment for a
position inside it, such as `#page=2`. Whether a source actually supports the assertion is judged
separately, by attestations. `hasEvidence` specializes `dcterms:references` (the same pattern as
`assertedBy` and `prov:wasAttributedTo`), so a generic Dublin Core citation query finds it when it
follows the published hierarchy ([Querying across the hierarchy](#querying-across-the-hierarchy)). The
skeleton has only an IRI, a title and a description.
[#73](https://github.com/regen-network/regen-data-standards/issues/73) adds content hash and resolver,
locator, producer, sources, place and licence terms.

**Period.** The base Claim has no period, only its assertion time. The period a claim is about
belongs to the domain activity it describes, such as a planting from 1 March to 15 April, which a
specialized claim schema defines together with its operator (`wasAssociatedWith`). Activity classes
declare the `ProvActivity` mixin. With timestamps, the activity uses `prov:startedAtTime` and
`prov:endedAtTime`, whose PROV domain is `prov:Activity` and range `xsd:dateTime`. With dates, it uses
date-typed terms such as `schema:startDate` and `schema:endDate`. Evidence has its own, different
time: when it was produced, for example a survey carried out after the planting. That time goes on
the activity that generated it (`prov:wasGeneratedBy`), not on the Evidence, because PROV-O declares
`prov:Activity` and `prov:Entity` disjoint and Evidence is an Entity.

## What is not Claim content

| Kept outside the Claim | Where it lives |
|---|---|
| Review, verification and lifecycle state (formerly `verificationStatus`) | Separate records pointing to the Claim. The shape is still to be agreed with the claims engine ([ADR D1][ADR-D1]). |
| Identifiers derived from the Claim's own canonical form (formerly `contentHash`, `dataIri`) | Computed over the Claim by [claims#1](https://github.com/regen-network/claims/issues/1) (WP1-08). |
| Which version is current, and the logical claim a version belongs to | Maintained outside immutable versions ([research §3.5][R35]). |
| Submission attempts, submitter, received bytes, ingestion time | Service records ([claims#55](https://github.com/regen-network/claims/issues/55), WP1-09). |
| Evidence integrity, resolver, licence terms and current availability | Integrity, resolver and licence fields are added to [`Evidence`](../schema/src/Evidence.yaml) by [#73](https://github.com/regen-network/regen-data-standards/issues/73) (WP1-06). Current availability and access stay outside Claim content. |
| Schema-version (conformance) declarations | Validation machinery. [claims#1](https://github.com/regen-network/claims/issues/1) decides whether they enter identity. |

## Shared vocabulary

[`ClaimVocabulary.yaml`](../schema/src/ClaimVocabulary.yaml) defines terms that the base Claim,
claim-type schemas and attestations reuse. Importing it attaches nothing; a class carries only the
slots it lists.

| Slot | RDF term | Used by |
|---|---|---|
| `wasAttributedTo` | `prov:wasAttributedTo` | Parent of `assertedBy`. |
| `references` | `dcterms:references` | Parent of `hasEvidence`: a plain citation. |
| `hasEvidence`, `wasRevisionOf` | `rfs:hasEvidence`, `prov:wasRevisionOf` | Base Claim; reusable by attestations. |
| `wasAssociatedWith` | `prov:wasAssociatedWith` | Not used by the base Claim. Provided for claim-type schemas such as CarbonEg ([#73](https://github.com/regen-network/regen-data-standards/issues/73)) to name the operator of a domain activity, e.g. a restoration activity ([ADR D1][ADR-D1], [research §3.2][R32]). |

One slot of the base Claim is still a plain IRI reference: `wasRevisionOf`, which ranges over
`Resource`, an abstract class with only an `id`. Its value is always an earlier Claim version, so
"must be an IRI" is the only rule that makes sense for it. The generated SHACL additionally requires a
`rfs:Resource` type that the data never states, so `check-claim-examples` removes that one rule.
LinkML 1.11 generates the right rule for `range: uriorcurie` (an IRI, no class), so both the
`Resource` class and the correction go away with the upgrade in
[#84](https://github.com/regen-network/regen-data-standards/issues/84).

## PROV-O conformance

Checked against the [PROV-O ontology][PROVO] (`https://www.w3.org/ns/prov-o`), [PROV-DM][PROVDM]
and [PROV-CONSTRAINTS][PROVC].

| Term | PROV domain → range | Use here | What PROV infers |
|---|---|---|---|
| `prov:wasAttributedTo`, specialized by `rfs:assertedBy` | Entity → Agent | Claim → claimant | The Claim is a `prov:Entity` and each claimant a `prov:Agent`. The claimant was associated with an activity that generated the Claim: the act of asserting (Inference 13). |
| `prov:wasRevisionOf` | Entity → Entity (⊑ `wasDerivedFrom`) | Claim version → earlier version | Also a derivation, and the two versions are alternates, i.e. aspects of the same thing (Inference 12). This is why it is reserved for revised versions of the same assertion. |
| `prov:wasAssociatedWith` | Activity → Agent | Domain activity → operator | The subject is a `prov:Activity`. |

The classes are aligned too. The mixins in [`ProvAlignment.yaml`](../schema/src/ProvAlignment.yaml)
make the published hierarchy state `rfs:Claim rdfs:subClassOf prov:Entity` and
`rfs:Entity rdfs:subClassOf prov:Agent`, and the `ProvActivity` mixin does the same for the activity
classes of specialized claim schemas. Our `Entity` class, an individual, organization or community,
is therefore a PROV *Agent*, not a PROV Entity. The mixins add no slots and do not change instance
data. The PROV slots declare no LinkML `domain:`, because `gen-owl` would turn it into an
`rdfs:domain` axiom on PROV's own property (for example "every `prov:wasRevisionOf` subject is an
`rfs:Claim`"), which is false outside our data.

`rfs:hasEvidence` (⊑ `dcterms:references`) and `rfs:assertedAt` are not PROV terms. The first presents
evidence, which PROV does not model. For the second, `prov:atTime` applies only to qualified events and `prov:generatedAtTime`
is the time a record was produced (see [Assertion time](#base-fields)).

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
- Declare set or sequence semantics on every new multivalued slot (ADR D2).

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

## Examples

| File | Shows |
|---|---|
| [`generic-claim.jsonld`](../schema/examples/generic-claim.jsonld) | A self-attested stewardship claim with an inline context. It has no credit class, impact or attestation. |
| [`generic-claim-revision.jsonld`](../schema/examples/generic-claim-revision.jsonld) | An immutable revision that names the earlier version by a labelled placeholder ClaimIRI. |
| [`claim.INVALID-*.yaml`](../schema/examples/) | Documents the base must reject: a candidate without a claimant, review state, the Claim's own hash/IRI, an empty claimant set, a date-only, local-offset or `Z` assertion time, and domain fields on the base. |

The JSON-LD files are generated from the playground fixtures in
[`schema/data/playground/Claim/`](../schema/data/playground/Claim/), which `gen-rdf` validates, by
`make -C schema gen-claim-examples`. CI runs `make -C schema check-claim-examples`, which runs
both validators the schema generates on every document:

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

## Field record against `Claim.yaml` at `0a4ba12a`

Prior definitions: [Claim.yaml at `0a4ba12a`][OLD].

| Prior slot | Change | Now |
|---|---|---|
| `Claim` (class) | Changed | Abstract, with an open generated shape. A claim with base content only is a `GenericClaim`, whose shape is closed. |
| `name`, `url` | Retained | Unchanged terms. `url` is described as a pointer, not evidence. |
| `description` | Retained | Same term. Now documented as asserted content ([ADR D1][ADR-D1]: "a description may contain asserted meaning"). |
| `hasClaimType` | Removed | A claim's kind is its class, such as `GenericClaim` or a claim-type class ([ADR 0001][ADR-HCT], following [#86](https://github.com/regen-network/regen-data-standards/issues/86)): a required subject-matter enum does not cover every assertion, for example an evaluation. The `ClaimType` enum stays in `taxonomy.yaml` for workflows that use it. |
| `hasClaimant` | Renamed, changed | Now `assertedBy` (`rfs:assertedBy`), which pairs with `assertedAt` and reads correctly for every Claim subclass, including an evaluation's issuer. It is a set (1..*) and a subproperty of `prov:wasAttributedTo`. A single claimant is a one-element list. |
| `hasSubject` | Retained, changed | Range changed from inline `Entity` to an inline `ClaimSubject` node, which must have an IRI. |
| `claimStartDate`, `claimEndDate` | Moved | Off the base, to the domain activity that specialized claim schemas describe (see [Period](#base-fields)). Placement was open in ADR D1. |
| — | Added | `assertedAt`, and `hasEvidence` over a new [`Evidence`](../schema/src/Evidence.yaml) skeleton (IRI, title, description). |
| `supersedes` | Replaced | By `wasRevisionOf` (`prov:wasRevisionOf`). It must name an exact version, not a logical identifier. |
| `hasOperator` | Moved | Off the base, onto the domain activity in claim-type schemas via `wasAssociatedWith` ([ADR D1][ADR-D1]). |
| `hasPrimaryImpact`, `hasCoBenefits`, `quantity`, `quantityUnit` (with the `QuantityUnit` enum and its rule), `hasCreditClass` | Moved | To specialized claim schemas ([ADR D1][ADR-D1]), starting with #73. Their shape, including co-benefit collection semantics, is decided there. `Impact` and `SDG` remain available as shared modules. |
| `usesMethodology` | Moved | To specialized claim schemas, starting with #73. It names a methodology document, such as a sampling protocol, which only some kinds of claim use. |
| `verificationStatus` | Removed | Review state is not content ([ADR D1][ADR-D1], agreed July 2026). The `VerificationStatus` enum remains in the taxonomy until the review-state record is designed. |
| `contentHash`, `dataIri` | Removed | Derived identity is not content (same agreement). |

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
  ([#58](https://github.com/regen-network/regen-data-standards/pull/58)). When it lands, the claimant
  can be identified by IRI like the subject.
- ADR 0001 still lists PROV-O alignment, claim period placement and the `supersedes` record as open.
  This implementation takes the WP1-01 recommendations for PROV-O, moves the claim period to the
  domain activity, and puts `wasRevisionOf` in Claim content. The ADR should record those decisions
  before either merges.
- Two items of the #71 checklist are deferred to #73, which has the first specialized schema to use
  them: verification-method terms (the story map's CS-4 enumeration, attributable to the claim or
  attestation that used them) and normative rule-set version references (PG-1). Neither applies to
  every claim, so neither is on the base Claim.
- The review-state record and the full evidence shape also belong to #73. Generated JSON Schema,
  SHACL and context artifacts belong to #74; no OWL artifact is planned.

[ADR-D1]: https://github.com/regen-network/regen-data-standards/blob/0cfe1c522754e4479baf7b931f272865d7c8f4e3/docs/adr/0001-claim-substance-canonicalization.md#d1--define-asserted-content-separately-from-lifecycle-and-derived-identity
[ADR-HCT]: https://github.com/regen-network/regen-data-standards/blob/630cd6225cabe8b1d5473a1c416e6989283a7b32/docs/adr/0001-claim-rdf-shape-and-provenance-boundaries.md?plain=1#L30
[RESEARCH]: https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md
[R31]: https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md#31-what-constitutes-a-claim-and-who-asserts-it
[R32]: https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md#32-asserted-content-versus-provenance
[R34]: https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md#34-schema-composition-select-terms-then-define-constraints
[R35]: https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md#35-identity-and-versioning
[OLD]: https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml
[PROVO]: https://www.w3.org/TR/prov-o/
[XSD-LEX]: https://www.w3.org/TR/xmlschema11-2/#rf-lexicalMappings-datetime
[XSD-CANON]: https://www.w3.org/TR/xmlschema11-2/#dt-canonical-representation
[XSD-TZ]: https://www.w3.org/TR/xmlschema11-2/#f-tzCanFragMap
[PROVDM]: https://www.w3.org/TR/prov-dm/
[PROVC]: https://www.w3.org/TR/prov-constraints/
