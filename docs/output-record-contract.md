# Output Record Contract — v0.1 (draft)

**Status:** draft for review (WP4). Canonical schema: [`schema/src/OutputRecord.yaml`](../schema/src/OutputRecord.yaml).
Language bindings are generated from the schema by the consuming repository; nothing generated is committed here.
Worked examples: [`schema/examples/`](../schema/examples/).

## What this is

The **Output Record Contract** is the single, sensor-agnostic envelope a *sensor*
emits when it hands data downstream to the *claims engine*. One contract, many
sensors (Otter transcripts, iNaturalist observations, field-signing apps, …). It
is the stable seam in the pipeline:

```
sources ─► sensors ─►  [ Output Record ]  ─► claims engine ─► attestation ─► Regen Ledger
                         (this contract)
```

A sensor's job is to pull messy data from a third-party source and emit
**structured, trustworthy records**: provenance + consent + evidence (+ any
extracted claims). The claims engine consumes them. Keeping this envelope stable
is what lets sensors and consumers evolve independently.

It composes with the merged WP4 schemas rather than re-inventing them:

- **`Claim`** — extracted claims are **referenced**, not embedded:
  `OutputRecord.claimRefs` (0..N `uriorcurie`). A claim's identity and lifecycle
  move independently of the source record.
- **`Attestation`** — **no field on this envelope.** `Attestation.attestsClaim`
  is required, so it is already the edge; attestations reachable from a record
  are found by traversing `claimRefs` and inverting `attestsClaim`.
- **`Entity`** — claimants, subjects, consenters, resolved speakers are `Entity`,
  and `Entity.type` already includes **`COMMUNITY`**, so collective claim-makers
  are first-class.
- **`ClaimType` / `VerificationStatus` / `ImpactType` / `QuantityUnit`** — reused
  from `taxonomy.yaml`; the contract introduces no parallel vocabulary for them.

`Claim.yaml` already refers to "the Output Record Contract instance shape" (the
flat `quantity` + `quantityUnit` comment); this schema is that shape made
explicit.

## Design requirements it satisfies

Two sources of hard requirements:

**A. Gregory's Otter-sensor field notes** (`regen-network/sensor-sdk`, PR #1) —
each "Contract implication" is honored by a field:

| Field-note implication | Contract field(s) |
|---|---|
| §1 Identity on the source's stable id, never title/filename; dedup/update defined on it | `rid` (the record's own identity) + `sourceRecordId` / `sensorId` (the dedup key) |
| §2 Timestamps need an explicit timezone rule in the schema, not per-sensor convention | `emittedAt` (UTC), `observedAt` (tz-qualified), `sourceTimezone` (the local date is derived, not stored) |
| §3 Records need a processing-state signal; re-emission for the same id must be legal | `processingState` enum (COMPLETE/PARTIAL/PLACEHOLDER/EMPTY/…) + `supersedes` |
| §4 Distinguish claimed participants from observed speakers (different trust) | `participants` (ParticipantRef, low trust) vs `speakers` (SpeakerRef, evidence-grade) |
| §5 Auth expiry is first-class; empty-sync ≠ auth-failure | `processingState: AUTH_EXPIRED` / `FETCH_ERROR` |
| §7 Enrichment versioning — consumers need to know which vintage they read | `enrichmentVersion` |
| §7 Access-tier / consent on **every** record from day one | `consentAtEmission` (required `ConsentDirective` snapshot) + `consentRef` (required, current policy) |
| "No English-only assumptions" | `language` (multivalued BCP-47) |
| §8 Prioritize the enrichment backlog | `priorityScore` |

**B. PACTO / biocultural-crediting requirements** (named downstream consumers):

- **Collective/community claim-makers, not just individuals** → `Entity.COMMUNITY`
  is used for `hasClaimant` / `consentedBy` / resolved speakers.
- **Consent / data sovereignty as a field from day one** → a required immutable
  `consentAtEmission: ConsentDirective` snapshot **plus** a required `consentRef`
  to current policy, resolved fail-closed to the more restrictive of the two.
