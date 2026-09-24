# ADR 0001 — Claim RDF shape and provenance boundaries

- **Status:** Proposed. Revised 2026-09-23. No ratification recorded. Acceptance depends on the WP0 standards governance process.
- **Date:** 2026-07-15; scope revised 2026-09-08.
- **Proposed deciders:** Darren Zal, Shawn Anderson, Jeancarlo / JC, Marie Gauthier. Listing a decider is not evidence of approval or an agreed package assignment.
- **Relates to:** [Claim.yaml at 0a4ba12a](https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml), [Output Record Contract #55](https://github.com/regen-network/regen-data-standards/pull/55), and the implementation companion in [koi-processor #54](https://github.com/gaiaaiagent/koi-processor/pull/54).

## Context and scope

Consumers need an explicit RDF representation of claim content and a distinction between asserted content, witnessed provenance and changing review/anchor state. This repository governs data shapes, namespaces and their interpretation. Service fingerprint framing, canonicalizer deployment, digest choice, ledger operations and database migration belong with their implementation.

An earlier version of this ADR mixed those responsibilities and presented pending substance choices as settled. This revision retains the RDF-shape proposal and moves the service work to `docs/claim-identity-proposal.md` in the implementation companion PR. Existing filenames remain stable for incoming links. **This ADR does not resolve #55’s canonicalization question or fill contentHash/dataIri by itself.**

The [historical compatibility spike](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/RESULT.md) illustrates why an incomplete content projection can collapse distinct claims. Its results are evidence about that experiment, not certification of a replacement service or a reason to ratify all proposed fields.

## Proposed RDF-shape decisions

### D1 — Define asserted content separately from lifecycle and derived identity

The following is a **candidate content profile**, not a merged change to Claim.yaml or a settled hashing field list. Any implementation must use the eventual accepted schema/profile revision.

| Existing slot | Proposed treatment | Decision still required |
|---|---|---|
| `hasClaimType`, `hasSubject` | Asserted content. | Confirm profile against intended claim types. |
| `hasClaimant` | Candidate asserted attribution in content. | Resolve in-content attribution versus separate assertion provenance; it remains pending. |
| `hasOperator` | Candidate asserted content where it describes the outcome. | Confirm meaning and placement; it remains pending. |
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

- **Claimant and operator:** decide asserted-provenance placement and the relevant profile fields in D1.
- **Methodology change:** the false “new identity or supersede” choice is removed, conditionally. If a methodology change alters the accepted identity-bearing content it produces a new identity, and a supersession relation can express continuity. Two things remain undefined: the claim-type content that carries the methodology reference, and the supersession relationship itself.
- **Lifecycle/provenance model:** define how external review state and the separate identity references are represented, and PROV-O alignment. [PR #82](https://github.com/regen-network/regen-data-standards/pull/82) is the input for the PROV-O part. It carries the WP1-01 findings for [#67](https://github.com/regen-network/regen-data-standards/issues/67) and is still under review. Do not infer a schema from one implementation’s storage columns.

## Consequences and acceptance

This keeps schema review independently reviewable while retaining links to the implementation decisions it informs. Acceptance of the RDF shape will not ratify a service’s fingerprint suite or anchoring migration. Conversely, a successful service spike will not approve a pending schema choice.

Before acceptance, record decisions on the pending rows, verify the RDF examples/conversion against a pinned schema revision, resolve the provenance/state representation and follow the WP0 approval process. Cross-engine canonicalization and identity vectors are separate implementation acceptance evidence.

## Revision history

- **2026-09-23:** carried forward the July 2026 agreement to remove `verificationStatus`, `contentHash` and `dataIri` from Claim.yaml, and placed impact, co-benefit, quantity, credit-class and methodology slots in specialized claim schemas, with co-benefit collection semantics to be decided in that scope. Namespace left the open decisions and methodology closes only conditionally, following review on [#70](https://github.com/regen-network/regen-data-standards/issues/70).
- **2026-09-08:** narrowed to RDF shape; pending choices made explicit; Marie retained among proposed deciders and ratification remains unrecorded; namespace and methodology review points reconciled. Service decisions formerly D2–D6 and D8–D9 move to the implementation companion. Prior presentation of service choices as settled, the broad Raw-attestation overstatement, and the claim that content/fingerprint parity was established are withdrawn.
- Earlier proposals and reversals remain in [the previous revision](https://github.com/DarrenZal/regen-data-standards/blob/52f61e911ccfb818d39083f66264a281edea92fe/docs/adr/0001-claim-substance-canonicalization.md) and PR history. They are historical records, not current implementation instructions.
