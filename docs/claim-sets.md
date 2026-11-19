# Claim sets

This document describes [`ClaimSet.yaml`](../schema/src/ClaimSet.yaml): the record for a claim set,
and the Claims that say something about a set. It builds on the base Claim in
[`docs/claim-base.md`](claim-base.md) and the evaluations in
[`docs/evaluation-and-evidence.md`](evaluation-and-evidence.md).

Two proposed decisions in `regen-network/claims` lead here:

- [ADR 0002](https://github.com/regen-network/claims/blob/20f89f8d4b9483945bc9c2c4c7a440db113def6b/docs/adr/0002-claim-and-claim-set-identity.md)
  ([regen-network/claims#60](https://github.com/regen-network/claims/pull/60)) defines a claim set
  and its identity ([D10, D11](https://github.com/regen-network/claims/blob/20f89f8d4b9483945bc9c2c4c7a440db113def6b/docs/adr/0002-claim-and-claim-set-identity.md#L110-L111)),
  and leaves the class and membership terms to this repository
  ([Q3](https://github.com/regen-network/claims/blob/20f89f8d4b9483945bc9c2c4c7a440db113def6b/docs/adr/0002-claim-and-claim-set-identity.md#L160)).
- [ADR 0006](https://github.com/regen-network/claims/blob/5d7fad6574255928973ce9745d57b62e27000352/docs/adr/0006-ledger-anchoring-and-attestation.md)
  ([regen-network/claims#69](https://github.com/regen-network/claims/pull/69)) says that an agent
  who signs off a set attests a Claim that names it, and leaves open how a statement about a set
  that is not a judgment is modelled
  ([Q2](https://github.com/regen-network/claims/blob/5d7fad6574255928973ce9745d57b62e27000352/docs/adr/0006-ledger-anchoring-and-attestation.md#L222)).
  In its review, [JC proposed](https://github.com/regen-network/claims/pull/69#discussion_r4553684010)
  one Claim type for each kind of statement, which this module follows.

## What a claim set is

A `ClaimSet` is a fixed set of exact Claim versions, each named by its ClaimIRI. Evaluations are
Claims, so they can be members too. The record holds its members and nothing else.

| Field | RDF term | Range | Card. | Meaning |
|---|---|---|---|---|
| `hasClaim` | `rfs:hasClaim` ⊑ `prov:hadMember` | IRI | 1..*, set | The ClaimIRI of each member. Order and repeats mean nothing. |

- **No name, creator or creation time.** Its IRI, the ClaimSetIRI, is computed from the record
  ([regen-network/claims#1](https://github.com/regen-network/claims/issues/1)), so the same members
  always give the same ClaimSetIRI, whoever lists them and whenever (ADR 0002 D10). Adding, removing
  or revising a member makes a different set. A name or a creator would give the same members several
  ClaimSetIRIs, so the closed shape rejects them
  ([example](../schema/examples/claim-set.SCHEMA-INVALID-with-name.yaml)).
- **At least one member.** ADR 0002 D10 rejects an empty set
  ([example](../schema/examples/claim-set.SCHEMA-INVALID-empty.yaml)).
- **One blank node.** In RDF the record is one blank node typed `rfs:ClaimSet`, with one
  `rfs:hasClaim` statement per member, the graph ADR 0002 D11 hashes:

  ```turtle
  [] a rfs:ClaimSet ;
      rfs:hasClaim <https://example.org/placeholder/claim-iri/c06-project-claim-mvp-001>,
          <https://example.org/placeholder/claim-iri/c06-cohort-claim-mvp-001> .
  ```

- **A PROV collection.** `ClaimSet` is a `prov:Collection` and `hasClaim` specializes
  `prov:hadMember`, so a PROV-aware query finds the members without knowing this schema.

The schema checks only that each member is an IRI. That it is the ClaimIRI of a Claim the service
admitted is checked by the service that records the set (ADR 0002 D10).

## Saying something about a set

A claim set asserts nothing and has no claimant, so nobody can sign it as its author. Whatever an
agent says about a set is its own record, which names the set by its ClaimSetIRI and has its own
claimant and assertion time. That record is what an agent attests on Regen Ledger (ADR 0006 Q2).

| What the agent says | Record | Schema change |
|---|---|---|
| A judgment of the set, such as a verifier's view of a package, or a registry decision about it | A `GenericEvaluation` or a `RequirementEvaluation` with the ClaimSetIRI in `hasTarget` | None. `EvidenceSupportEvaluation` and `ClaimConsistencyEvaluation` restrict their targets to `Evidence` records and claim versions, so they cannot name a set. |
| A statement that is not a judgment, such as a developer presenting a package as complete | A Claim of a claim type for that kind of statement, whose subject is the set | One claim type per kind of statement. The first is [`ClaimSetCompletenessClaim`](#claimsetcompletenessclaim). |

Each kind of statement has its own claim type, not a general "this Claim points to a set" slot on
the base Claim. A general slot would say that a Claim names a set, but not why. A claim type says
what the statement means, and its schema can require what that statement needs. The base Claim's
`reliesOn` names a premise, a Claim or Evaluation whose content this one rests on. It does not name
a set.

A proof pack for a verifier or auditor
([regen-network/claims#53](https://github.com/regen-network/claims/issues/53)) is a bundle of
records to hand over, not a statement, so it needs no claim type. A claim set can fix which Claims
it contains.

## `ClaimSetCompletenessClaim`

The claimants' statement that a claim set holds every Claim they present for a stated purpose, such
as a project developer's registration package for one project. `claimStatement` states the purpose.

| Field | RDF term | Range | Card. | Meaning |
|---|---|---|---|---|
| `hasSubject` | `rfs:hasSubject` | `ClaimSetSubject` (inlined) | 1 | The claim set presented as complete, by its ClaimSetIRI. |
| `governedBy` | `rfs:governedBy` | IRI | 0..*, set | Exact versions of the governing documents the set is presented under, such as a credit class version. |

It also has every base Claim field (`claimStatement`, `assertedBy`, `assertedAt` or `assertedOn`,
`hasEvidenceCitation`, `reliesOn`, `wasRevisionOf` and the rest).

- **Requirements are named on the members.** Which requirements each Claim in the set answers is
  stated on that Claim, with `addressesRequirement`. The completeness claim does not repeat it.
- **It states what the claimants present, not that the set is enough.** A reviewer who judges
  whether the set meets a checklist makes an Evaluation with the same ClaimSetIRI in `hasTarget`
  and the checklist version in `appliesRequirementSet`.
- **The members stay in the ClaimSet record.** The completeness claim names the set; it cannot list
  members itself ([example](../schema/examples/claim-set-completeness-claim.SCHEMA-INVALID-member-list.yaml)).
- **It cannot be a member of its own set.** Its ClaimIRI is computed from content that contains the
  ClaimSetIRI, so the set must exist first.
- **A fuller package is a new set.** Adding a Claim to a package makes a new claim set, and the
  claimants make a new `ClaimSetCompletenessClaim` about it, with `wasRevisionOf` naming the earlier
  completeness claim when the new package replaces it.

`ClaimSetSubject` is the `ClaimSubject` subclass for a set as a Claim's subject. It carries only the
ClaimSetIRI; the members are in the set's own record.

## Adding another claim type about sets

A new kind of statement about a set is a new claim type that narrows `hasSubject` to
`ClaimSetSubject` and adds what its statement needs:

```yaml
imports: [linkml:types, Claim, ClaimSet]
default_range: string
classes:
  ExampleSetStatementClaim:
    is_a: Claim
    slot_usage:
      hasSubject: {range: ClaimSetSubject}
    attributes:
      exampleField: {required: true}
```

A type is added when a workflow needs it, not ahead of time.

## Examples

| Example | Shows |
|---|---|
| [`claim-set.jsonld`](../schema/examples/claim-set.jsonld) | A `ClaimSet` of the four C06 example claims, named by placeholder ClaimIRIs |
| [`claim-set-completeness-claim.jsonld`](../schema/examples/claim-set-completeness-claim.jsonld) | A `ClaimSetCompletenessClaim`: the developer presents that set as its complete registration package for project P-001, under the C06 credit class |
| `claim-set*.SCHEMA-INVALID-*.yaml` | An empty set, a set with a name, and a completeness claim that lists members instead of naming a set |

`make -C schema check-claim-examples` checks both examples and the invalid documents with both
generated validators, as for the other claim examples.

## Open

- **The terms depend on proposed ADRs.** ADR 0002 and ADR 0006 are under review. Once
  `rfs:ClaimSet` and `rfs:hasClaim` are agreed, they are part of every claim set's hashed content,
  and changing either changes every ClaimSetIRI (ADR 0002 D11).
- **The examples use placeholder IRIs.** ClaimIRIs and ClaimSetIRIs are computed by the claim
  service ([regen-network/claims#20](https://github.com/regen-network/claims/issues/20)), so the
  examples use labelled placeholders, as the other claim examples do.
- **The validators cannot tell what an IRI names.** Neither checks that a `hasClaim` value is a
  ClaimIRI or that a completeness claim's subject is a ClaimSetIRI. The service checks both when it
  admits the records.
