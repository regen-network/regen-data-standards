# ADR 0001 — Claim substance & content-addressed canonicalization

- **Status:** Proposed — **revised 2026-07-31**, D2 recommendation reversed (see the changelog at the foot). Needs ratification by Darren + Shawn + JC.
- **Date:** 2026-07-15, revised 2026-07-31
- **Deciders:** Darren Zal (KOI claims engine), Shawn Anderson, Jeancarlo / JC (ybird-labs, RDF claims engine)
- **Relates to:** [`schema/src/Claim.yaml`](../../schema/src/Claim.yaml); the Output Record Contract (`docs/output-record-contract.md`, added in PR #55 — this ADR resolves that PR's open question #1); Regen Data Module on-chain anchoring.

## Context

Two claims engines are converging: KOI's operational engine (extraction → review → attestation → on-chain anchoring → federation) and JC's RDF-based engine, which contributes a **content-based identity** for a claim. The open question the team named on 2026-07-14 is *not* "which engine wins" — the answer there is **alongside, not migration**: JC provides an identity adapter; KOI keeps operational ownership. The real first decision is upstream of that:

> **What is the "substance" of a Claim — the exact set of Claim fields that constitute its content-addressed identity — and how is that substance canonicalized into a fingerprint?**

Those five naïve fields are not a proposal — they are an **observation of the incumbent shape**, taken from koi-processor's current claim model (`api/routers/claims_router.py`, `ClaimCreateRequest`; the `claims` table in `migrations/064_claims_engine.sql`). The point of naming them is that this is what is live today and how it fails.

Get this wrong in the narrowing direction and the new identity **silently merges genuinely different claims**. Get the algorithm wrong and it either forks identical claims across engines or opens a denial-of-service surface on untrusted input.

### Evidence: the compatibility spike (2026-07-14)

A synthetic, offline compatibility spike — **published at [`koi-research/experiments/claim-canonicalization-spike-2026-07-14`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/README.md)**, permalinks pinned to the commit; [`RESULT.md`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/RESULT.md) is the full record — tested RDFC-1.0 canonicalization (pyoxigraph 0.5.9) + a digest over the canonical N-Quads. It produced **one load-bearing failure and two decision-forcing caveats**:

1. **Substance collision (the load-bearing finding).** A naïve substance set of 5 fields — `(claimant, subject, statement, claim_type, asserted_at)` — **drops real claim substance** (`quantity`, `unit`, `credit class`, `impact`, `methodology`). Two materially different impact claims collapsed to one fingerprint and one IRI:

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

Rationale: this is the minimal fix that makes the fingerprint **at least as discriminating** as KOI's incumbent anchor, closing the substance collision, while keeping identity stable across a claim's verification lifecycle.

**Exclusion is not enough — these slots should leave `Claim.yaml` altogether.** Raised in review, and it is the stronger position. Excluding a field from the substance projection still leaves it declared on the class, so every implementation must remember to exclude it and nothing detects the one that forgets. `verificationStatus`, `contentHash` and `dataIri` belong on a **separate versioned lifecycle record** that references the claim.

koi-processor **already works this way**, which makes this free rather than a migration: `verification` lives in its own column with an insert-only `claim_state_log` beside it (`migrations/064_claims_engine.sql`), and `ledger_anchor.py`'s canonical projection omits both it and `content_hash`. So the merged `Claim.yaml` declares a required `verificationStatus` on a class whose content hash deliberately excludes it — **the schema is out of step with the implementation, not the reverse.** Removing the three slots also shrinks the `sh:closed` violation surface currently blocking koi-processor PR #30.

The companion record does not exist yet in `schema/src`. Proposing it alongside the `Claim.yaml` change rather than inside this ADR.

### D2 — Canonicalization algorithm: **RDFC-1.0 (D2-a)**

> **Reversed 2026-07-31.** This ADR previously recommended **D2-b (JCS over a typed projection)**. That recommendation is **withdrawn**. The reason is not a cost re-estimate — it is a constraint neither option had been checked against.

**The decisive constraint: `MsgAttest` cannot accept a raw-bytes anchor.**

```protobuf
// regen-ledger/proto/regen/data/v2/tx.proto — MsgAttest
// content_hashes are the content hashes for anchored data. Only RDF graph
// data can be signed as its data model is intended to specifically convey
// semantic meaning.
repeated ContentHash.Graph content_hashes = 2;
```

The field is typed `ContentHash.Graph`, **not** `ContentHash` — a structural constraint, not a convention, and the CLI enforces it again (`x/data/client/tx.go`: *"can only attest to graph data types"*).

koi-processor anchors `ContentHash.Raw` today (`api/ledger_anchor.py`, `{"raw": {…, "file_extension": "json"}}` — the only anchor construction in the codebase). **So claims as we anchor them cannot be attested on-chain at all.** Attestation is the next layer of the claims engine, so D2-b would not merely sit outside the semantic path — it would foreclose a path we are actively building.

**Decision: D2-a — RDFC-1.0 over the substance graph**, anchored as `ContentHash.Graph` with `GRAPH_CANONICALIZATION_ALGORITHM_RDFC_1_0` and BLAKE2b-256 (D5).

Two corrections to the reasoning that had supported D2-b, recorded so the reversal is auditable rather than a change of mind:

- **"JCS is effectively the incumbent" was false.** Production computes `json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',',':'))`. That is deterministic JSON; it is **not** RFC 8785. JCS mandates UTF-8 output with minimal escaping (`ensure_ascii=True` does the opposite), key ordering by UTF-16 code unit rather than Python's code-point order, and ECMAScript `Number::toString` serialization. It was also a status-quo argument, and the incumbent is not even a clean substance projection — it hashes `claim_rid` and `entity_uri`, which are derived local identifiers rather than claimed content.
- **`ContentHash.Raw` argues against the raw path, not for it.** Its own doc comment: *"raw specifies 'raw' data which does not specify a deterministic, canonical encoding. Users of these hashes MUST maintain a copy of the hashed data which is preserved bit by bit."* That is the ledger declining to make the guarantee we wanted from it.

**The cost D2-a carries, stated honestly.** It needs an RDFC-1.0 canonicalizer in the serving path (the spike used `pyoxigraph` 0.5.9); the Claim→RDF substance projection, which does not exist yet and is the same missing piece koi-processor PR #30 names as its wiring blocker; a change to `derive_ledger_iri`, which hardcodes the `raw` variant; and **D4's guard becomes a hard release gate** rather than a recommendation, because RDFC-1.0 is now genuinely on the serving path.

**What remains open, and it is JC's call.** The objection raised in review — that JCS guarantees deterministic bytes for one JSON shape but not RDF-level equivalence — cuts the other way too: choosing D2-a means the **RDF encoding profile itself must be frozen** (namespace, literal-vs-IRI for `claim_type`, compact vs expanded IRIs), or the same class of false-fork reappears one layer down. `hasCoBenefits` is a live instance: it is `multivalued` + `inlined_as_list` with **no ordering declaration**, while other schemas in this repo do use `list_elements_ordered`. Set-vs-sequence must be settled explicitly (see D7) regardless of algorithm.

### D3 — Timestamp & value normalization (algorithm-independent)

Before fingerprinting, normalize value-typed fields to one canonical lexical form so equal *values* yield equal *bytes*:

- `xsd:dateTime` / dates → UTC, `Z` suffix, no fractional seconds unless semantically required (`2026-07-14T00:00:00Z`).
- `quantity` → a single canonical decimal form (fixed, e.g. no trailing zeros; unit kept separate in `quantityUnit`, never folded into the number).
- Entity references → their canonical KOI id / ORN RID, not a display label.

### D4 — DoS guard is mandatory for any untrusted input

**Mandatory, unconditionally, and now a release gate.** Any canonicalization that can touch an untrusted claim graph MUST run behind an **external wall-clock timeout and a blank-node / triple-count cap**, failing closed, in a worker isolated from the request path.

Under D2-a this is no longer hypothetical: the spike proved `pyoxigraph` 0.5.9 satisfies all 64 runnable W3C eval vectors yet **fails the §4.4.3 DoS-defence MUST** — a poison clique graph does not terminate (SIGKILL, rc=137). koi-processor is single-worker, so an unbounded canonicalization does not fail one request, it stalls the service. The guard is not a mitigation to schedule later; **D2-a does not ship without it.**

### D5 — Hash function: BLAKE2b-256, to match the on-chain anchor

`Claim.contentHash` is documented as **BLAKE2b-256 for on-chain anchoring via Regen Data Module**. The spike used SHA-256 as a stand-in. The canonical fingerprint that lands in `contentHash` / `dataIri` MUST be **BLAKE2b-256** so the content-addressed identity and the ledger anchor are the same value — not two competing hashes over the same claim.

### D6 — Immutability invariant

The accepted-claim object MUST be immutable *through its substance* — the spike found a `frozen=True` wrapper around a *mutable* substance dict, letting content desync from its stored fingerprint. Recompute-and-compare on read, or a deep-frozen substance, is required.

**Strengthened 2026-07-31, from review:** the earlier framing still had the claim carrying its own fingerprint, with `contentHash` excluded from the input by an exclusion list. That is the same defect one level up — it makes correctness depend on every implementation remembering to exclude the same field, and a reader cannot distinguish a correctly-excluded hash from an incorrectly-included one.

**The fingerprint is not a property of the claim; it is an index over it.** The claim object is pure substance. Identity lives in the versioned record that carries `claimRef` + `contentHash` + `dataIri` — the same record D1's exclusions imply. Canonicalization then becomes *total* over the object, with no exclusion list to get wrong, and D6's invariant is enforced by the object having nothing mutable in it rather than by a wrapper.

### D7 — Collection ordering must be declared

Any multivalued substance field must state whether it is a **set** or a **sequence**, because the two hash differently under any algorithm. `hasCoBenefits` is currently `multivalued` + `inlined_as_list` with no ordering declaration, while other schemas in this repo do use `list_elements_ordered` — so the distinction exists and this field simply has not made it.

**Decision:** substance collections are **sets**, canonicalized by sorting on the element's canonical identifier before serialization. A claim asserting co-benefits *{A, B}* is the same claim as one asserting *{B, A}*; ordering is a presentation artifact and must not fork identity. Fields where order is semantically meaningful must say so explicitly and be excluded from this rule.

### D8 — Migration: dual anchoring, not a re-mint

Adopting D2-a does **not** require re-minting every existing `content_hash` and `data_iri`, and this ADR explicitly does not ask for that.

- Existing `ContentHash.Raw` anchors **stay** as historical payload-integrity proofs. They remain true statements about the bytes they hashed.
- New claims mint a `ContentHash.Graph` / RDFC-1.0 fingerprint as their content-addressed identity, and become attestable.
- The claims schema gains **algorithm and profile/version columns** so every claim records which scheme minted its identity. `migrations/064_claims_engine.sql` and `070_data_iri.sql` have no such columns today — that absence is its own latent problem, independent of this decision, since the current schema cannot express *which* canonicalization produced a stored hash.
- Backfill of historical claims is optional and lazy. Anything never attested does not need a graph fingerprint.

This avoids a big-bang migration while refusing to pretend the old raw-JSON anchors carried RDF semantics.

## Consequences

- **Positive.** The substance collision closes (D1). Claims become **attestable**, which under the previous recommendation they would not have been (D2-a). Identity is stable across the verification lifecycle (D1 exclusions) and across engines and instants (D3). The fingerprint *is* the ledger anchor (D5). Collection ordering can no longer silently fork identity (D7). This fills the Output Record Contract's `Claim.contentHash → dataIri` fields (PR #55, open question #1) without changing that envelope — note that PR #55 now references claims rather than embedding them, which is consistent with identity living on the claim.
- **Negative / cost.** D2-a needs an RDFC-1.0 canonicalizer in the serving path, the Claim→RDF substance projection that does not yet exist, a change to `derive_ledger_iri`, and D4's guard as a hard release gate. The RDF encoding profile must be frozen or the false-fork risk moves down a layer. Freezing the substance field set is a compatibility commitment — adding a substance field later re-mints identities, so `supersedes` chains must absorb any future substance-schema change.
- **Rejected alternatives.** *D2-b (JCS over a typed projection)* — forecloses attestation; withdrawn. *Keep the incumbent raw-JSON anchor* — same problem, and it is not a clean substance projection. *Re-mint all existing hashes* — unnecessary given D8.
- **Follow-ups.** (a) Encode D1's substance set as a machine-checkable list beside `Claim.yaml`, so both engines read one source of truth. (b) Verify byte-parity against koi-processor's `ledger_anchor.py` once the RDF projection exists. (c) Propose the lifecycle/anchor companion record that D1's exclusions imply. (d) Add the algorithm/profile columns from D8.

## Open questions for the deciding call

1. **RDF encoding profile — @JeancarloBarrios.** D2-a makes the profile load-bearing. Which namespace, and is `claim_type` a literal or an IRI? Compact or expanded IRIs? This is the remaining place a false fork can hide, and it is the one question the code cannot answer for us.
2. **Does JC's engine already produce RDFC-1.0 canonical N-Quads over an equivalent substance set?** If yes, cross-engine parity is largely free and the adapter is thin.
3. Is `hasOperator` substance, or provenance? *(This ADR counts it as substance when present.)*
4. Do `hasCoBenefits` participate in identity, or only the primary impact? *(This ADR includes them, as an unordered set per D7.)*
5. Should a change in `usesMethodology` alone mint a new identity, or supersede? *(Answered in review: these are the **same operation**, not alternatives — a substance change mints a new identity **and** the new claim carries `supersedes` pointing at the old. The version chain preserves continuity; identity stability was never meant to do that job. Retained here only because it was posed as an either/or in the original.)*
6. Confirm BLAKE2b-256 (D5) against the live Regen Data Module anchor encoding — `DIGEST_ALGORITHM_BLAKE2B_256 = 1` is what `ledger_anchor.py` already sends.

---

## Changelog

**2026-07-31 — D2 reversed, D4 hardened, D6 strengthened, D7/D8 added.**
Prompted by @blushi's review, which argued for D2-a on the grounds that `ContentHash.Graph` declares only RDFC-1.0. Investigating that premise surfaced the stronger reason: `MsgAttest.content_hashes` is typed `ContentHash.Graph`, so the previously recommended D2-b would have made claims permanently un-attestable. Two supporting arguments for D2-b also failed on inspection — production runs deterministic `json.dumps`, not RFC 8785; and `ContentHash.Raw`'s doc comment disclaims the canonical-encoding guarantee the ADR had read into it. Review additionally established that the D1 exclusions should be removals from `Claim.yaml` rather than exclusions from the projection, and that a claim should not carry its own fingerprint at all.

**2026-07-15 — initial draft.** Recommended D2-b.

---

*Evidence: the compatibility spike is published at [`koi-research/experiments/claim-canonicalization-spike-2026-07-14`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/README.md) — [`RESULT.md`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/RESULT.md) is the full record, permalinks pinned to the commit so they survive branch changes. Its contemporaneous write-up (`ADR-jc-koi-canonicalization-profile.md`) predates this revision and argues for D2-b; it is preserved as-run rather than back-edited, because rewriting evidence after the conclusion changed is what makes a spike untrustworthy. Findings 1 and 3 are algorithm-independent; finding 2 becomes more load-bearing under D2-a, not less. Real `Claim` shape: [`schema/src/Claim.yaml`](../../schema/src/Claim.yaml).*