- **Raw data stays at source; only the content-addressed fingerprint anchors
  on-chain** → `rawContentHash` (obligated to travel) + `rawContentUri` (pointer)
  + `rawContentInline` (permitted only when `rawDataStaysAtSource: false`), with a
  schema rule enforcing that a `COMPLETE` record always carries the fingerprint.

## The consent / sovereignty primitive

`ConsentDirective` is the genuinely new thing here — nothing in `Claim` /
`Attestation` / `Entity` carried it. Required fields:

- `consentStatus` — GRANTED / PENDING / REVOKED / WITHHELD
- `dataSovereigntyTier` — PUBLIC / KNOWLEDGE_COMMONS / RESTRICTED / SOVEREIGN
- `rawDataStaysAtSource` — when true, only the fingerprint may leave
- `onChainAnchorAllowed` — may the fingerprint anchor on-chain (independent of
  the above: a fingerprint can anchor even when raw never leaves source)

Optional: `consentedBy` (an `Entity`, may be `COMMUNITY`), `consentDate`,
`retentionPolicy`, `consentEvidence`.

Why day-one and required: a team standup and a 1:1 are the same record type from
the same sensor but have different sharing semantics. Retrofitting consent onto
an existing corpus is far more painful than carrying a mostly-default field.

### Why the record carries consent twice

The v0.1 draft embedded a single `consent: ConsentDirective` in the record. That
is wrong, and the objection is @blushi's on [#55](https://github.com/regen-network/regen-data-standards/pull/55):
`consentStatus`, `dataSovereigntyTier`, `rawDataStaysAtSource`,
`onChainAnchorAllowed` and `retentionPolicy` are **mutable authorization state**,
not stable evidence provenance. Freezing them inside a provenance envelope means
a consumer holding an older record acts on consent that has since been revoked.

The naive fix — move consent out entirely, leave a pointer — trades one failure
for a worse one. Today a consumer that ignores the index reads *stale* policy.
After a pointer-only split, a consumer that never learns the index exists reads
*none*, and the day-one guarantee (consent present and non-losable on every
record) is gone.

So the record carries both, and they are different things:

| | `consentAtEmission` | `consentRef` |
|---|---|---|
| What it is | Immutable snapshot, inlined | Reference to the current versioned consent record |
| Semantics | **Evidence** — what was true at emission | **Policy** — what is true now |
| Mutability | Never updated in place | Changes without touching this record |
| Required | Yes | Yes |
| Failure mode it closes | Consent cannot be lost | Consent cannot go stale |

A re-emission (new `rid`, same `sourceRecordId` + `sensorId`) carries its own
snapshot. Neither field is sufficient alone: the snapshot can be stale, the ref
can be unresolvable.

Gregory's 15 July requirement was that consent be **present and non-losable on
every record**. The embedded class was an implementation choice, not the ask. The
snapshot satisfies non-losability; the ref keeps policy current; the fail-closed
rule below resolves the conflict between them safely.

### Consent resolution

**The rule, in three lines.**

1. Any use `consentAtEmission` **already forbids** is forbidden. No resolution
   needed — a stricter snapshot is authoritative on its own.
2. For any use `consentAtEmission` **permits**, resolve `consentRef` first and
   apply the **more restrictive** of the two, field by field.
3. If `consentRef` **cannot be resolved**, the use is **denied**. A resolution
   failure is never a permit.

**Field-by-field merge.** The two enum fields are totally ordered by the `rank`
declared on each permissible value, so "more restrictive" is computable, not a
judgement call.

| Field | Merge | Why |
|---|---|---|
| `consentStatus` | higher `rank` (GRANTED 1 → PENDING 2 → REVOKED 3 → WITHHELD 4) | Only an effective `GRANTED` permits use |
| `dataSovereigntyTier` | higher `rank` (PUBLIC 1 → KNOWLEDGE_COMMONS 2 → RESTRICTED 3 → SOVEREIGN 4) | Tier can only tighten in effect |
| `rawDataStaysAtSource` | logical **OR** | Either side asserting residency wins |
| `onChainAnchorAllowed` | logical **AND** | Anchoring is irreversible; needs both |
| `retentionPolicy` | **not mergeable** — resolved policy governs, snapshot retained as evidence | Free text has no restrictiveness order |
| `consentedBy` / `consentDate` / `consentEvidence` | descriptive; prefer resolved, fall back to snapshot | Not permission-bearing |

