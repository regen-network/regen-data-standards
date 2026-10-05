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

A Claim is an attributed assertion: related statements that one or more claimants present together
about a subject, at a stated time.

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
| `hasClaimant` | `rfs:hasClaimant` ⊑ `prov:wasAttributedTo` | `Entity` (inlined) | 1..*, set | Who takes responsibility for the assertion. |
| `assertedAt` | `rfs:assertedAt` | `xsd:dateTime`, UTC, whole seconds | 1 | When the claimants make the assertion. |
| `hasSubject` | `rfs:hasSubject` | `ClaimSubject` (inlined, with IRI) | 1 | What the claim is about, as a typed subject node. |
| `hasEvidence` | `rfs:hasEvidence` ⊑ `dcterms:references` | `Evidence` (inlined, with IRI) | 0..*, set | Sources the claimant presents as evidence, each a typed Evidence node. |
| `wasRevisionOf` | `prov:wasRevisionOf` | IRI | 0..1 | The exact earlier Claim version this one revises. |

The rows below explain the design choices that aren't obvious from the table.

**Collections.** Every multivalued slot is `list_elements_ordered: false`. Order carries no meaning,
and each one serializes as repeated RDF triples, not an `rdf:List` (ADR D2).

**Claimant.** Each listed claimant takes responsibility for the whole assertion. A collective that asserts
as one body, such as a cooperative or community, is **one** claimant of type `COMMUNITY` or
`ORGANIZATION`. Listing it does not make its members co-claimants. A service that extracted,
generated or submitted the RDF is not a claimant unless it asserts the content itself
([research §3.1][R31]). The slot declares `is_a: wasAttributedTo`. `gen-owl --no-use-native-uris`
emits this as `rfs:hasClaimant rdfs:subPropertyOf prov:wasAttributedTo`. Instance data carries only
`rfs:hasClaimant`, so queries that want generic PROV attribution must apply the property hierarchy.
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

**Timestamp format.** `assertedAt` is written in UTC with whole seconds, in the XSD canonical form,
for example `2026-05-02T07:30:00Z`. RDF literals are compared by their exact text, so the same instant
written two ways (`Z` and `+00:00`, or `…:00` and `…:00.0`) would give the same assertion two
identities. XSD 1.1 names these redundancies ([lexical mappings][XSD-LEX]) and fixes one spelling per
value, its canonical representation ([definition][XSD-CANON]), which for a zero offset is `Z`
([timezone canonical mapping][XSD-TZ]). A pattern enforces the format in both JSON Schema and SHACL,
so a local offset such as `+02:00` is rejected
([example](../schema/examples/claim.INVALID-local-offset-assertion-time.yaml)). This applies to
timestamps only: date-only values elsewhere stay dates and are not shifted to UTC.

