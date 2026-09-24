# ADR 0001 — Claim RDF shape and provenance boundaries

- **Status:** Proposed. Revised 2026-09-24. No ratification recorded. Acceptance depends on the WP0 standards governance process.
- **Date:** 2026-07-15; scope revised 2026-09-08.
- **Proposed deciders:** Darren Zal, Shawn Anderson, Jeancarlo / JC, Marie Gauthier. Listing a decider is not evidence of approval or an agreed package assignment.
- **Relates to:** [Claim.yaml at 0a4ba12a](https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml), [Output Record Contract #55](https://github.com/regen-network/regen-data-standards/pull/55), and the implementation companion in [koi-processor #54](https://github.com/gaiaaiagent/koi-processor/pull/54).

## Context and scope

Consumers need an explicit RDF representation of claim content and a distinction between asserted content, witnessed provenance and changing review/anchor state. This repository governs data shapes, namespaces and their interpretation. Service fingerprint framing, canonicalizer deployment, digest choice, ledger operations and database migration belong with their implementation.

The service work is in `docs/claim-identity-proposal.md` in the implementation companion PR. Existing filenames remain stable for incoming links. **This ADR does not resolve #55’s canonicalization question or fill contentHash/dataIri by itself.**

The [historical compatibility spike](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/RESULT.md) illustrates why an incomplete content projection can collapse distinct claims. Its results are evidence about that experiment, not certification of a replacement service or a reason to ratify all proposed fields.

## Proposed RDF-shape decisions

### D1 — Define asserted content separately from lifecycle and derived identity

The following is a **candidate content profile**, not a merged change to Claim.yaml or a settled hashing field list. Any implementation must use the eventual accepted schema/profile revision.

| Existing slot | Proposed treatment | Decision still required |
|---|---|---|
| `hasClaimType`, `hasSubject` | Asserted content. | Confirm profile against intended claim types. |
| `hasClaimant` | Asserted content: in-content attribution naming who takes responsibility for the assertion. Agreed in September 2026 ([review](https://github.com/regen-network/regen-data-standards/pull/56#discussion_r4092570377)). | None for placement. Declaring `rfs:hasClaimant` a subproperty of `prov:wasAttributedTo`, the preferred option in [#82 §3.1](https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md#31-what-constitutes-a-claim-and-who-asserts-it), belongs to the PROV-O alignment in Open decisions. |
| `hasOperator` | Not on the generic Claim. The operator is described on the relevant domain activity in the specialized claim schema, as responsibility for that activity (`prov:wasAssociatedWith`), not as attribution of the Claim. Operator responsibility stays explicit even when operator and claimant coincide, unlike the current Claim.yaml description (“if different from the claimant”). The activity description can remain in the specialized claim’s asserted content and contribute to its identity. See [PR #82 §3.2](https://github.com/regen-network/regen-data-standards/blob/c133c146871cae275ce001a76d89c07e4bbd4ce1/docs/research/claims-and-provenance-models.md#32-asserted-content-versus-provenance). | Define the activity shape and its participants per specialized schema. Emitting `prov:wasAssociatedWith` belongs to the PROV-O alignment in Open decisions. Add a Claim-level shortcut only for a demonstrated workflow need. |
| `hasPrimaryImpact`, `hasCoBenefits`, `quantity`, `quantityUnit`, `hasCreditClass`, `usesMethodology` | Belong to the relevant specialized claim schemas, not the generic Claim. The generic Claim does not assume an impact or crediting workflow. These slots can still contribute to a specialized claim’s identity. | Validate applicability and RDF shape per specialized schema. Omission must not collapse material distinctions. Co-benefit collection semantics are decided in that scope. See D2. The identity recipe over the composed claim is [claims#1](https://github.com/regen-network/claims/issues/1) (WP1-08). |
| `claimStartDate`, `claimEndDate` | Pending. This revision does not decide their placement. | Decide whether the claim period belongs on the generic Claim or in a specialized schema. Omission must not collapse material distinctions. |
| `verificationStatus` | Changing review state, excluded from asserted content. To be removed from Claim.yaml, not made optional. Agreed in July 2026 ([request](https://github.com/regen-network/regen-data-standards/pull/56#discussion_r3656696865), [agreement](https://github.com/regen-network/regen-data-standards/pull/56#discussion_r3693332604)). | Decide how external review state is represented. Discuss the shape with Jeancarlo before specifying it. Do not assume that migration is free. |
| `contentHash`, `dataIri` | Derived identity, excluded from asserted content. To be removed from Claim.yaml, not made optional, under the same July 2026 agreement. | Removal is agreed. Their derivation belongs to [claims#1](https://github.com/regen-network/claims/issues/1) (WP1-08). |
| `supersedes` | A relation between claim versions. | Decide which RDF record carries it and whether it is part of asserted content. |
| `name`, `description`, `url` | Inspect their meaning per claim-type profile. | Do not exclude them from identity merely because they look presentational; a description may contain asserted meaning. |

Changing identity-bearing content, including an assertion timestamp or attribution expressed in RDF, changes the input to a content-based fingerprint. A correction can produce a new claim with a relation to the previous one. Separating witnessed ingestion metadata does not imply all provenance is excluded from identity.

Removing `verificationStatus`, `contentHash` and `dataIri` from Claim.yaml is agreed, and that edit belongs to [#71](https://github.com/regen-network/regen-data-standards/issues/71). How external review state is represented and whether PROV-O is used are still open. This documentation PR changes no schema or validation rule.

### D2 — Declare collection semantics in the schema

A multivalued slot should declare whether its order has domain meaning. `multivalued`/`inlined_as_list` alone should not stand in for that decision. Any ordered collection must preserve its sequence in RDF. Sorting a serializer’s input is not a substitute for declaring how the RDF model represents order. This ADR does not impose one blanket rule on every future multivalued field. The set-versus-sequence decision for `hasCoBenefits` belongs to the specialized claim schema that carries it (see D1), not to this ADR.

## Standards boundaries already established

Use `rfs:`/`rft:` and the schema-generated JSON-LD context from this repository. Compact and expanded identifiers under the same pinned context are not alternative namespace choices. Date-only values remain dates; timestamp lexical normalization belongs to an explicit type-aware implementation profile, not a rule that silently timezone-shifts dates.

## Open decisions

- **Methodology change:** the false “new identity or supersede” choice is removed, conditionally. If a methodology change alters the accepted identity-bearing content it produces a new identity, and a supersession relation can express continuity. Two things remain undefined: the claim-type content that carries the methodology reference, and the supersession relationship itself.
- **Lifecycle/provenance model:** define how external review state and the separate identity references are represented, and PROV-O alignment. [PR #82](https://github.com/regen-network/regen-data-standards/pull/82) is the input for the PROV-O part. It carries the WP1-01 findings for [#67](https://github.com/regen-network/regen-data-standards/issues/67) and is still under review. Do not infer a schema from one implementation’s storage columns.

## Consequences and acceptance

This keeps schema review independently reviewable while retaining links to the implementation decisions it informs. Acceptance of the RDF shape will not ratify a service’s fingerprint suite or anchoring migration. Conversely, a successful service spike will not approve a pending schema choice.

Before acceptance, record decisions on the pending rows, verify the RDF examples/conversion against a pinned schema revision, resolve the provenance/state representation and follow the WP0 approval process. Cross-engine canonicalization and identity vectors are separate implementation acceptance evidence.

## Revision history

- **2026-09-24:** settled `hasClaimant` as asserted, in-content attribution, leaving its PROV subproperty declaration to the PROV-O alignment, and moved `hasOperator` off the generic Claim onto the relevant domain activity in specialized claim schemas, following review on [#56](https://github.com/regen-network/regen-data-standards/pull/56) and [#82](https://github.com/regen-network/regen-data-standards/pull/82) §3.2. Claimant and operator left the open decisions.
- **2026-09-23:** carried forward the July 2026 agreement to remove `verificationStatus`, `contentHash` and `dataIri` from Claim.yaml, and placed impact, co-benefit, quantity, credit-class and methodology slots in specialized claim schemas, with co-benefit collection semantics to be decided in that scope. Namespace left the open decisions and methodology closes only conditionally, following review on [#70](https://github.com/regen-network/regen-data-standards/issues/70).
- **2026-09-08:** narrowed to RDF shape; pending choices made explicit; Marie retained among proposed deciders and ratification remains unrecorded; namespace and methodology review points reconciled. Service decisions formerly D2–D6 and D8–D9 move to the implementation companion. Prior presentation of service choices as settled, the broad Raw-attestation overstatement, and the claim that content/fingerprint parity was established are withdrawn.
- Earlier proposals and reversals remain in [the previous revision](https://github.com/DarrenZal/regen-data-standards/blob/52f61e911ccfb818d39083f66264a281edea92fe/docs/adr/0001-claim-substance-canonicalization.md) and PR history. They are historical records, not current implementation instructions.
