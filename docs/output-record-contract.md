# Output Record Contract — v0.1 (draft)

**Status:** draft for review (WP4). Canonical schema: [`schema/src/OutputRecord.yaml`](../schema/src/OutputRecord.yaml).
Pydantic mirror: generated from the schema (regenerable; `generated/` is gitignored — see the command at the end of this doc).
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

- **`Claim`** — extracted claims ride in `OutputRecord.claims` (0..N).
- **`Attestation`** — optional, in `OutputRecord.attestations`.
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
| §1 Identity on the source's stable id, never title/filename; dedup/update defined on it | `sourceRecordId` (required) + `sensorId` as the dedup key |
| §2 Timestamps need an explicit timezone rule in the schema, not per-sensor convention | `emittedAt` (UTC), `observedAt` (tz-qualified), `observedLocalDate`, `sourceTimezone` |
| §3 Records need a processing-state signal; re-emission for the same id must be legal | `processingState` enum (COMPLETE/PARTIAL/PLACEHOLDER/EMPTY/…) + `supersedes` |
| §4 Distinguish claimed participants from observed speakers (different trust) | `participants` (ParticipantRef, low trust) vs `speakers` (SpeakerRef, evidence-grade) |
| §5 Auth expiry is first-class; empty-sync ≠ auth-failure | `processingState: AUTH_EXPIRED` / `FETCH_ERROR` |
| §7 Enrichment versioning — consumers need to know which vintage they read | `enrichmentVersion` |
| §7 Access-tier / consent on **every** record from day one | `consent` (required `ConsentDirective`) |
| "No English-only assumptions" | `language` (multivalued BCP-47) |
| §8 Prioritize the enrichment backlog | `priorityScore` |

**B. PACTO / biocultural-crediting requirements** (named downstream consumers):

- **Collective/community claim-makers, not just individuals** → `Entity.COMMUNITY`
  is used for `hasClaimant` / `consentedBy` / resolved speakers.
- **Consent / data sovereignty as a field from day one** → `ConsentDirective`,
  **required on every record**.
- **Raw data stays at source; only the content-addressed fingerprint anchors
  on-chain** → `rawContentHash` (obligated to travel) + `rawContentUri` (pointer)
  + `rawContentInline` (permitted only when `rawDataStaysAtSource: false`), with a
  schema rule enforcing that a `COMPLETE` record always carries the fingerprint.

## The consent / sovereignty primitive

`ConsentDirective` is the genuinely new thing here — nothing in `Claim` /
`Attestation` / `Entity` carried it. Every record has one. Required fields:

- `consentStatus` — GRANTED / PENDING / WITHHELD / REVOKED
- `dataSovereigntyTier` — PUBLIC / KNOWLEDGE_COMMONS / RESTRICTED / SOVEREIGN
- `rawDataStaysAtSource` — when true, only the fingerprint may leave (enforced)
- `onChainAnchorAllowed` — may the fingerprint anchor on-chain (independent of
  the above: a fingerprint can anchor even when raw never leaves source)

Optional: `consentedBy` (an `Entity`, may be `COMMUNITY`), `consentDate`,
`retentionPolicy`, `consentEvidence`.

Why day-one and required: a team standup and a 1:1 are the same record type from
the same sensor but have different sharing semantics. Retrofitting consent onto
an existing corpus is far more painful than carrying a mostly-default field.

## Identity, dedup, and versioning semantics

- **Identity key** = `(sourceRecordId, sensorId)`. Exactly one live record per
  key downstream.
- **Re-emission** of the same key is a legal **in-place update**, not a new
  record (field-notes §1/§3). Consumers update in place.
- **Placeholder safety**: a `PLACEHOLDER`/`EMPTY` emission must never clobber a
  prior `COMPLETE` body for the same key.
- **Version chains**: `supersedes` (IRI or ORN RID) links a record to the prior
  one it replaces, mirroring `Claim.supersedes`.

## Fingerprints and the on-chain anchor

Two hashes, both BLAKE2b-256 (matching `Claim.contentHash` / `Attestation.contentHash`):

- `rawContentHash` — fingerprint of the canonical **raw source payload**. This is
  the value obligated to travel and the one that anchors on-chain even under
  `rawDataStaysAtSource: true`.
- `recordContentHash` — fingerprint of the canonical **OutputRecord envelope**
  itself (tamper-evidence of the record as emitted).

> **Seam to the JC / claims-engine canonicalization work.** "Only the
> content-addressed fingerprint anchors on-chain" is the same design surface as
> the claims-engine substance-fingerprint / canonicalization spike. The contract
> deliberately keeps the *fields* (`rawContentHash`, `recordContentHash`,
> `Claim.contentHash` → `dataIri`) while leaving the *canonicalization algorithm*
> to that ADR. Whatever substance-schema that ADR lands, it fills these fields;
> it does not change this envelope.

## Open questions for review

1. **Canonicalization** of `rawContentHash` / `recordContentHash` — defer to the
   claims-engine substance-schema ADR, or pin a byte-canonicalization here?
2. **Consent granularity** — is a single `ConsentDirective` per record enough, or
   do we need per-claim / per-field consent for mixed-sensitivity records?
3. **`rawContentInline` vs pointer-only** — should the contract forbid inline raw
   entirely for `SOVEREIGN` tier (schema rule), not just when
   `rawDataStaysAtSource: true`?
4. **`recordType` vocabulary** — free string now; promote to a taxonomy enum once
   the first 2–3 sensors exist?
5. **Speaker identity resolution** — is `resolvedEntity` on `SpeakerRef` the right
   place, or should resolution be a separate downstream annotation pass?

## Regenerating the Pydantic mirror

The LinkML schema is canonical; the Pydantic mirror is generated:

```bash
gen-pydantic --meta NONE schema/src/schema.yaml \
  > schema/generated/pydantic/regen_data_standards.py
```

Validate instances:

```bash
linkml-validate -s schema/src/schema.yaml -C OutputRecord schema/examples/output-record.meeting-transcript.yaml
```