`+00:00`, the other spelling of UTC, is rejected too
([example](../schema/examples/claim.INVALID-utc-offset-assertion-time.yaml)). Tools must therefore
check the text as written. LinkML objects rewrite `Z` as `+00:00` when they load data, and rdflib does
the same unless `NORMALIZE_LITERALS` is off. So CI validates the authored files with `linkml-validate`
rather than with `linkml-convert --validate`, and `check-claim-examples` parses JSON-LD with literal
normalization off. The Turtle and JSON-LD that `gen-rdf` writes still contain `+00:00`, the same
value. How the identity recipe treats timestamp literals is decided in
[claims#1](https://github.com/regen-network/claims/issues/1).

**References are typed nodes.** Every resource a claim points to is written as a node with its own
IRI and an RDF type, never as a bare IRI, so the generated JSON Schema and SHACL can validate it as
generated and claims can be queried by what they point to.

**Subject.** The subject is a [`ClaimSubject`](../schema/src/ClaimSubject.yaml) node: its IRI, so
claims about the same plot, project or community can be joined, and optionally a name. Its full
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
`hasClaimant` and `prov:wasAttributedTo`), so generic Dublin Core citation queries still find it. Each Evidence node also
carries the hash of the cited version, where to fetch it, its DCMI type and its licence reference; see
[`docs/attestation-and-evidence.md`](attestation-and-evidence.md) (#73).

**Period.** The base Claim has no period, only its assertion time. The period a claim is about
belongs to the domain activity it describes, such as a planting from 1 March to 15 April, which a
specialized claim schema defines together with its operator (`wasAssociatedWith`). Activity classes
declare the `ProvActivity` mixin. With timestamps, the activity uses `prov:startedAtTime` and
`prov:endedAtTime`, whose PROV domain is `prov:Activity` and range `xsd:dateTime`. With dates, it uses
date-typed terms such as `schema:startDate` and `schema:endDate`. Evidence has its own, different
time: when it was produced, for example a survey carried out after the planting. That time goes on
the activity that generated it (`Evidence.wasGeneratedBy`, an [`Activity`](../schema/src/Activity.yaml)), not on the Evidence, because PROV-O declares
`prov:Activity` and `prov:Entity` disjoint and Evidence is an Entity.

## What is not Claim content

| Kept outside the Claim | Where it lives |
|---|---|
| Review, verification and lifecycle state (formerly `verificationStatus`) | Separate records pointing to the Claim. The shape is still to be agreed with the claims engine ([ADR D1][ADR-D1]). |
| Identifiers derived from the Claim's own canonical form (formerly `contentHash`, `dataIri`) | Computed over the Claim by [claims#1](https://github.com/regen-network/claims/issues/1) (WP1-08). |
| Which version is current, and the logical claim a version belongs to | Maintained outside immutable versions ([research §3.5][R35]). |
| Submission attempts, submitter, received bytes, ingestion time | Service records ([claims#55](https://github.com/regen-network/claims/issues/55), WP1-09). |
| Evidence integrity, resolver, licence terms and current availability | The hash, resolver and licence reference of the cited version are [`Evidence`](../schema/src/Evidence.yaml) fields (#73, [`docs/attestation-and-evidence.md`](attestation-and-evidence.md)). Current availability and access, and the currently offered licence, stay outside Claim content. |
| Schema-version (conformance) declarations | Validation machinery. [claims#1](https://github.com/regen-network/claims/issues/1) decides whether they enter identity. |

## Shared vocabulary

[`ClaimVocabulary.yaml`](../schema/src/ClaimVocabulary.yaml) defines terms that the base Claim,
claim-type schemas and attestations reuse. Importing it attaches nothing; a class carries only the
slots it lists.

| Slot | RDF term | Used by |
|---|---|---|
| `wasAttributedTo` | `prov:wasAttributedTo` | Parent of `hasClaimant`. |
| `references` | `dcterms:references` | Parent of `hasEvidence`: a plain citation. |
| `hasEvidence`, `wasRevisionOf` | `rfs:hasEvidence`, `prov:wasRevisionOf` | Base Claim; reusable by attestations. |
| `wasAssociatedWith` | `prov:wasAssociatedWith` | Not used by the base Claim. Defined with `Activity` in [`Activity.yaml`](../schema/src/Activity.yaml), which `ClaimVocabulary` imports ([#73](https://github.com/regen-network/regen-data-standards/issues/73)). It names who carried out an activity: the one that generated a piece of evidence, or a domain activity a claim-type schema describes, e.g. a restoration activity ([ADR D1][ADR-D1], [research §3.2][R32]). |

One slot of the base Claim is a plain IRI reference: `wasRevisionOf`, with `range: uriorcurie`
(as is `references`, its unused sibling). Its value is always an earlier Claim version, so "must be
an IRI" is the only rule that makes sense for it. Since LinkML 1.11
([#84](https://github.com/regen-network/regen-data-standards/issues/84)), such a value is an IRI node
in the Turtle output and the generated SHACL requires `sh:nodeKind sh:IRI` with no class, which is
that rule. By default the generated JSON-LD context and OWL still treat it as an `xsd:anyURI`
literal; both generators need `--xsd-anyuri-as-iri` (see [Examples](#examples) and
[PROV-O conformance](#prov-o-conformance)).

## PROV-O conformance

Checked against the [PROV-O ontology][PROVO] (`https://www.w3.org/ns/prov-o`), [PROV-DM][PROVDM]
and [PROV-CONSTRAINTS][PROVC].

| Term | PROV domain → range | Use here | What PROV infers |
|---|---|---|---|
| `prov:wasAttributedTo`, specialized by `rfs:hasClaimant` | Entity → Agent | Claim → claimant | The Claim is a `prov:Entity` and each claimant a `prov:Agent`. The claimant was associated with an activity that generated the Claim: the act of asserting (Inference 13). |
| `prov:wasRevisionOf` | Entity → Entity (⊑ `wasDerivedFrom`) | Claim version → earlier version | Also a derivation, and the two versions are alternates, i.e. aspects of the same thing (Inference 12). This is why it is reserved for revised versions of the same assertion. |
| `prov:wasAssociatedWith` | Activity → Agent | Activity → operator | The subject is a `prov:Activity`. |
| `prov:wasGeneratedBy` | Entity → Activity | Evidence → the activity that produced it (#73) | The Evidence is a `prov:Entity` and the activity a `prov:Activity`. |

The classes are aligned too. The mixins in [`ProvAlignment.yaml`](../schema/src/ProvAlignment.yaml)
make the generated OWL state `rfs:Claim rdfs:subClassOf prov:Entity` and
`rfs:Entity rdfs:subClassOf prov:Agent`, and the `ProvActivity` mixin does the same for `Activity`
and the activity classes of specialized claim schemas. Our `Entity` class, an individual, organization or community,
is therefore a PROV *Agent*, not a PROV Entity. The mixins add no slots and do not change instance
data. The PROV slots declare no LinkML `domain:`, because `gen-owl` would turn it into an
`rdfs:domain` axiom on PROV's own property (for example "every `prov:wasRevisionOf` subject is an
`rfs:Claim`"), which is false outside our data.

`rfs:hasEvidence` (⊑ `dcterms:references`) and `rfs:assertedAt` are not PROV terms. The first presents
evidence, which PROV does not model. For the second, `prov:atTime` applies only to qualified events and `prov:generatedAtTime`
is the time a record was produced (see [Assertion time](#base-fields)).

**Generated OWL must not redefine PROV or DCTerms properties.** No OWL artifact is built,
published or planned: [#74](https://github.com/regen-network/regen-data-standards/issues/74)
generates contexts, JSON Schema and SHACL only. The rules below apply if one is added. With
LinkML 1.11.1, `gen-owl --no-use-native-uris` emits two kinds of axiom on properties we reuse but
do not own:

- *Contradictions, fixed by `--xsd-anyuri-as-iri`.* By default a `uriorcurie` slot becomes an
  `owl:DatatypeProperty` with `rdfs:range xsd:anyURI`. PROV-O declares `prov:wasRevisionOf` an
  `owl:ObjectProperty` from `prov:Entity` to `prov:Entity`, so loading both makes it both kinds of
  property, which OWL 2 DL forbids, and a reasoner infers that the earlier Claim version is both a
  `prov:Entity` and an `xsd:anyURI` value. The same default makes `rfs:hasEvidence`, an object
  property, a subproperty of the datatype property `dcterms:references`. With the flag, both become
  object properties without a range, as in PROV-O and DCMI Terms.
- *Global narrowing, fixed by emitting only `rfs:` axioms.* `prov:wasAttributedTo rdfs:range
  rfs:Entity` (and the same for `prov:wasAssociatedWith`) remains. It is not a contradiction, but a
  reasoner applies it to all PROV data: any agent anyone attributes anything to becomes an
  `rfs:Entity`. The published OWL should therefore drop every axiom whose subject is a non-`rfs:`
  IRI, keeping the links from our terms, such as `rfs:hasClaimant rdfs:subPropertyOf
  prov:wasAttributedTo` and `rfs:Claim rdfs:subClassOf prov:Entity`.

Checked with the OWL-RL reasoner over PROV-O plus the generated OWL: with both measures, the
reasoner infers only what PROV-O itself implies. Without `--no-use-native-uris`, `gen-owl` mints
`rfs:`-namespaced copies of these properties, which describe terms the data does not use. Any
future OWL artifact needs both measures.

## Extending the base: claim-type schemas

A claim-type schema supplies whatever its kind of claim needs beyond the base: domain statements,
quantities with units, activities and their operators, methodologies, and stricter constraints. For
example, the C06 claim schema in [#73](https://github.com/regen-network/regen-data-standards/issues/73)
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

The shape above was checked with a scratch schema. It validated, rejected its own fields under the
base `Claim`, and produced the expected RDF. It is not committed, because domain schemas belong to #73.

## Validation entry points

- **Entry point:** the most specific claim class a document declares. For a generic claim that is
  `Claim` (`linkml-validate -s schema/src/schema.yaml -C Claim`, or `sh:targetClass rfs:Claim` in
  `gen-shacl` output). For a claim-type document it is its own class, such as `HedgerowClaim`.
- **Target node:** the root claim node, typed with that one class. Do not also type a claim-type
  instance `rfs:Claim`, because the base shape is closed and would reject the extension's fields.
  Queries for all Claims should use `rdfs:subClassOf` from the generated OWL.
- **Nested and imported definitions:** `Entity`, `Methodology` and other imported classes are checked
  only as values reached from the entry point. Importing a module does not make its classes separate
  whole-claim targets.
- **Additional fields are rejected.** Generated JSON Schema and SHACL shapes are closed
  (`additionalProperties: false`, `sh:closed true`). New content requires a claim-type schema, which
  keeps domain-authoring requirements from leaking into the generic admission floor
  ([example](../schema/examples/claim.INVALID-domain-fields-on-base.yaml)).
- **Service behaviour is not defined here.** Admission outcomes and error information are
  [claims#55](https://github.com/regen-network/claims/issues/55) (WP1-09). Runtime checks are
  [claims#18](https://github.com/regen-network/claims/issues/18) (WP3-03). Schema conformance is not a
  programme verdict.

## Examples

| File | Shows |
|---|---|
| [`generic-claim.jsonld`](../schema/examples/generic-claim.jsonld) | A self-attested stewardship claim with an inline context. It has no credit class, impact or attestation. |
| [`generic-claim-revision.jsonld`](../schema/examples/generic-claim-revision.jsonld) | An immutable revision that names the earlier version by a labelled placeholder ClaimIRI. |
| [`claim.INVALID-*.yaml`](../schema/examples/) | Documents the base must reject: a candidate without a claimant, review state, the Claim's own hash/IRI, an empty claimant set, a date-only, local-offset or `+00:00` assertion time, and domain fields on the base. |

The JSON-LD files are generated from the playground fixtures in
[`schema/data/playground/Claim/`](../schema/data/playground/Claim/), which `gen-rdf` validates, by
`make -C schema gen-claim-examples`. CI runs `make -C schema check-claim-examples`, which runs
the published validators of the current schema version (`schema/versions/<version>/`) on every
document:

- the JSON Schema (`json-schema.json`, errors reported as `linkml-validate` reports them) over the
  authored YAML;
- the SHACL shapes (`shacl.ttl`, closed shapes, run with pyshacl) over the RDF graph of the authored
  JSON-LD. The graph is parsed without rdflib's literal normalization, so lexical forms are checked
  as written. The generated shapes are used unchanged.

The check fails if an example is stale, if its JSON-LD graph is not isomorphic to the fixture's
Turtle output, if either validator rejects a valid example, or if either accepts an invalid one.
JSON Schema must reject each invalid document with the error named on its first line.

The inline context is the published context of the current schema version, generated from
`schema.yaml` with `gen-jsonld-context --xsd-anyuri-as-iri`, so `uri` and `uriorcurie` terms (`url`,
`wasRevisionOf`, `references`) map to `@type: @id` and their values are IRI nodes, as in Turtle. It is
corrected so that it gives the same RDF as the Turtle output: enum terms map each value to its
`meaning`, and a slot name that classes map differently, such as `File`'s `description` in `ProjectPost.yaml`
(`dcterms:description`), is redefined in a type-scoped context on its class. Nested objects carry
`@type`. The corrections and the other generator limitations are listed in
[`schema/README.md`](../schema/README.md#generator-limitations) (#74, WP1-07).

## Field record against `Claim.yaml` at `0a4ba12a`

Prior definitions: [Claim.yaml at `0a4ba12a`][OLD].

| Prior slot | Change | Now |
|---|---|---|
| `name`, `url` | Retained | Unchanged terms. `url` is described as a pointer, not evidence. |
| `description` | Retained | Same term. Now documented as asserted content ([ADR D1][ADR-D1]: "a description may contain asserted meaning"). |
| `hasClaimType` | Removed | A single required enum could not cover every kind of claim (#86: a health claim had no category). The kind of claim is the specialized claim class (`is_a Claim`). The `ClaimType` enum remains in the taxonomy. |
| `hasClaimant` | Retained, changed | Now a set (1..*) and a subproperty of `prov:wasAttributedTo`. A single claimant is a one-element list. |
| `hasSubject` | Retained, changed | Range changed from inline `Entity` to an inline `ClaimSubject` node, which must have an IRI. |
| `claimStartDate`, `claimEndDate` | Moved | Off the base, to the domain activity that specialized claim schemas describe (see [Period](#base-fields)). Placement was open in ADR D1. |
| — | Added | `assertedAt`, and `hasEvidence` over a new [`Evidence`](../schema/src/Evidence.yaml) skeleton (IRI, title, description). |
| `supersedes` | Replaced | By `wasRevisionOf` (`prov:wasRevisionOf`). It must name an exact version, not a logical identifier. |
| `hasOperator` | Moved | Off the base, onto the domain activity in claim-type schemas via `wasAssociatedWith` ([ADR D1][ADR-D1]). |
| `hasPrimaryImpact`, `hasCoBenefits` | Removed | They describe the project or the credit class, which `ProjectInfo` and `CreditClassInfo` already do, not what a claim asserts. |
| `quantity`, `quantityUnit` (with the `QuantityUnit` enum and its rule) | Moved | To specialized claim schemas that state a quantity; `C06Claim` states areas with the shared `QuantityValue` in `core.yaml` (`area`). A richer quantity structure is open ([#86](https://github.com/regen-network/regen-data-standards/issues/86)). |
| `hasCreditClass` | Replaced | By `appliesRuleSet` (`ClaimVocabulary`), the exact credit class version a claim applies, used by `C06ProjectClaim`. |
| `usesMethodology` | Moved | To `C06ProjectClaim.methodologyUse`, which names each methodology version and its role. Only some kinds of claim use a methodology. |
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
- Verification-method terms (the story map's CS-4 enumeration) and normative rule-set version
  references (PG-1), deferred from #71, are defined in `ClaimVocabulary` by #73 and used by
  `Attestation` and the C06 claims; neither is on the base Claim. The Attestation and the full
  evidence shape are in [`docs/attestation-and-evidence.md`](attestation-and-evidence.md). Generated
  JSON Schema, SHACL and context artifacts belong to #74; no OWL artifact is planned.

[ADR-D1]: https://github.com/regen-network/regen-data-standards/blob/0cfe1c522754e4479baf7b931f272865d7c8f4e3/docs/adr/0001-claim-substance-canonicalization.md#d1--define-asserted-content-separately-from-lifecycle-and-derived-identity
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
