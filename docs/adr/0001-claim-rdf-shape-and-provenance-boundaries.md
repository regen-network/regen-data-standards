# ADR 0001 — Claim RDF shape and provenance boundaries

- **Status:** Proposed. Revised 2026-10-05. No ratification recorded; acceptance follows the WP0 standards governance process.
- **Date:** 2026-07-15; scope revised 2026-09-08.
- **Proposed deciders:** Darren Zal, Shawn Anderson, Jeancarlo / JC, Marie Gauthier.
- **Implementation:** [base Claim #85](https://github.com/regen-network/regen-data-standards/pull/85), [LinkML upgrade #87](https://github.com/regen-network/regen-data-standards/pull/87), and [Attestation/Evidence/C06 #90](https://github.com/regen-network/regen-data-standards/pull/90). These PRs remain review-dependent.

## Context and scope

Consumers need a reusable RDF representation of an assertion, distinct from the activity it describes, its authoring trail, and changing review or anchoring state. This repository governs those data shapes and their interpretation. The [WP1-01 recommendations](https://github.com/regen-network/regen-data-standards/blob/d6654689d93aaa91068449de7d4c7010edbb6077/docs/research/claims-and-provenance-models.md) and the base Claim implementation make concrete proposals for the previously pending field choices.

This revision records those proposals for acceptance together. It does not declare the schema PRs approved. The service's identity recipe is [claims ADR 0002, PR #60](https://github.com/regen-network/claims/pull/60); canonicalizer deployment, digest choice, ledger operations and migration belong there and in the service work packages. This ADR changes no schema or validation rule itself.

## Proposed decisions

### D1 — Define asserted content separately from lifecycle and derived identity

A Claim is an attributed assertion made by one or more claimants about a subject at a stated time. An extraction draft without a claimant is an authoring candidate, not a Claim. A Claim needs no third-party attestation to be valid. Each version is immutable.

| Content | Proposed treatment |
|---|---|
| `name`, `description`, `url` | Keep on the base Claim. The title and the claimant's description are asserted content. `url` is a reader's pointer; evidence is cited with `hasEvidence`. These statements are not excluded from content because they appear presentational. |
| `hasSubject` | A required, inlined `ClaimSubject` node with its own IRI. The subject may be a place, project, dataset, agent or another claim; it is not restricted to the `Entity` agent class. Domain schemas may narrow its type. |
| `hasClaimant` | A nonempty, unordered set of agents taking responsibility for the whole assertion. It specializes `prov:wasAttributedTo`. A collective acting as one body is one claimant; its members do not thereby become co-claimants. A service that only transcribes or submits content is recorded in the authoring trail. |
| `assertedAt` | Required assertion time, distinct from observation, transcription, submission and ingestion time. The same content asserted at another time is another Claim. The base profile uses UTC whole-second timestamps ending in `Z`; authored values are validated before a converter can rewrite their lexical form. |
| `hasEvidence` | An optional, unordered set of typed Evidence nodes identifying the exact sources cited. It specializes `dcterms:references`. A citation does not itself establish support, derivation or integrity. |
| `wasRevisionOf` | Replace `supersedes` with `prov:wasRevisionOf` in Claim content, naming one exact immutable earlier version. Use it for a correction of the same assertion, not for a separate follow-up observation. The old version is unchanged; its attestations do not carry over. Selection of a current version and legacy logical-ID mappings stay outside content. |
| `hasOperator`, `claimStartDate`, `claimEndDate` | Remove from the generic Claim. An operator and the period of a domain activity belong on that activity in a specialized schema. Activity responsibility is `prov:wasAssociatedWith`, even when the operator is also the claimant. The assertion time does not stand in for the activity period. |
| Impact, quantity, credit-class and methodology fields | Keep domain requirements in specialized schemas. Include a value or a versioned rule/methodology reference when that particular assertion states it; a generic Claim does not require a crediting workflow. Reuse existing project/credit-class resources for their own descriptive fields. |
| `hasClaimType` | A universal required enum does not cover every assertion. Use the specialized RDF class to identify a claim's kind; retain the taxonomy for workflows that need it. This follows the concrete counterexample in [#86](https://github.com/regen-network/regen-data-standards/issues/86) and #90's removal of the base slot. |
| `verificationStatus`, `contentHash`, `dataIri` | Remove from Claim content, as agreed in July 2026. Review/anchor state is held in separate records; identity derived from the Claim's own canonical form is computed by the service. Neither is made an optional content field. |

Changing asserted content, including attribution, assertion time, evidence references or the exact predecessor reference, changes the service's identity input. That is different from updating an operational review status.

### D2 — Declare collection semantics in the schema

Every multivalued slot declares whether order has domain meaning. The base Claim's claimant and evidence collections are unordered sets, serialized as repeated RDF triples. A future ordered domain collection must preserve its sequence in RDF; `multivalued` or `inlined_as_list` alone does not define that sequence. Sorting serializer input cannot substitute for the schema declaration. Specialized schemas make the decision for their own fields.

### D3 — Reuse PROV-O without confusing agents, entities and activities

Claim versions are PROV Entities. The existing `Entity` class represents agents and aligns with `prov:Agent`; an activity aligns with `prov:Activity`. These alignments are declared by the mixins introduced in #85 and #90. `rfs:hasClaimant` specializes attribution of the assertion; `prov:wasAssociatedWith` describes responsibility for an activity. The attribution and activity roles remain distinct when one agent performs both.

Domain activities use `prov:startedAtTime` and `prov:endedAtTime` for timestamps, or date-typed terms such as `schema:startDate` and `schema:endDate` for calendar dates. Date-only values remain dates. Evidence is an Entity; its production activity is reached through `prov:wasGeneratedBy`, rather than treating the evidence as the activity.

`prov:wasRevisionOf` expresses a revision of the same assertion. A new assertion that merely builds on a prior one is not a revision. A methodology correction produces another immutable Claim, with a revision relation where appropriate; minting a version and expressing continuity are complementary.

### D4 — Keep review assertions and service state outside the target Claim

An attestation is a separate Claim subclass that states the issuer's judgment. When it names targets, those references identify exact immutable versions; it may also cite evidence. It does not mutate those targets. Program-specific findings and outcomes extend that subclass, as in #90. Admission, submission attempts, workflow status, anchoring status and selection of the current version are service records defined by the claims-engine work packages, including [claims#55](https://github.com/regen-network/claims/issues/55). This ADR imposes no companion lifecycle RDF class inferred from an implementation's database columns.

## Consequences and acceptance

Use `rfs:`/`rft:` and the repository's generated JSON-LD context under a pinned schema revision. Compact and expanded identifiers under that context are not alternative namespace choices. Required fields and inherited domain constraints must be checked against the most specific declared claim class; schema conformance is not a program verdict.

These proposed decisions replace the pending D1 table and provenance/period/revision questions in the September revision. Acceptance still requires the WP0 process and review of the schema implementations and their authored YAML/JSON-LD/RDF validation evidence. It does not approve the service identity recipe, a canonicalizer's safety, or a migration. Identifier policy for agents remains [#58](https://github.com/regen-network/regen-data-standards/pull/58), outside this content-boundary decision.

## Revision history

- **2026-10-05:** renamed the file to reflect its RDF-shape scope; proposed the remaining period, revision and PROV-O placements from #82/#85/#90; distinguished attestation content from operational state; linked service identity to claims#60. Acceptance remains unrecorded.
- **2026-09-24:** settled claimant attribution and moved operator responsibility to domain activities following review on #56 and #82.
- **2026-09-23:** carried forward removal of verification/derived-identity fields and placed domain fields in specialized schemas.
- **2026-09-08:** narrowed this ADR to RDF shape and moved service decisions to the implementation companion.
- Prior proposals and reversals remain in [the September revision](https://github.com/DarrenZal/regen-data-standards/blob/0cfe1c522754e4479baf7b931f272865d7c8f4e3/docs/adr/0001-claim-substance-canonicalization.md) and PR history. They are historical records.
