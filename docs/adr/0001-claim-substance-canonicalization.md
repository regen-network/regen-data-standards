# ADR 0001 — Claim substance & content-addressed canonicalization

- **Status:** Proposed (needs ratification by Darren + Shawn + JC)
- **Date:** 2026-07-15
- **Deciders:** Darren Zal (KOI claims engine), Shawn Anderson, Jeancarlo / JC (ybird-labs, RDF claims engine)
- **Relates to:** [`schema/src/Claim.yaml`](../../schema/src/Claim.yaml); the Output Record Contract (`docs/output-record-contract.md`, added in PR #55 — this ADR resolves that PR's open question #1); Regen Data Module on-chain anchoring.

## Context

Two claims engines are converging: KOI's operational engine (extraction → review → attestation → on-chain anchoring → federation) and JC's RDF-based engine, which contributes a **content-based identity** for a claim. The open question the team named on 2026-07-14 is *not* "which engine wins" — the answer there is **alongside, not migration**: JC provides an identity adapter; KOI keeps operational ownership. The real first decision is upstream of that:

> **What is the "substance" of a Claim — the exact set of Claim fields that constitute its content-addressed identity — and how is that substance canonicalized into a fingerprint?**

Get this wrong in the narrowing direction and the new identity **silently merges genuinely different claims**. Get the algorithm wrong and it either forks identical claims across engines or opens a denial-of-service surface on untrusted input.

### Evidence: the compatibility spike (2026-07-14)

A synthetic, offline compatibility spike (`RegenAI/scratch/jc-koi-canon-spike/`, RESULT.md) tested RDFC-1.0 canonicalization (pyoxigraph 0.5.9) + a digest over the canonical N-Quads. It produced **one load-bearing failure and two decision-forcing caveats**:

1. **Substance-collision (the load-bearing finding).** A naïve substance set of 5 fields — `(claimant, subject, statement, claim_type, asserted_at)` — **drops real claim substance** (`quantity`, `unit`, `credit class`, `impact`, `methodology`). Two materially different impact claims collapsed to one fingerprint and one IRI:

   ```
   A  quantity=100  creditClass=C04  unit=tonnes     -> fp e69fb077…
   B  quantity=5    creditClass=C05  unit=kilograms  -> fp e69fb077…   (IDENTICAL)
   ```

   KOI's incumbent BLAKE2b-256 anchor keeps A and B distinct; the naïve fingerprint merges them. **The proposed identity was strictly *less* discriminating than what it would replace.** This is the finding that must drive the substance definition.

2. **DoS non-conformance.** pyoxigraph 0.5.9's RDFC-1.0 passes all 64 W3C eval vectors but **fails the §4.4.3 DoS-defense MUST** — a poison "clique" graph does not terminate (SIGKILL after >90s). JC's engine ingests *external* claim graphs, so this is a live surface, not a theoretical one.

3. **Timestamp lexical-vs-value.** The fingerprint is taken over the *lexical* form of `xsd:dateTime`, so four representations of the **same instant** mint four different identities:

   ```
   2026-07-14T00:00:00Z  /  …+00:00  /  …000Z  /  2026-07-13T17:00:00-07:00   →  four distinct IRIs
   ```

   Two engines (Rust JC vs Python KOI) serializing the same instant differently would fork the identity of an identical claim.

What genuinely held: **determinism** (two syntactically different serializations of the same content converge), **no over-normalization** (~560 adversarial cases, 0 false collisions on IRIs/Unicode/literals), and **pure computation** (no production effect).

## Decision

### D1 — Substance = the full *what-is-claimed* field set, defined against `Claim.yaml`

A Claim's content-addressed identity is computed over its **substance projection**: the fields that determine *what is being claimed*, taken from the merged `Claim` schema. Lifecycle and provenance fields are **excluded** — they change over a claim's life without changing what is claimed.

**Substance (identity-bearing):**

| `Claim.yaml` field | Why it is substance |
|---|---|
| `hasClaimType` | The claim's category (ecological/social/…). |
| `hasClaimant` (Entity id) | *Who* asserts. May be a `COMMUNITY`. |
| `hasSubject` (Entity id) | *What/whom* it is about. |
| `hasOperator` (Entity id, if present) | Who produced the outcome, when distinct. |
| `hasPrimaryImpact` | **Dropped by the naïve model.** The impact claimed. |
| `hasCoBenefits` | Secondary impacts — part of what is claimed. |
| `quantity` + `quantityUnit` | **The A/B collision was exactly here.** 100 t ≠ 5 kg. |
| `hasCreditClass` | **The A/B collision was exactly here.** C04 ≠ C05. |
| `claimStartDate` / `claimEndDate` | The period the claim covers. |
| `usesMethodology` | **Dropped by the naïve model.** How it was measured. |

**Not substance (excluded — lifecycle / provenance / derived):**

| Field | Why excluded |
|---|---|
| `verificationStatus` | Moves `SELF_REPORTED → … → LEDGER_ANCHORED` over time; the same claim, more assured. Including it would re-mint identity on every review step. |
| `contentHash` | The fingerprint itself — cannot be an input to its own computation. |
| `dataIri` | Derived from `contentHash`. |
| `supersedes` | A version-chain pointer, not claimed content. |
| `name`, `description`, `url` | Human-facing presentation; not the asserted substance. |

Rationale: this is the minimal fix that makes the fingerprint **at least as discriminating** as KOI's incumbent anchor, closing the A1 collision, while keeping identity stable across a claim's verification lifecycle.

### D2 — Canonicalization algorithm

Two viable options; **this ADR recommends D2-b** and asks JC to confirm cross-engine parity:

- **D2-a — RDFC-1.0 over the substance graph.** Semantic-web native; matches JC's RDF engine directly. Determinism verified in the spike. **Cost:** carries the §4.4.3 DoS surface; requires a mandatory guard (D4) on any untrusted input; identity depends on the RDF encoding profile (namespace, literal-vs-IRI for `claim_type`), which must then itself be frozen.
- **D2-b — JCS (RFC 8785 canonical JSON) over the typed substance projection *(recommended)*.** A Claim has a **fixed LinkML shape**, not an arbitrary RDF graph, so we do not need graph canonicalization to get a deterministic serialization. Project the substance fields (D1) into a fixed-key-ordered JSON object (entities by canonical id, quantity as a normalized decimal, timestamps per D3), and hash the JCS bytes. **No blank nodes → the DoS surface in D4 disappears by construction.** JC can compute the identical projection from the RDF side; parity is defined at the *projection*, not the serialization.

The recommendation is D2-b because the claim is a typed record with a schema, JCS sidesteps the DoS MUST entirely, and it removes the "which RDF encoding profile" sub-decisions. D2-a stays on the table only if cross-engine parity with JC's existing RDF pipeline proves cheaper to hold at the N-Quads layer than at the projection layer.

### D3 — Timestamp & value normalization (applies to either algorithm)

Before fingerprinting, normalize value-typed fields to one canonical lexical form so equal *values* yield equal *bytes*:

- `xsd:dateTime` / dates → UTC, `Z` suffix, no fractional seconds unless semantically required (`2026-07-14T00:00:00Z`).
- `quantity` → a single canonical decimal form (fixed, e.g. no trailing zeros; unit kept separate in `quantityUnit`, never folded into the number).
- Entity references → their canonical KOI id / ORN RID, not a display label.

### D4 — DoS guard is mandatory for any untrusted input

Independent of algorithm: any canonicalization that can touch an untrusted claim graph (JC's engine ingests external claims) MUST run behind an **external wall-clock timeout and a blank-node / triple-count cap**, failing closed. D2-b removes the blank-node vector entirely; if D2-a is chosen, this guard is a hard release gate, not a nice-to-have.

### D5 — Hash function: BLAKE2b-256, to match the on-chain anchor

`Claim.contentHash` is documented as **BLAKE2b-256 for on-chain anchoring via Regen Data Module**. The spike used SHA-256 as a stand-in. The canonical fingerprint that lands in `contentHash` / `dataIri` MUST be **BLAKE2b-256** so the content-addressed identity and the ledger anchor are the same value — not two competing hashes over the same claim.

### D6 — Immutability invariant

The accepted-claim object that carries a fingerprint MUST be immutable *through its substance* (the spike found a `frozen=True` wrapper around a *mutable* substance dict, letting content desync from its stored fingerprint). Recompute-and-compare on read, or a deep-frozen substance, is required so a claim can never disagree with its own identity.

## Consequences

- **Positive:** the A1 collision closes (D1); the DoS MUST is satisfied by construction (D2-b/D4); identity is stable across verification lifecycle (D1 exclusions) and across engines/instants (D3); the fingerprint *is* the ledger anchor (D5). This directly fills the Output Record Contract's `rawContentHash` / `Claim.contentHash → dataIri` fields (PR #55, open question #1 resolved) without changing that envelope.
- **Negative / cost:** if D2-b is chosen, JC's RDF-native pipeline must compute the same substance projection (a defined adapter, not a migration). Freezing the substance field set is a compatibility commitment — adding a substance field later re-mints identities, so `supersedes` version chains must absorb any future substance-schema change.
- **Follow-ups:** (a) encode D1's substance set as a machine-checkable list next to `Claim.yaml` (so both engines read one source of truth); (b) verify byte-parity against `koi-processor`'s production `ledger_anchor.py` (out of scope for the spike); (c) decide D2-a vs D2-b with JC on the call.

## Open questions for the deciding call

1. **D2-a vs D2-b** — is cross-engine parity cheaper to hold at the RDFC-1.0 N-Quads layer (JC-native) or at a typed JCS projection (DoS-free)? *(Recommendation: D2-b.)*
2. Is `hasOperator` substance, or provenance? (This ADR counts it as substance when present.)
3. Do `hasCoBenefits` participate in identity, or only the primary impact? (This ADR includes them.)
4. Should a change in `usesMethodology` alone mint a new claim identity, or supersede the prior one?
5. Confirm BLAKE2b-256 (D5) against the live Regen Data Module anchor encoding.

---

*Evidence: `RegenAI/scratch/jc-koi-canon-spike/RESULT.md` (adversarial spike record, 2026-07-14). Real `Claim` shape: [`schema/src/Claim.yaml`](../../schema/src/Claim.yaml).*
