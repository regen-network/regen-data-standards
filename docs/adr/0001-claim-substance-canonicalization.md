# ADR 0001 — Claim substance & content-addressed canonicalization

- **Status:** Proposed — **revised 2026-08-06** (D2 rationale re-grounded on the v2 enum and on four live mainnet `MsgAttest`; D8 collapsed and then re-based on a chain-wide anchor census; JC-assumption claim withdrawn). D2 recommendation was reversed 2026-07-31. See the changelog at the foot. Needs ratification by Darren + Shawn + JC.
- **Date:** 2026-07-15, revised 2026-07-31 and 2026-08-06
- **Deciders:** Darren Zal (KOI claims engine), Shawn Anderson, Jeancarlo / JC (ybird-labs, RDF claims engine)
- **Relates to:** [`schema/src/Claim.yaml`](https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml); the Output Record Contract ([`docs/output-record-contract.md`](https://github.com/DarrenZal/regen-data-standards/blob/e2c2b8448d228d2aa10faa91e95df2edaa7e67c2/docs/output-record-contract.md), added in PR #55 — this ADR resolves that PR's open question #1); Regen Data Module on-chain anchoring.

**Pinned sources.** Every code citation below is pinned so a future reader reasons about the same bytes this ADR did. `regen-ledger` refs are at [`451c3a3f`](https://github.com/regen-network/regen-ledger/tree/451c3a3f4353fc0d5a82383f2616a284baffa96f); `koi-processor` refs are at `regen-prod` [`c08c0a7e`](https://github.com/gaiaaiagent/koi-processor/tree/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95) (the deployed branch); `regen-data-standards` schema refs are at [`0a4ba12a`](https://github.com/regen-network/regen-data-standards/tree/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae). Line numbers are a convenience; the symbol name is the durable anchor.

## Context

Two claims engines are converging: KOI's operational engine (extraction → review → attestation → on-chain anchoring → federation) and JC's RDF-based engine, which contributes a **content-based identity** for a claim. The open question the team named on 2026-07-14 is *not* "which engine wins" — the answer there is **alongside, not migration**: JC provides an identity adapter; KOI keeps operational ownership. *(That framing is the team's from 2026-07-14. This ADR does not describe JC's implementation — where its shape matters, it is booked as an open question rather than assumed.)* The real first decision is upstream of that:

> **What is the "substance" of a Claim — the exact set of Claim fields that constitute its content-addressed identity — and how is that substance canonicalized into a fingerprint?**

Those five naïve fields are not a proposal — they are an **observation of the incumbent shape**, taken from koi-processor's current claim model ([`api/routers/claims_router.py`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/api/routers/claims_router.py), `ClaimCreateRequest`; the `claims` table in [`migrations/064_claims_engine.sql`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/migrations/064_claims_engine.sql)). The point of naming them is that this is what is live today and how it fails.

Get this wrong in the narrowing direction and the new identity **silently merges genuinely different claims**. Get the algorithm wrong and it either forks identical claims across engines or opens a denial-of-service surface on untrusted input.

### Evidence: the compatibility spike (2026-07-14)

A synthetic, offline compatibility spike — **published at [`koi-research/experiments/claim-canonicalization-spike-2026-07-14`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/README.md)**, permalinks pinned to the commit; [`RESULT.md`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/RESULT.md) is the full record — tested RDFC-1.0 canonicalization (pyoxigraph 0.5.9) + a digest over the canonical N-Quads. It produced **one load-bearing failure and two decision-forcing caveats**:

1. **Substance collision (the load-bearing finding).** A naïve substance set of 5 fields — `(claimant, subject, statement, claim_type, asserted_at)` — **drops real claim substance** (`quantity`, `unit`, `credit class`, `impact`, `methodology`). Two materially different impact claims collapsed to one fingerprint and one IRI:

   ```
   A  quantity=100  creditClass=C04  unit=tonnes     -> fp e69fb077…
   B  quantity=5    creditClass=C05  unit=kilograms  -> fp e69fb077…   (IDENTICAL)
   ```

   KOI's incumbent BLAKE2b-256 anchor keeps A and B distinct; the naïve fingerprint merges them. **The proposed identity was strictly *less* discriminating than what it would replace.** This is the finding that must drive the substance definition.

2. **DoS non-conformance.** pyoxigraph 0.5.9's RDFC-1.0 passes all 64 W3C eval vectors but **fails the §4.4.3 DoS-defense MUST** — a poison "clique" graph does not terminate (SIGKILL after >90s). Any engine that canonicalizes claim graphs it did not author is exposed here, so this is a live surface, not a theoretical one.

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

**Exclusion is not enough — these slots should leave `Claim.yaml` altogether.** Excluding a field from the substance projection still leaves it declared on the class, so every implementation must remember to exclude it and nothing detects the one that forgets. `verificationStatus`, `contentHash` and `dataIri` belong on a **separate versioned lifecycle record** that references the claim.

koi-processor **already works this way**, which makes this free rather than a migration: `verification` lives in its own column with an insert-only `claim_state_log` beside it ([`migrations/064_claims_engine.sql`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/migrations/064_claims_engine.sql)), and [`ledger_anchor.py`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/api/ledger_anchor.py#L31-L58)'s canonical projection (`_canonical_claim_json`) omits both it and `content_hash`. So the merged `Claim.yaml` declares a required `verificationStatus` on a class whose content hash deliberately excludes it — **the schema is out of step with the implementation, not the reverse.** Removing the three slots also shrinks the `sh:closed` violation surface currently blocking koi-processor PR #30.

**The companion record's shape is open, and it needs JC in the room.** An earlier version of this thread said JC's work already assumes this shape. That was wrong and is withdrawn: @blushi, who is closer to that codebase, reports that JC's work maps the claim IRI to the graph through `ClaimValue`, that versioned status is handled differently, and that **there are no corresponding shapes in his work at all** — what exists are `ClaimCandidate` and snapshots, which cover roughly the same lifecycle ground by a different route. This ADR therefore asserts nothing about what JC's engine assumes. Whether the lifecycle/anchor record is a new class in `schema/src`, an alignment onto `ClaimCandidate`/snapshots, or something else is **an open item for a call with JC** (see Open Questions), not a decision to be taken in this PR.

### D2 — Canonicalization algorithm: **RDFC-1.0 (D2-a)** — the data module's own name for it

> **Reversed 2026-07-31, re-grounded 2026-08-06.** This ADR previously recommended **D2-b (JCS over a typed projection)**. That recommendation is **withdrawn**. The reason is not a cost re-estimate — it is a pair of constraints neither option had been checked against.

**RDFC-1.0 is not a preference this ADR argues for. It is the only algorithm the data module we anchor against names.**

Production targets **`regen.data.v2`**. The evidence is in our own code: `derive_ledger_iri` sends `"file_extension": "json"` ([`api/ledger_anchor.py#L304-L322`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/api/ledger_anchor.py#L304-L322)), and `file_extension` is a **v2-only** field — v1's `ContentHash.Raw` has no such field, it carries a `RawMediaType media_type = 3` enum instead ([`v1/types.proto#L22-L33`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/proto/regen/data/v1/types.proto#L22-L33)).

And v2's canonicalization registry has exactly one non-zero entry, which is RDFC-1.0 by name:

```protobuf
// regen-ledger/proto/regen/data/v2/types.proto:84-91
enum GraphCanonicalizationAlgorithm {
  // unspecified and invalid
  GRAPH_CANONICALIZATION_ALGORITHM_UNSPECIFIED = 0;

  // RDFC 1.0 graph canonicalization algorithm. Essentially the same as URDNA2015 with some
  // small clarifications around escaping of escape characters.
  GRAPH_CANONICALIZATION_ALGORITHM_RDFC_1_0 = 1;
}
```

[`proto/regen/data/v2/types.proto#L84-L91`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/proto/regen/data/v2/types.proto#L84-L91). So the choice is not JCS-vs-RDFC — it is RDFC-1.0 or nothing the module can label.

**The v1 → v2 rename, spelled out so a future reader is not confused.** v1 declares the *same wire value* under the old name: `GRAPH_CANONICALIZATION_ALGORITHM_URDNA2015 = 1` ([`v1/types.proto#L127-L135`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/proto/regen/data/v1/types.proto#L127-L135)). "URDNA2015" in older Regen material and "RDFC-1.0" here therefore denote the **same enum slot**. They are not the same spec text, and the shared wire value `1` is a trap rather than a reassurance: two implementations can stamp the identical algorithm byte and still produce different canonical N-Quads for a graph containing escape characters. Choosing D2-a means choosing the v2 **spec**, not merely the byte — and v2 does not check the byte for us (`ContentHash_Graph.Validate`, [`x/data/types.go#L55-L66`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/x/data/types.go#L55-L66), rejects only `== 0`; in v2 the field is a plain `uint32`, not enum-typed). Client-side correctness is the only control.

**The second, independent constraint — `MsgAttest` cannot accept a raw-bytes anchor at all.**

```protobuf
// regen-ledger/proto/regen/data/v2/tx.proto:93-96 — MsgAttest
// content_hashes are the content hashes for anchored data. Only RDF graph
// data can be signed as its data model is intended to specifically convey
// semantic meaning.
repeated ContentHash.Graph content_hashes = 2;
```

[`v2/tx.proto#L93-L96`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/proto/regen/data/v2/tx.proto#L93-L96), identical in [`v1/tx.proto#L88-L91`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/proto/regen/data/v1/tx.proto#L88-L91). The field is typed `ContentHash.Graph`, **not** `ContentHash` — a structural constraint, not a convention, and the CLI enforces it again ([`x/data/client/tx.go#L110`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/x/data/client/tx.go#L110): *"can only attest to graph data types"*).

koi-processor anchors `ContentHash.Raw` today (`derive_ledger_iri`, `{"raw": {…, "file_extension": "json"}}` — the only claim-anchor construction in the codebase). **So claims as we anchor them cannot be attested on-chain at all.** Attestation is the next layer of the claims engine, so D2-b would not merely sit outside the semantic path — it would foreclose a path we are actively building. @blushi had made this point months before the ADR was written: if we want data attested, it should not be anchored as raw JSON. The ADR should have started there.

**And this is not a hypothetical next layer — Graph attestation is already live practice on this chain.** The same census behind D8 finds **four `MsgAttest` transactions on Regen mainnet**: 2026-07-13 (heights 27852490 and 27852917), 2026-07-19 (27942757) and **2026-08-03** (28159777) — the most recent three days before this revision. All four are from `regen1jfheyvsah5wqfyawmedme43te056z8gzdnpf3j`, and **every one carries `canonicalization_algorithm: 1`** — RDFC-1.0, the exact algorithm D2-a selects. *(We have not attributed that account; the census identifies a sender, not an operator.)*

That is the **positive** case for D2-a, and it is a much stronger one than the negative case this ADR previously leaned on ("we have nothing to lose"). Someone is attesting Graph-anchored data with this algorithm, on this chain, this month. Every claim our engine has anchored is structurally excluded from doing the same — and Raw anchoring is the only thing keeping us off that path.

**Decision: D2-a — RDFC-1.0 over the substance graph**, anchored as `ContentHash.Graph` with `canonicalization_algorithm = 1` (`GRAPH_CANONICALIZATION_ALGORITHM_RDFC_1_0`, v2) and BLAKE2b-256 (D5).

Two corrections to the reasoning that had supported D2-b, recorded so the reversal is auditable rather than a change of mind:

- **"JCS is effectively the incumbent" was false.** Production computes `json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',',':'))` ([`ledger_anchor.py#L58`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/api/ledger_anchor.py#L58)). That is deterministic JSON; it is **not** RFC 8785. JCS mandates UTF-8 output with minimal escaping (`ensure_ascii=True` does the opposite), key ordering by UTF-16 code unit rather than Python's code-point order, and ECMAScript `Number::toString` serialization. It was also a status-quo argument, and the incumbent is not even a clean substance projection — it hashes `claim_rid` and `entity_uri`, which are derived local identifiers rather than claimed content.
- **`ContentHash.Raw` argues against the raw path, not for it.** Its own doc comment ([`v1/types.proto#L8-L15`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/proto/regen/data/v1/types.proto#L8-L15)): *"Raw specifies 'raw' data which does not specify a deterministic, canonical encoding. Users of these hashes MUST maintain a copy of the hashed data which is preserved bit by bit."* That is the ledger declining to make the guarantee we wanted from it.

**A live divergence D2-a inherits, named here so it is not discovered later.** The deployed graph path already runs a canonicalizer, and it is not RDFC-1.0: `generate_graph_iri` calls `pyld.jsonld.normalize(doc, {"algorithm": "URDNA2015", "format": "application/n-quads"})` ([`ledger_anchor.py#L226-L241`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/api/ledger_anchor.py#L226-L241)) and `_content_hash_graph_to_iri` stamps the constant `_GRAPH_CANON_URDNA2015 = 1` ([`#L158`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/api/ledger_anchor.py#L158)). That path serves *attestation records*, not claims — but it means the codebase will hold two graph canonicalizers naming different specs while writing the same byte `1`, and the chain will not flag it. Any PR touching this path must state which spec it runs and reconcile against that constant.

**The cost D2-a carries, stated honestly.** It needs an RDFC-1.0 canonicalizer in the serving path (the spike used `pyoxigraph` 0.5.9); the Claim→RDF substance projection, which does not exist yet and is the same missing piece koi-processor PR #30 names as its wiring blocker; a change to `derive_ledger_iri`, which hardcodes the `raw` variant; reconciliation with the URDNA2015 constant above; and **D4's guard becomes a hard release gate** rather than a recommendation, because RDFC-1.0 is now genuinely on the serving path.

**What remains open, and it must be settled *with* JC rather than assumed on his behalf.** The objection raised in review — that JCS guarantees deterministic bytes for one JSON shape but not RDF-level equivalence — cuts the other way too: choosing D2-a means the **RDF encoding profile itself must be frozen** (namespace, literal-vs-IRI for `claim_type`, compact vs expanded IRIs), or the same class of false-fork reappears one layer down. `hasCoBenefits` is a live instance: it is `multivalued` + `inlined_as_list` with **no ordering declaration**, while other schemas in this repo do use `list_elements_ordered`. Set-vs-sequence must be settled explicitly (see D7) regardless of algorithm.

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

### D8 — Migration: cut over to Graph. *Our* Raw corpus is eight throwaway fixtures.

> **Rewritten twice on 2026-08-06.** This section originally specified a **dual-anchoring** period, on the premise that a body of existing `ContentHash.Raw` claim anchors had to be preserved and backfilled lazily — a premise asserted, never checked. The first rewrite checked it and over-corrected, concluding there was *"no production Raw corpus"* on mainnet and that a chain-wide census was impossible from a query node. **Both of those were false.** A chain-wide census has now been run, and Raw anchoring on Regen mainnet is a live, ordinary path. The dual-anchor machinery still goes, but for a narrower and better-supported reason, and every statement about our own anchoring is now scoped explicitly to our signing key.

**Evidence, in two layers. The distinction between them is the thing the previous revision collapsed.**

*Layer 1 — the chain.* A census over the tx index for `/regen.data.v2.MsgAnchor`, covering **2026-02-24 → 2026-08-05**, returns **950 anchor transactions: 418 `Raw` and 532 `Graph`.** Raw by sender:

| Raw anchors | Sender | |
|---:|---|---|
| 399 | `regen1ugps77ux3l9cqe7g3pjdqfs6lgz2uq7y5ky2xl` | also sends 528 of the 532 Graph anchors — the registry service account |
| 10 | `regen1wkc7x2465hhmr57fc300yxu84p78u3ystue5p5` | all `json`; unattributed |
| **8** | **`regen15eexs5vt9klzf304v2fczfh2823lwgz8g4apt9`** | **the claims engine — ours** |
| 1 | `regen1jfheyvsah5wqfyawmedme43te056z8gzdnpf3j` | `json`; also the sender of all four mainnet `MsgAttest` |

By file extension, chain-wide Raw is overwhelmingly documents and images rather than claim JSON: **pdf 259, jpeg 58, jpg 50, png 24, json 19, webp 5, heic 2, bin 1**. Two consequences worth stating because the previous revision got each of them wrong:

- **"The registry's own data is already all-Graph" is misleading.** It holds for ecocredit *metadata IRIs* — 13/13 credit classes, 187/187 projects and 80/80 batches carry `.rdf` IRIs resolving to `graph.canonicalization_algorithm: 1`, and with `pagination.count_total=true` those are complete censuses, not samples. But the same registry account anchored **399 Raw** in this window, mostly PDFs. Raw is that account's live document-attachment path, running alongside its Graph metadata path.
- **Our share is 8 of 418 — 1.9%.** "Raw anchoring on mainnet is essentially just our dogfooding" was wrong by roughly a factor of 52, and is withdrawn. **363 Raw anchors were made after our last one**, the most recent on **2026-08-05T17:31:53Z**. Raw anchoring is not winding down; we simply stopped.

*Layer 2 — our signing key,* `regen15eexs5vt9klzf304v2fczfh2823lwgz8g4apt9`. This is now exhaustive by construction rather than by enumeration: the account reports **`sequence: 9`** — the lifetime count of transactions it has signed — and a tx-index query for that sender returns **exactly 9**: 8 × `/regen.data.v2.MsgAnchor` + 1 × `/cosmos.bank.v1beta1.MsgSend` (height 25956958, 2026-03-11T20:21:10Z). Nine signed, nine found, eight anchors — there is no room for a tenth. *(This supersedes the previous revision's `UNVERIFIED` note about an unexplained ninth transaction: it was the `MsgSend`.)*

Those eight are **4 claims** (2026-03-11T18:09:36, 18:09:53, 2026-03-30T20:21:00, 2026-04-23T16:54:28) and **4 attestation blobs** (2026-03-11, anchored via `MsgAnchor`), all `"raw": {…, "file_extension": "json"}, "graph": null`, every hash matching the production DB `content_hash` byte for byte. Every one is test or demo content: two explicit fixtures (claimant `orn:personal-koi.entity:claims-engine-test-org`, statements reading *"Test organization restored 50 hectares… (run 1773215949)"*), one demo org `cec_demo_001`, one seed sample about Regen itself. **Zero are third-party ecological claims, and this key has anchored nothing since 2026-04-23.**

Neither of our accounts has executed a `MsgAttest`: `AttestationsByAttestor` returns `total: 0` for both, and the laptop key `regen14nekysjjlq6gl4c6qe57jknz4mm7lujtgnm0qc` has `pub_key: null` and `sequence: 0` — it has never signed anything on mainnet. The local `personal_koi` database nonetheless holds 8 claims marked `ledger_anchored`, and all 8 IRIs return not-found on chain. `derive_ledger_iri` **does** contact a node — it shells out to `regen q data convert-hash-to-iri … --node $REGEN_RPC_URL` — but only to convert a hash into an IRI; **it never checks whether an anchor for that IRI exists**. A local `ledger_anchored` status therefore does not imply anchored, and the precondition that gates it ([`claims_router.py#L366-L372`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/api/routers/claims_router.py#L366-L372)) requires only that `content_hash` and `ledger_iri` are non-empty.

**Decision:**

- New claims anchor as `ContentHash.Graph` / RDFC-1.0. **No dual-anchor period, and no dual-anchor machinery.**
- **The reason is the size of our corpus, not the absence of a corpus on the chain.** Re-anchoring eight throwaway fixtures is not a migration, so dual-anchor machinery is unpaid-for complexity — the preserved bytes read *"Test organization… (run 1773215949)"*. It is **not** because Raw is unused on mainnet; 418 anchors say otherwise.
- The eight existing Raw anchors are re-anchored or abandoned as a one-off.
- Backfill is not *optional and lazy* — it is **unnecessary**. Nothing of ours has ever been attested, so nothing needs a graph fingerprint retroactively.
- Note for anyone tempted by a re-label: moving an anchor from Raw to Graph **mints a new IRI**. The hash-type prefix byte is part of the base58check payload (`IriPrefixRaw = 0` / `IriPrefixGraph = 1`, [`x/data/iri.go#L26-L31`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/x/data/iri.go#L26-L31), written by `ContentHash_Raw.ToIRI` / `ContentHash_Graph.ToIRI`, [`#L33-L69`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/x/data/iri.go#L33-L69)). "Keep the IRI and attest it later" was never an available option.

**The question this decision does not answer, named rather than assumed away.** Dual-anchoring buys one thing besides migration: **forward interoperability during a transition** — a Raw IRI that some counterparty already dereferences keeps resolving while the Graph anchor lands. **No evidence gathered here addresses that.** *"Our corpus is small"* answers *is re-minting expensive*; it does not answer *does anyone else read our Raw anchors*. Two mainnet accounts we cannot attribute are anchoring Raw JSON in roughly our shape (`regen1wkc7x…`, 10; `regen1jfhey…`, 1), and **none of their 11 hashes matches either claims database** — so they are not ours, and we do not know whose they are. If any consumer resolves our IRIs, this decision needs a transition window after all. **Booked as Open Question 8.**

**Bounds, so the census is not over-read.**

- The window is a **lower bound on chain history, not the whole chain.** The queried node's tx index begins at height 25498036 (**2026-02-09T07:58:59Z**), not at genesis, so any anchor older than that is invisible to this method. The earliest anchor *found* is 2026-02-24.
- **Two transports, and they agree on their overlap — not on a single number.** The REST `cosmos/tx/v1beta1/txs` message-type query against the deeper-indexed node returns **950**; Tendermint `tx_search` against a node pruned to height 27420001 returns **815** — and exactly **815 of the 950** are at or above 27420001. The counts differ only by each node's index floor. *(An earlier framing of this evidence claimed both transports returned 950. They do not; the reconciliation above is what was actually checked.)*
- `x/data` v2 exposes **no list RPC** — all 11 query RPCs are keyed lookups ([`v2/query.proto`](https://github.com/regen-network/regen-ledger/blob/451c3a3f4353fc0d5a82383f2616a284baffa96f/proto/regen/data/v2/query.proto)). That premise is true, but the conclusion previously drawn from it — that a chain-wide Raw census is therefore impossible — is a non-sequitur and is **withdrawn**: the tx index, not the data module, is the right instrument.
- The claim-level detail (statements, claimants, hash parity) additionally rests on `AnchorByIRI` per stored claim IRI — a current-state lookup, unaffected by index pruning — validated first against a **positive control**, a real C01 batch IRI that returns a full anchor record, without which a "not found" would mean nothing.

The practical effect on this ADR: the migration burden that formed part of D2-a's cost largely disappears — for our corpus, and subject to Open Question 8.

### D9 — Every stored hash must record the scheme that minted it

Promoted out of D8, where it sat as one bullet. It survives the rewrite above because it is about telling **future** schemes apart, not legacy ones.

[`migrations/064_claims_engine.sql`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/migrations/064_claims_engine.sql) and [`070_data_iri.sql`](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/migrations/070_data_iri.sql) have **no algorithm, profile or version column**. Verified rather than assumed: `grep -inE 'algorithm|profile|canonical|rdfc|urdna|jcs'` over both files at `c08c0a7e` returns exactly one hit — a comment on [line 41 of 064](https://github.com/gaiaaiagent/koi-processor/blob/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95/migrations/064_claims_engine.sql#L41), `content_hash TEXT, -- BLAKE2b-256 of canonical form`. The schema cannot express *which* canonicalization produced a stored hash.

That is load-bearing given D2: v2 does not validate the canonicalization identifier on-chain, and the deployed graph path already stamps `1` while running URDNA2015. The database is the only place a truthful record of the scheme can live. **Decision:** a claim row MUST carry the canonicalization algorithm and the RDF profile/version that minted its `content_hash`.

## Consequences

- **Positive.** The substance collision closes (D1). Claims become **attestable**, which under the previous recommendation they would not have been (D2-a) — and attestation with `canonicalization_algorithm: 1` is demonstrably in use on mainnet already, most recently 2026-08-03. Identity is stable across the verification lifecycle (D1 exclusions) and across engines and instants (D3). The fingerprint *is* the ledger anchor (D5). Collection ordering can no longer silently fork identity (D7). This fills the Output Record Contract's `Claim.contentHash → dataIri` fields (PR #55, open question #1) without changing that envelope — note that PR #55 now references claims rather than embedding them, which is consistent with identity living on the claim.
- **Negative / cost.** D2-a needs an RDFC-1.0 canonicalizer in the serving path, the Claim→RDF substance projection that does not yet exist, a change to `derive_ledger_iri`, reconciliation with the deployed URDNA2015 constant, and D4's guard as a hard release gate. The RDF encoding profile must be frozen or the false-fork risk moves down a layer. Freezing the substance field set is a compatibility commitment — adding a substance field later re-mints identities, so `supersedes` chains must absorb any future substance-schema change. **The migration cost is near zero *for our corpus*** (D8) — our signing key has 8 Raw anchors on mainnet and all are test or demo content. That scoping is load-bearing: chain-wide there are **418** Raw anchors, and whether any counterparty dereferences ours is unanswered (Open Question 8).
- **Rejected alternatives.** *D2-b (JCS over a typed projection)* — forecloses attestation, and names an algorithm the v2 registry does not carry; withdrawn. *Keep the incumbent raw-JSON anchor* — same problem, and it is not a clean substance projection. *Re-mint all existing hashes* — trivially cheap rather than moot: it is eight test fixtures (D8). *Dual anchoring* — withdrawn 2026-08-06 **on cost**: unpaid-for machinery for a corpus of eight throwaway records. Explicitly **not** withdrawn on the earlier claim that mainnet carries no Raw corpus, which was false.
- **Follow-ups.** (a) Encode D1's substance set as a machine-checkable list beside `Claim.yaml`, so both engines read one source of truth. (b) Verify byte-parity against koi-processor's `ledger_anchor.py` once the RDF projection exists. (c) Settle the lifecycle/anchor companion record **with JC** — D1 implies it, and this ADR does not presume its shape. (d) Add the algorithm/profile columns from D9. (e) Reconcile the deployed `_GRAPH_CANON_URDNA2015` constant with D2-a, or document why they differ.

## Open questions for the deciding call

1. **RDF encoding profile — @JeancarloBarrios.** D2-a makes the profile load-bearing. Which namespace, and is `claim_type` a literal or an IRI? Compact or expanded IRIs? This is the remaining place a false fork can hide, and it is the one question the code cannot answer for us.
2. **Does JC's engine already produce RDFC-1.0 canonical N-Quads over an equivalent substance set?** Genuinely open — this ADR makes no assumption either way. If yes, cross-engine parity is largely free and the adapter is thin.
3. Is `hasOperator` substance, or provenance? *(This ADR counts it as substance when present.)*
4. Do `hasCoBenefits` participate in identity, or only the primary impact? *(This ADR includes them, as an unordered set per D7.)*
5. Should a change in `usesMethodology` alone mint a new identity, or supersede? *(Answered in review: these are the **same operation**, not alternatives — a substance change mints a new identity **and** the new claim carries `supersedes` pointing at the old. The version chain preserves continuity; identity stability was never meant to do that job. Retained here only because it was posed as an either/or in the original.)*
6. Confirm BLAKE2b-256 (D5) against the live Regen Data Module anchor encoding — `DIGEST_ALGORITHM_BLAKE2B_256 = 1` is what `ledger_anchor.py` already sends.
7. **Where does the lifecycle/anchor companion record live, given JC's model? — needs a call with @JeancarloBarrios.** D1 takes `verificationStatus` / `contentHash` / `dataIri` off `Claim.yaml` and implies a companion versioned record. @blushi reports that JC's work maps the claim IRI to the graph via `ClaimValue`, handles versioned status differently, and has **no corresponding shapes** — but does have `ClaimCandidate` and snapshots covering similar lifecycle ground. So the real question is whether we align onto those concepts or define a new class in `schema/src`. **Not decidable in this PR, and not decidable without JC.** *(Numbered 7 rather than inserted, so existing review-thread references to questions 1–6 stay valid.)*
8. **Does anyone outside this team dereference our Raw-anchored claim IRIs? — @blushi / @JeancarloBarrios.** D8 drops the dual-anchor period because re-minting eight fixtures is not a migration. But dual-anchoring also buys forward **interoperability** during a transition, and nothing gathered so far speaks to that: corpus size answers *is re-minting expensive*, not *does anyone else read it*. Concretely — two mainnet accounts are anchoring Raw JSON in roughly our shape and we cannot attribute either: `regen1wkc7x2465hhmr57fc300yxu84p78u3ystue5p5` (10 Raw JSON) and `regen1jfheyvsah5wqfyawmedme43te056z8gzdnpf3j` (1 Raw JSON, 4 Graph, and all four mainnet `MsgAttest`). None of their 11 hashes matches either of our claim databases, so they are not ours. **Do you know whose keys those are?** If a consumer exists, D8 needs a transition window.

---

## Changelog

**2026-08-06 — D2 re-grounded, D8 collapsed, JC assumption withdrawn, citations pinned.**
Four changes, all from @blushi's 2026-08-03 review.
(1) **D2's argument is now the v2 enum itself.** RDFC-1.0 is not a preference this ADR advocates — `GRAPH_CANONICALIZATION_ALGORITHM_RDFC_1_0` is the only non-zero value in the canonicalization registry of the module production actually targets (v2, evidenced by `derive_ledger_iri` sending the v2-only `file_extension` field). v1 carries the same wire value under the old name `URDNA2015`; the rename is documented as "some small clarifications around escaping of escape characters," so the shared byte `1` proves nothing about which spec ran. @blushi had raised the underlying point — anchor as RDF, not raw JSON, if we want attestation — months before this ADR was drafted; the enum finding is the citation that should have accompanied it.
(2) **The claim that JC's work already assumes the lifecycle-record shape is withdrawn** (D1, Open Question 7). @blushi is closer to that codebase and reports no corresponding shapes exist in it. The ADR now asserts nothing about JC's model and books the question as needing him in the room.
(3) **D8 rewritten from dual anchoring to a straight cutover, and its algorithm-column bullet promoted to D9.** Our signing key has made **8** Raw anchors on mainnet, all test or demo content, and has executed **zero** `MsgAttest`. Re-anchoring eight throwaway fixtures is not a migration, so the dual-anchor machinery is unpaid-for complexity. Conclusion unchanged; justification replaced with evidence; machinery removed.
(3b) **Correction to (3), same day, before this branch left review.** The first draft of the rewritten D8 justified the collapse with *"there is no production Raw corpus on mainnet"* and added that a chain-wide census was impossible from a query node. **Both were false.** A census over the tx index (2026-02-24 → 2026-08-05) returns **950 `MsgAnchor`: 418 Raw, 532 Graph** — ours is **8 of 418 (1.9%)**, **363** Raw anchors post-date our last, and the most recent is **2026-08-05**. Raw is also the registry account's live document path (259 PDFs), so "the registry's data is already all-Graph" holds only for ecocredit metadata IRIs. D8 now rests on corpus **size**, scopes every our-account statement to `regen15eexs…`, and books the interoperability gap it does *not* answer as **Open Question 8**. The same census surfaced the evidence in (3c). It also resolved the previous revision's `UNVERIFIED` ninth-transaction note: `sequence: 9` against 9 indexed txs = 8 anchors + 1 `MsgSend`.
(3c) **Four live mainnet `MsgAttest` added to D2 as the positive case for D2-a** — 2026-07-13 ×2, 2026-07-19, 2026-08-03, all carrying `canonicalization_algorithm: 1`. Graph attestation with the algorithm D2-a selects is already working practice on this chain, which is a far stronger argument than the "we have nothing to lose" framing it replaces.
(4) **Every code citation pinned to a commit SHA**, per @blushi's ask on the `Claim.yaml` link, applied across the whole document rather than to that one line.

**2026-07-31 — D2 reversed, D4 hardened, D6 strengthened, D7/D8 added.**
Prompted by @blushi's review, which argued for D2-a on the grounds that `ContentHash.Graph` declares only RDFC-1.0. Investigating that premise surfaced the stronger reason: `MsgAttest.content_hashes` is typed `ContentHash.Graph`, so the previously recommended D2-b would have made claims permanently un-attestable. Two supporting arguments for D2-b also failed on inspection — production runs deterministic `json.dumps`, not RFC 8785; and `ContentHash.Raw`'s doc comment disclaims the canonical-encoding guarantee the ADR had read into it. Review additionally established that the D1 exclusions should be removals from `Claim.yaml` rather than exclusions from the projection, and that a claim should not carry its own fingerprint at all.

**2026-07-15 — initial draft.** Recommended D2-b.

---

*Evidence: the compatibility spike is published at [`koi-research/experiments/claim-canonicalization-spike-2026-07-14`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/README.md) — [`RESULT.md`](https://github.com/regen-network/koi-research/blob/310855b5d0dfdf1ec2df63fdd05c3c4d5727352c/experiments/claim-canonicalization-spike-2026-07-14/RESULT.md) is the full record, permalinks pinned to the commit so they survive branch changes. Its contemporaneous write-up (`ADR-jc-koi-canonicalization-profile.md`) predates this revision and argues for D2-b; it is preserved as-run rather than back-edited, because rewriting evidence after the conclusion changed is what makes a spike untrustworthy. Findings 1 and 3 are algorithm-independent; finding 2 becomes more load-bearing under D2-a, not less. Real `Claim` shape: [`schema/src/Claim.yaml` @ `0a4ba12a`](https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml) — pinned, because the field set this ADR reasons about will move under review.*