**Worked example.** A record emitted under a permissive snapshot, whose community
has since tightened the terms:

```yaml
# on the record, frozen at emission
consentAtEmission:
  consentStatus: GRANTED
  dataSovereigntyTier: KNOWLEDGE_COMMONS
  rawDataStaysAtSource: false
  onChainAnchorAllowed: true
consentRef: "orn:regen.consent:wsanec-riparian-monitoring/v4"
```

```yaml
# resolved from consentRef, current
consentStatus: GRANTED
dataSovereigntyTier: SOVEREIGN
rawDataStaysAtSource: true
onChainAnchorAllowed: false
```

Effective policy:

| Field | Snapshot | Resolved | Effective | Rule |
|---|---|---|---|---|
| `consentStatus` | GRANTED (1) | GRANTED (1) | **GRANTED** | higher rank |
| `dataSovereigntyTier` | KNOWLEDGE_COMMONS (2) | SOVEREIGN (4) | **SOVEREIGN** | higher rank |
| `rawDataStaysAtSource` | false | true | **true** | OR |
| `onChainAnchorAllowed` | true | false | **false** | AND |

So: the record may be used, but it is SOVEREIGN-tier, `rawContentInline` must not
be read even though the snapshot permitted it, and the fingerprint must **not** be
anchored on-chain even though the snapshot permitted that too. Had `consentRef`
been unreachable, all three would have been denied instead.

The inverse case matters as much: if the snapshot said `SOVEREIGN` /
`rawDataStaysAtSource: true` and the resolved record said `PUBLIC` / `false`, the
effective policy is still `SOVEREIGN` / `true`. **Resolution can only tighten,
never loosen.** Loosening consent requires a new emission with a new snapshot,
which is what makes the snapshot evidence rather than a cache.

**Not schema-enforced.** LinkML cannot express any of this — it cannot follow
`consentRef`, and as the section at the end of this document explains, it cannot
even traverse into `consentAtEmission` from the parent class. This rule is a
consumer obligation. Treat schema validation as necessary but not sufficient.

## Identity, dedup, and versioning semantics

Two handles, doing two different jobs. Conflating them was the original mistake.

