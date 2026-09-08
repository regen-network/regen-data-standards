# ADR 0001 — Claim RDF shape and provenance boundaries

- **Status:** Proposed — revised 2026-09-08. No ratification recorded. Acceptance depends on the WP0 standards governance process.
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
| `hasPrimaryImpact`, `quantity`, `quantityUnit`, `hasCreditClass`, `claimStartDate`, `claimEndDate`, `usesMethodology` | Preserve the stated impact, amount/unit, classification, period and methodology in the relevant claim-type profile. | Validate applicability and RDF shape per claim type. Omission must not collapse material distinctions. |
| `hasCoBenefits` | Candidate additional asserted impacts. | Participation and collection semantics remain pending; see D7. |
| `verificationStatus`, `contentHash`, `dataIri` | Propose separating changing review state and derived identity from asserted content. | Decide the companion shape and references; do not assume JC’s crate already defines it or that migration is free. |
| `supersedes` | A relation between claim versions. | Decide which RDF record carries it and whether it is part of asserted content. |
| `name`, `description`, `url` | Inspect their meaning per claim-type profile. | Do not exclude them from identity merely because they look presentational; a description may contain asserted meaning. |

Changing identity-bearing content, including an assertion timestamp or attribution expressed in RDF, changes the input to a content-based fingerprint. A correction can produce a new claim with a relation to the previous one. Separating witnessed ingestion metadata does not imply all provenance is excluded from identity.

The precise companion model, whether PROV-O is used, and any removal of slots from Claim.yaml are still open. This documentation PR changes no schema or validation rule.

### D7 — Declare collection semantics in the schema

Propose set semantics for `hasCoBenefits` if order has no domain meaning; seek explicit confirmation. `multivalued`/`inlined_as_list` alone should not stand in for that decision. Any ordered collection must preserve its sequence in RDF. Sorting a serializer’s input is not a substitute for declaring how the RDF model represents order. This ADR does not impose one blanket rule on every future multivalued field.

## Standards boundaries already established

Use `rfs:`/`rft:` and the schema-generated JSON-LD context from this repository. Compact and expanded identifiers under the same pinned context are not alternative namespace choices. The implementation’s `claim_type` field must map to the schema’s `hasClaimType` according to that schema. Date-only values remain dates; timestamp lexical normalization belongs to an explicit type-aware implementation profile, not a rule that silently timezone-shifts dates.

## Open decisions and review continuity

Historical question numbers are retained here so existing review links remain interpretable.

1. **RDF namespace/compaction:** remove as an open choice. Existing namespaces and the generated context govern it, as clarified in review. Validate adapters against that context.
2. **JC implementation:** source evidence and the main/design/spike distinction are documented in the implementation companion. A suite name is not proof of an implemented canonicalizer, equivalent content, or parity.
3. **Claimant and operator:** decide asserted-provenance placement and the relevant profile fields in D1.
4. **Co-benefits:** decide inclusion and set/sequence semantics in D1/D7.
5. **Methodology change:** remove the false “new identity or supersede” choice. If it changes the accepted identity-bearing content it produces a new identity; a supersession relation can express continuity. Relation placement remains part of the schema discussion above.
6. **Digest suite:** moved to the implementation proposal; no digest algorithm is selected here.
7. **Lifecycle/provenance model:** define the separate state/identity references, if adopted, and PROV-O alignment. Do not infer a schema from one implementation’s storage columns.
8. **Raw-anchor migration:** moved to the implementation proposal. Consumer and deployment evidence is required before selecting cutover or transition.
9. **Declared schema references in identity:** moved to the implementation proposal. If an adopted profile requires schema declarations at a standards boundary, propose that shape explicitly in a subsequent schema change.

## Consequences and acceptance

This keeps schema review independently reviewable while retaining links to the implementation decisions it informs. Acceptance of the RDF shape will not ratify a service’s fingerprint suite or anchoring migration. Conversely, a successful service spike will not approve a pending schema choice.

Before acceptance, record decisions on the pending rows, verify the RDF examples/conversion against a pinned schema revision, resolve the provenance/state representation and follow the WP0 approval process. Cross-engine canonicalization and identity vectors are separate implementation acceptance evidence.

## Revision history

- **2026-09-08:** narrowed to RDF shape; pending choices made explicit; Marie retained among proposed deciders and ratification remains unrecorded; namespace and methodology review points reconciled. Service decisions formerly D2–D6 and D8–D9 move to the implementation companion. Prior presentation of service choices as settled, the broad Raw-attestation overstatement, and the claim that content/fingerprint parity was established are withdrawn.
- Earlier proposals and reversals remain in [the previous revision](https://github.com/DarrenZal/regen-data-standards/blob/52f61e911ccfb818d39083f66264a281edea92fe/docs/adr/0001-claim-substance-canonicalization.md) and PR history. They are historical records, not current implementation instructions.
