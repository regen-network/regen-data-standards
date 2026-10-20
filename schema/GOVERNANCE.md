# Schema Governance

**Status:** Proposed — tracks `koi-gov` manifesto v1.2.0 / v1.3.0 ratification.

Regen governs two adjacent and interdependent schema sets. This repository holds one of them.

| | Authority | Namespace |
|---|---|---|
| **Registry system** — projects, credit classes, methodologies, crediting programs, registries, credit protocols, claims, attestations, impacts, SDGs, geometry, taxonomies | **this repository** | `https://framework.regen.network/schema/` (prefix `rfs:`) |
| **Non-registry operational + knowledge** — RegenOS, Compass, work coordination, knowledge objects, decisions, specs | [`regen-network/koi-gov`](https://github.com/regen-network/koi-gov) | `orn:regen.<entity-class>:<context>/<reference>` |

**One-line test:** *does the schema describe an object the ecocredit registry issues, holds, or verifies?* If yes, it belongs here. If it describes how Regen itself works, decides, or publishes, it belongs to koi-gov.

## The contract

The full boundary contract — rules SGB-1 through SGB-7, the cross-domain reference inventory, and open items — is canonical in **[`koi-gov/docs/schema-governance-boundary-v1.md`](https://github.com/regen-network/koi-gov/blob/main/docs/schema-governance-boundary-v1.md)**. It is not restated here.

> **Link note:** that document currently lives on koi-gov branch `claude/koi-metadata-spine-v1.3.0` and the `main` link above resolves only once v1.2.0/v1.3.0 are ratified and merged. Merge koi-gov first, then this branch.

What matters for work in this repository:

- **Do not redefine koi-gov's concepts** (SGB-2). Access tiers, Publication targets, RID identity, and ledger-anchoring discipline are governed there and inherited here — including for registry schemas published to external surfaces.
- **Cross-domain references travel as RIDs** (SGB-3). RID v3 spans URI schemes and ORNs, so an `rfs:` IRI and an `orn:regen.*` ORN are both valid RIDs and no translation layer is needed. A slot that may hold either declares `range: uriorcurie` — as `Claim.supersedes` already does.
- **Changing a cross-domain slot requires notice to koi-gov before merge** (SGB-6). Current seam points: `Claim.supersedes`, `Attestation.attestsClaim`, `Attestation.hasReviewer`, `Claim.dataIri`. Adding a new one means adding it to the inventory in the boundary document.
- **Anchoring is one shared mechanism** (SGB-5). `Claim.contentHash` + `Claim.dataIri` are this domain's expression of the same Regen Ledger `x/data` `MsgAnchor` flow the koi-gov manifesto describes for KOI objects.

## Why the seam already exists

These schemas were built to interoperate before the boundary was written down. `Attestation.hasReviewer` requires "a registered identity (KOI entity URI and/or wallet address)" — that identity is `orn:regen.entity:org/<slug>`, defined in the koi-gov manifesto §RID. The boundary document records the connection rather than creating it.
