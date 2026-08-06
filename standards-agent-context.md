# standards-agent-context.md

**How to use this file.** Agents bootstrap from it before writing a schema change, an ADR, or a PR
description; humans read §3 as a pre-PR checklist. The rule that matters: **an unverified assumption about
ledger behaviour is blocking, not something review will catch.** If a claim about what the chain accepts is
load-bearing for your change, open the cited file and confirm it — do not infer chain behaviour from a doc
comment, a sibling type, or a previous ADR. §1.10 is a live divergence that no reviewer and no CI check would
have caught.

Citations are pinned. `regen-ledger` refs are at commit
[`451c3a3f`](https://github.com/regen-network/regen-ledger/tree/451c3a3f4353fc0d5a82383f2616a284baffa96f);
`koi-processor` refs are at `regen-prod`
[`c08c0a7e`](https://github.com/gaiaaiagent/koi-processor/tree/c08c0a7e3fdde4b6ce5186e2f7d8d11069ff4b95).
Line numbers drift — the symbol name is the durable anchor, the line number is a convenience.

---

## 1. Non-negotiable ledger constraints

### 1.1 `MsgAttest` accepts **only** `ContentHash.Graph`

`repeated ContentHash.Graph content_hashes = 2;` — `proto/regen/data/v1/tx.proto:88-91` and
`proto/regen/data/v2/tx.proto:93-96`. Both carry the comment: *"Only RDF graph data can be signed as its data
model is intended to specifically convey semantic meaning."*

**Consequence:** anything you intend to **attest** must be anchored as RDF. There is no Raw path to
attestation in either module version, and no flag relaxes it. A design that anchors Raw and plans to attest
later is not a phased rollout — it is a dead end requiring re-anchoring under a new IRI (§1.7).

### 1.2 `ContentHash.Raw` explicitly disclaims canonical encoding

`proto/regen/data/v1/types.proto:8-15`, repeated at `proto/regen/data/v2/types.proto:12-17`: *"Raw specifies
'raw' data which does not specify a deterministic, canonical encoding. Users of these hashes MUST maintain a
copy of the hashed data which is preserved bit by bit."*

**Consequence:** a Raw anchor fingerprints **specific bytes you must keep forever**, not a canonical
projection of meaning. Never argue a Raw anchor is stable across re-serialization, formatting, or key
ordering. Lose the exact bytes and the anchor is unverifiable.

### 1.3 Canonicalization algorithm: RDFC-1.0 (v2) — same wire value as URDNA2015 (v1)

- v1: `GRAPH_CANONICALIZATION_ALGORITHM_URDNA2015 = 1` — `proto/regen/data/v1/types.proto:134`
- v2: `GRAPH_CANONICALIZATION_ALGORITHM_RDFC_1_0 = 1` — `proto/regen/data/v2/types.proto:90`, commented
  *"Essentially the same as URDNA2015 with some small clarifications around escaping of escape characters."*

**Consequence:** the rename is not cosmetic and the shared wire value `1` is a trap. Two implementations can
stamp the identical algorithm byte and still produce different hashes for a graph containing escape
characters. The wire value proves nothing about which spec was run.

### 1.4 Digest algorithm: BLAKE2b-256; hash must be 20–64 bytes

`DIGEST_ALGORITHM_BLAKE2B_256 = 1` — `proto/regen/data/v1/types.proto:60`,
`proto/regen/data/v2/types.proto:76`. Length enforced in `validateHash`, `x/data/types.go:110-125`: `< 20`
bytes rejected, `> 64` bytes rejected, `digest_algorithm == 0` rejected.

**Consequence:** BLAKE2b-256 (32 bytes) is inside the window. Check any proposed digest lands in 20–64 bytes,
and never assume the chain verifies that the digest you *named* is the digest you *ran* — see §1.6.

### 1.5 Production targets **`regen.data.v2`**

Two independent confirmations:
1. `x/data/types.pb.go:2` — `// source: regen/data/v2/types.proto`. The live Go module is generated from v2.
   `proto/regen/data/v2/types.proto:5` is the only one of the two that declares
   `go_package = "github.com/regen-network/regen-ledger/x/data"`.
2. `koi-processor` writes `"file_extension": "json"` (`api/ledger_anchor.py:320`). `file_extension` is a
   **v2-only** field — v1 used a `RawMediaType media_type = 3` enum (`v1/types.proto:32`) and has no
   `file_extension` at all.

**Consequence:** when v1 and v2 differ, **v2 governs**. Quoting a v1 field name or the `RawMediaType` enum in
a design doc is a correctness error, not a stylistic one.

### 1.6 v2 does **not** validate algorithm identifiers on-chain

In v2, `digest_algorithm`, `canonicalization_algorithm` and `merkle_tree` are plain `uint32`, not enum-typed
(`proto/regen/data/v2/types.proto:32,54,58,62`). All three enum declarations carry: *"With v2, this enum is no
longer validated on-chain. However, this enum SHOULD still be used and updated as a registry of known …
algorithms and all implementations should coordinate on these values."*
(`v2/types.proto:66-70, 79-83, 93-97`).

Confirmed in code, not just comments:
- `ContentHash_Graph.Validate` (`x/data/types.go:55-66`) rejects only `CanonicalizationAlgorithm == 0`. Any
  other value passes, including values naming no known algorithm.
- `validateHash` (`x/data/types.go:110-125`) rejects only `digestAlgorithm == 0`.
- The strict membership checks `DigestAlgorithm.Validate` (`x/data/types.go:68-88`) and
  `GraphCanonicalizationAlgorithm.Validate` (`:90-100`) have **zero non-test call sites** — verified with
  `grep -rn "DigestAlgorithm.Validate" --include="*.go" x/data/ | grep -v _test.go` → empty. They are dead on
  the validation path.

**Consequence:** the chain is a registry-by-convention, not an enforcer. A wrong algorithm identifier is
accepted silently and produces a permanently mislabeled anchor. **Client-side correctness is the only
control.** Never write "the chain will reject that" about an algorithm value — it will not.

### 1.7 The IRI encodes the hash type; Raw and Graph of the same bytes are **different IRIs**

`x/data/iri.go:26-31` defines `IriPrefixRaw = 0`, `IriPrefixGraph = 1`, written as the first byte of the
base58check payload.
- Raw: `regen:{base58check(concat(byte(0x0), byte(digest_algorithm), hash))}.{file_extension}` — `iri.go:33-49`
- Graph: `regen:{base58check(concat(byte(0x1), byte(canonicalization_algorithm), byte(merkle_tree), byte(digest_algorithm), hash))}.rdf` — `iri.go:51-69`

**Consequence:** migrating an anchor from Raw to Graph **mints a new IRI**. It is not a re-label of an
existing one. Every stored `data_iri` reference downstream points at the Raw identifier and keeps pointing
there. This is why ADR 0001 **D8** specifies *dual anchoring* rather than a re-mint — and why "we'll just
re-attest the existing IRI later" is not an available option.

### 1.8 Graph IRIs must end `.rdf`; Raw extensions are 2–6 lowercase-or-numeric characters

`ParseIRI` rejects a graph-prefixed IRI whose extension is not `rdf` (`x/data/iri.go:127-131`).
`ContentHash_Raw.Validate` (`x/data/types.go:35-50`) requires the extension be 2–6 characters, lowercase or
numeric.

**Consequence:** the cheapest correctness check available, needing no chain access — **read the IRI suffix**.
`regen:….rdf` is a graph hash and is attestable. `regen:….json` (or any other suffix) is Raw and is not.

### 1.9 Current gap — claims anchor Raw and are therefore not attestable

Precisely, on the deployed branch:
- **Claims** → `compute_content_hash` (`api/ledger_anchor.py:94-101`) hashes
  `json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',',':'))` (`:58`) with BLAKE2b-256, then
  `derive_ledger_iri` (`:304-322`) builds `{"raw": {…, "file_extension": "json"}}` and `broadcast_anchor`
  (`:358`) sends `MsgAnchor`. **The resulting `regen:….json` IRI can never be passed to `MsgAttest`** (§1.1).
- **Attestations** → `build_attestation_jsonld` (`:249`) → `generate_graph_iri` (`:226`) → `broadcast_attest`
  (`:463`) does use a graph IRI. So attestation *records* are graph-anchored; the *claim* is not.

Note that the deterministic `json.dumps` above is **not RFC 8785 (JCS)** — it is sorted-key compact dumps.
Do not describe production as JCS-canonical.

Tracked migration: **ADR 0001 D8** ([`docs/adr/0001-claim-substance-canonicalization.md`](docs/adr/0001-claim-substance-canonicalization.md)),
dual anchoring — existing Raw anchors stay, new claims additionally mint a `ContentHash.Graph` identity.

### 1.10 Live divergence: deployed canonicalizer is URDNA2015 (pyld); ADR 0001 D2-a specifies RDFC-1.0

`generate_graph_iri` calls `pyld.jsonld.normalize(doc, {"algorithm": "URDNA2015", "format": "application/n-quads"})`
(`api/ledger_anchor.py:236-241`) and `_content_hash_graph_to_iri` stamps the constant `_GRAPH_CANON_URDNA2015 = 1`
(`:158`, used at `:216-222`). ADR 0001 D2-a selects **RDFC-1.0**. Both write wire byte `1` (§1.3), and the chain
does not check it (§1.6).

**Consequence:** if RDFC-1.0's escape-character clarifications change the canonical N-Quads for any graph we
anchor, we get a different hash carrying an identical algorithm identifier — a silent fork with no on-chain
signal. Any PR that touches the canonicalization path must state which spec it runs and reconcile against this
constant. Related, verified: `pyld` is imported lazily inside the function and is **absent from
`koi-processor/requirements.txt`** (97 lines, no `pyld`/`rdflib`/`oxigraph`/`jsonld` entry), so the graph path
carries an undeclared runtime dependency.

---

## 2. Where the authoritative sources are

No mystery references — each is a real path that resolves.

**Ledger (source of truth for anchoring/attestation).** Repo: https://github.com/regen-network/regen-ledger (default branch `main`)
| Path | What it settles |
|---|---|
| `proto/regen/data/v2/tx.proto` | `MsgAnchor` / `MsgAttest` wire types. **v2 is what production targets.** |
| `proto/regen/data/v2/types.proto` | `ContentHash.Raw` / `.Graph`, digest + canonicalization enums, the "no longer validated on-chain" notes |
| `proto/regen/data/v1/tx.proto`, `v1/types.proto` | v1 equivalents — historical; consult only to explain a rename |
| `x/data/types.go` | What the chain **actually** validates (`validateHash`, `ContentHash_*.Validate`) |
| `x/data/iri.go` | IRI construction + `ParseIRI`; the Raw/Graph prefix bytes and the `.rdf` rule |
| `x/data/msg_attest.go`, `x/data/msg_anchor.go` | `ValidateBasic` for each message |

**KOI implementation (source of truth for what we anchor today).** Repo: https://github.com/gaiaaiagent/koi-processor (default branch `regen-prod` — this is the deployed branch)
| Path | What it settles |
|---|---|
| `api/ledger_anchor.py` | The only anchor construction in the codebase: hashing, IRI derivation, `MsgAnchor`/`MsgAttest` broadcast |
| `api/routers/claims_router.py` | Call sites for `generate_graph_iri` / `broadcast_attest` |
| `tests/test_graph_iri.py` | Graph IRI expectations |

**This repo.**
| Path | What it settles |
|---|---|
| [`docs/adr/`](docs/adr/) | Architecture decisions. ADR 0001 governs claim substance + canonicalization. *(Arrives on `main` with PR #56.)* |
| [`schema/src/`](schema/src/) | LinkML source schemas — `Claim.yaml`, `Attestation.yaml`, `Entity.yaml`, `Impact.yaml`, `core.yaml` |
| [`schema/README.md`](schema/README.md) | Schema build + generation instructions |

**External specs.** RDFC-1.0: https://www.w3.org/TR/rdf-canon/ · LinkML identifiers:
https://linkml.io/linkml-model/latest/docs/identifier/ · JCS (RFC 8785, *not* what production runs):
https://www.rfc-editor.org/rfc/rfc8785

---

## 3. Before you open a PR

Agent drafts → **human checks this list** → only then open the PR. Every item is mechanically checkable.

**Ledger constraints**
- [ ] Does this change anything that gets anchored or attested? If no, skip to *Standards compatibility*.
- [ ] If it will be **attested**: is it anchored as `ContentHash.Graph`? (§1.1) Check the IRI suffix is `.rdf` (§1.8).
- [ ] Named a canonicalization algorithm? State **which spec**, and confirm the code runs that spec — not just
      that it stamps the right byte (§1.3, §1.6, §1.10).
- [ ] Named a digest? BLAKE2b-256, 32 bytes, inside 20–64 (§1.4).
- [ ] Cited a proto field? Confirm it exists in **v2**, not only v1 (§1.5).
- [ ] Asserted the chain rejects something? Find the rejecting line in `x/data/`. If there isn't one, delete
      the assertion (§1.6).
- [ ] Changes an existing anchor's type? Say explicitly that the IRI changes and name the migration (§1.7).

**Standards compatibility**
- [ ] Every `uriorcurie` reference has a resolvable identifier slot on the target class.
- [ ] Multivalued slots that participate in identity declare ordering (`list_elements_ordered`) — set vs
      sequence must be explicit (ADR 0001 D7).
- [ ] `make -C schema` (or the documented build) runs clean.

**Provenance**
- [ ] Every factual claim in the PR body traces to a file path, a `gh api` call, or a line of code — and you
      ran it, this session.
- [ ] Links to code that can move are pinned to a commit SHA (§5).

---

## 4. Review tag vocabulary

Reviewers prefix a comment with one tag so threads can be triaged and counted.

| Tag | Use for |
|---|---|
| `[CONSISTENCY]` | Internal contradiction — doc vs schema, ADR vs implementation, two sections disagreeing |
| `[LEDGER-CONSTRAINT]` | The change conflicts with, or assumes something unverified about, §1 |
| `[DOC-ACCESS]` | A reference a reader cannot resolve — unpinned link, missing path, private doc, undefined term |

**Author response convention.** Reply to every tagged thread with exactly one of:

- **`Addressed: <what changed>`** — name the change and the commit. Not "done", not "good catch".
- **`Deferred: <plan/timeline>`** — name where it goes (issue, follow-up PR, ADR) and when. A deferral without
  a destination is an unanswered comment.

Unanswered `[LEDGER-CONSTRAINT]` threads block merge. The others do not, but they must be answered.

---

## 5. ADR ↔ schema alignment

**Schema PRs** state, in the description:
- `Implements ADR: <link to the ADR, pinned to a commit SHA>`
- `Differences from ADR (if any) and why:` — and "none" is a valid answer that must still be written. Silence
  is not.

**ADRs** that link to schema files **pin to a commit SHA**, never to a branch. Schemas move under review, so a
branch link silently re-points to a shape the ADR was never reasoning about.

- ✅ `https://github.com/regen-network/regen-data-standards/blob/0a4ba12a28f4d9fd8bc77e9b6a7e37c08fc5b6ae/schema/src/Claim.yaml`
- ❌ `https://github.com/regen-network/regen-data-standards/blob/main/schema/src/Claim.yaml`

Repo-relative links (`../../schema/src/Claim.yaml`) are fine for navigation but do not count as pinning — if
the ADR's reasoning depends on the current field set, pin it. Same rule for evidence: spike results,
experiment repos and prior discussion get permalinks, so the record survives a force-push.

---

## 6. Worked example — the error this file exists to prevent

ADR 0001 originally recommended **D2-b**: JCS over a typed JSON projection. It was reversed on 2026-07-31.

The reasoning failed at three separate points, each of which is a checklist item above:

1. It assumed a Raw JSON anchor could be attested later. **§1.1** — `MsgAttest` is typed
   `repeated ContentHash.Graph`. One `grep content_hashes proto/regen/data/v2/tx.proto` refutes it.
2. It read `ContentHash.Raw` as providing a canonical projection. **§1.2** — the field's own doc comment
   disclaims exactly that.
3. It described production as JCS-canonical. **§1.9** — production runs sorted-key `json.dumps`, not RFC 8785.

All three were checkable in under five minutes against files named in §2, and all three would have been caught
by the §3 boxes *"if it will be attested, is it anchored as Graph?"* and *"asserted the chain rejects
something? find the rejecting line."* The cost of not checking was a full ADR rewrite plus a reviewer's time.

§1.10 is the same error class, still open: the deployed canonicalizer and the ADR name different specs while
stamping the same byte. Nothing downstream surfaces it. Someone has to look.