- **Record identity** = `rid` (required, `uriorcurie`). The record's own stable
  address — what a reference *to this record* resolves against, and what
  `supersedes` points at. Shape carried over from [PR #57](https://github.com/regen-network/regen-data-standards/pull/57).
- **Dedup / update key** = `(sourceRecordId, sensorId)`. Says *which upstream
  thing* this record is about, and therefore which live record a re-emission
  replaces. Exactly one live record per key downstream.
- A re-emission mints a **new `rid`** and reuses the **same
  `(sourceRecordId, sensorId)`**; that is precisely what makes it an update
  rather than a new subject.
- `rid` is deliberately **not** declared `identifier: true`. LinkML resolves an
  identifier slot's value as a CURIE during RDF serialization, and `orn:` has no
  declared prefix expansion, so `linkml-convert --output-format ttl` fails with
  `Unknown CURIE prefix: orn`. Promoting it requires first deciding what `orn:`
  expands to — that belongs with the `Entity` / `Claim` identity-key follow-up.
- **Re-emission** of the same key is a legal **in-place update**, not a new
  record (field-notes §1/§3). Consumers update in place.
- **Placeholder safety**: a `PLACEHOLDER`/`EMPTY` emission must never clobber a
  prior `COMPLETE` body for the same key.
- **Version chains**: `supersedes` (IRI or ORN RID) links a record to the prior
  one it replaces, mirroring `Claim.supersedes`.

## Fingerprints and the on-chain anchor

Two hashes, both BLAKE2b-256 (matching `Claim.contentHash` / `Attestation.contentHash`):

- `rawContentHash` — fingerprint of the **raw source payload**. This is the value
  obligated to travel and the one that anchors on-chain even under
  `rawDataStaysAtSource: true`.
- `recordContentHash` — fingerprint of the **OutputRecord envelope** itself
  (tamper-evidence of the record as emitted).

Both use the wire format decided below. Note that "canonical" is doing no work in
either definition until ADR 0001 lands — the contract pins how a hash is
*written*, not what was hashed.

> **Seam to the JC / claims-engine canonicalization work.** "Only the
> content-addressed fingerprint anchors on-chain" is the same design surface as
> the claims-engine substance-fingerprint / canonicalization spike, specified in
> [**ADR 0001 — Claim substance & content-addressed canonicalization**](adr/0001-claim-substance-canonicalization.md)
> ([PR #56](https://github.com/regen-network/regen-data-standards/pull/56)). The
> contract deliberately keeps the *fields* (`rawContentHash`, `recordContentHash`,
> `Claim.contentHash` → `dataIri`) while leaving the *canonicalization algorithm*
> to ADR 0001. Whatever substance-schema that ADR lands, it fills these fields; it
> does not change this envelope.

### Hash wire format

**Decision: `b2s256:<64 lowercase hex chars>`, enforced by a `pattern` on both
hash slots.** This reverses the lean I put to @blushi on 31 July (bare hex), and
the reason is worth stating because it is the opposite of what I expected.

What the evidence actually says:

- **Production emits bare lowercase hex.** `koi-processor/api/ledger_anchor.py:96`
  returns `hashlib.blake2b(..., digest_size=32).hexdigest()`. No prefix.
- **`b2s256` appears nowhere.** `grep -r b2s256` over both `koi-processor` and
  `regen-ledger` returns zero hits. I invented it in these examples.
- **The ledger carries the algorithm out of band.** `ContentHash.Raw` and
  `ContentHash.Graph` are `{hash: bytes, digest_algorithm: uint32, …}` — raw
  bytes plus a numeric discriminator, never a prefixed string.

Read alone, those three all argue for bare hex, which is why I leaned that way.
The thing that flips it:

- **A bare 64-hex string is ambiguous, and the ambiguity is already in our own
  database.** `koi_memories.content_hash` is SHA-256
  (`migrations/004_add_publication_dates.sql:28`) and `claims.content_hash` is
  BLAKE2b-256 (`migrations/064_claims_engine.sql:41`). Same name, same shape,
  same length, different algorithms, one codebase. Nothing in the value
  distinguishes them.
- **ADR 0001 D8 commits us to two coexisting anchoring schemes** — legacy
  `ContentHash.Raw` anchors stay, new claims mint `ContentHash.Graph` — and names
  the absence of a discriminator as a latent defect in its own words: *"the
  current schema cannot express which canonicalization produced a stored hash."*
  Shipping an undiscriminated hash in a **wire contract**, where there is no
  sibling column to add later, repeats that defect in the one place it is hardest
  to fix.

A wire envelope is not a database row. The ledger and ADR 0001 can put the
discriminator in an adjacent field because they control both sides of the read.
This contract is consumed by parties we do not control, so the value has to carry
its own meaning.

**What the token does and does not say.** `b2s256` names the **digest
algorithm** — nothing else. Specifically:

- It is drawn from the ledger's `DigestAlgorithm` registry, which today has
  exactly one non-zero member (`DIGEST_ALGORITHM_BLAKE2B_256 = 1`). A new token
  may only be minted when that enum gains a member. This is not a freehand
  namespace.
- It does **not** encode the `ContentHash` kind (Raw vs Graph) or a
  canonicalization algorithm. For `rawContentHash` that is complete: a raw source
  payload is not RDF, so it anchors as `ContentHash.Raw`, and the proto is
  explicit that Raw *"does not specify a deterministic, canonical encoding."*
  For `recordContentHash` it is **not** complete — this envelope does have an RDF
  projection, so Raw-over-JSON vs Graph-over-RDFC-1.0 is genuinely open, and it
  is the same question ADR 0001 is answering for `Claim`. Flagged in the slot
  description rather than quietly decided here.

**Lowercase hex only** (`[0-9a-f]`, not `[0-9a-fA-F]` as the review bot
suggested). `hexdigest()` is lowercase, and permitting mixed case gives a single
fingerprint 2⁶⁴ valid spellings — string equality and dedup would break on a
value whose entire purpose is content-addressed identity.

**Rejected: multihash / multibase.** Standards-based and genuinely
self-describing, but it needs a codec table on both sides, produces values
nothing in our stack emits today, and diverges from the ledger's own registry
for no gain we can currently spend.

**The cost, plainly.** koi-processor emits bare hex today and will have to prefix
at the contract boundary. That is a one-line change, and it is the right
direction: the standard sets the wire format and the implementation adapts, not
the reverse. Conversion back is `token, hex = value.split(":")` →
`bytes.fromhex(hex)` + the mapped `digest_algorithm`.

**Not done here:** `Claim.contentHash` and `Attestation.contentHash` on `main`
are `range: string` with no pattern and the same ambiguity. Same class of gap as
`Entity` having no identifier slot — belongs in the identity-keys follow-up, not
in a PR that has no business editing merged schemas.

## Open questions for review

1. ~~**Canonicalization** of `rawContentHash` / `recordContentHash`~~ — **wire
   format settled above**; the *canonicalization* remains ADR 0001's call, and
   for `recordContentHash` specifically the Raw-vs-Graph kind is still open.
2. **Consent granularity** — is one `consentAtEmission` / `consentRef` pair per
   record enough, or do we need per-claim / per-field consent for
   mixed-sensitivity records? (The snapshot-plus-ref split is settled; this is
   about *how many* of them a record carries.)
3. **`rawContentInline` vs pointer-only** — should the contract forbid inline raw
   entirely for `SOVEREIGN` tier (schema rule), not just when
   `rawDataStaysAtSource: true`?
4. **`recordType` vocabulary** — free string now; promote to a taxonomy enum once
   the first 2–3 sensors exist?
5. **Speaker identity resolution** — is `resolvedEntity` on `SpeakerRef` the right
   place, or should resolution be a separate downstream annotation pass?

## Consuming the contract

The LinkML schema in `schema/src/` is canonical. How a consumer binds to it —
generated Pydantic models, generated dataclasses, hand-written validators — is
the consumer's choice and is documented in the consuming repository, not here.


---

## Raw-data residency is not schema-enforced

An **effective** `rawDataStaysAtSource: true` means the raw payload MUST NOT
travel — only `rawContentHash` and `rawContentUri` may. "Effective" is the OR of
`consentAtEmission.rawDataStaysAtSource` and the resolved `consentRef` value, per
"Consent resolution" above. **LinkML does not enforce this, and a record that
violates it will validate successfully.**

The reason is structural, and the split makes it worse, not better: a LinkML
`rule` on `OutputRecord` cannot traverse into
`consentAtEmission.rawDataStaysAtSource` to make `rawContentInline` conditionally
forbidden, and it certainly cannot follow `consentRef` to a separate record. The
only rule the class carries requires `rawContentHash` when `processingState` is
`COMPLETE`. Hoisting a mirror of `rawDataStaysAtSource` onto `OutputRecord` itself
would make the intra-record half expressible, but at the cost of two sources of
truth for the same policy — worse than an honest gap.

So the invariant is enforced **outside the schema**, and every consumer owes it:

> Before reading `rawContentInline`, check
> `consentAtEmission.rawDataStaysAtSource`. If it is true, the record is
> malformed — reject it and do not read the payload. If it is false, resolve
> `consentRef` and check again; if the ref will not resolve, do not read the
> payload. Fail closed.

`schema/examples/output-record.INVALID-sovereign-inline-raw.yaml` is a committed
negative fixture demonstrating exactly this: a SOVEREIGN-tier record carrying its
raw payload inline. It passes `linkml-validate`. It is kept so the gap stays
visible, and so that if a future LinkML version or a SHACL shape ever does express
the constraint, the fixture begins to fail and we notice.

Treat schema validation as necessary but not sufficient.
