# standards-agent-context.md

**Scope.** This file covers what an agent or a human needs before changing a **schema** or an **ADR**
in this repository. It deliberately stops at the repository boundary: how the resulting data is
anchored, attested or consumed downstream is documented with the relevant implementation.

**How to use it.** Agents bootstrap from it before writing a schema change, an ADR, or a PR
description; humans read §1 as a pre-PR checklist.

**The rule that matters:** an unverified assumption is blocking, not something review will catch. If
a claim is load-bearing for your change, open the cited file and confirm it — do not infer behaviour
from a doc comment, a sibling type, or a previous ADR.

Pin code citations to a commit SHA. Line numbers drift — use the symbol name as well as the line number.

---

## 1. Before you open a PR

Agent drafts → **human checks this list** → only then open the PR. Every item is mechanically checkable.

**Standards compatibility**
- [ ] Every `uriorcurie` reference has a resolvable identifier slot on the target class.
- [ ] Multivalued slots that participate in identity declare ordering (`list_elements_ordered`) — set vs
      sequence must be explicit.
- [ ] `make -C schema lint` passes; `make -C schema all` runs clean if you changed generated output.
      (Bare `make -C schema` runs only the first target, `gen-taxonomy` — it is not a full check.)

**Provenance**
- [ ] Every factual claim in the PR body traces to a file path, a `gh api` call, or a line of code — and you
      ran it, this session.
- [ ] Links to code that can move are pinned to a commit SHA (§2).

---

## 2. ADR ↔ schema alignment

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

## 3. Where the authoritative sources are

No mystery references — each is a real path that resolves.

**This repo.**
| Path | What it settles |
|---|---|
| [`schema/src/`](schema/src/) | LinkML source schemas — `Claim.yaml`, `Attestation.yaml`, `Entity.yaml`, `Impact.yaml`, `core.yaml` |
| [`schema/README.md`](schema/README.md) | Schema build + generation instructions |

Add an ADR directory to this source index when it exists on the target branch; until then,
link relevant proposed decisions from each PR without treating them as accepted.

**External specs.** LinkML identifiers: https://linkml.io/linkml-model/latest/docs/identifier/

---

## 4. Review tag vocabulary

Reviewers prefix a comment with one tag so threads can be triaged and counted.

| Tag | Use for |
|---|---|
| `[CONSISTENCY]` | Internal contradiction — doc vs schema, ADR vs implementation, two sections disagreeing |
| `[DOC-ACCESS]` | A reference a reader cannot resolve — unpinned link, missing path, private doc, undefined term |

**Author response convention.** Reply to every tagged thread with exactly one of:

- **`Addressed: <what changed>`** — name the change and the commit. Not "done", not "good catch".
- **`Deferred: <plan/timeline>`** — name where it goes (issue, follow-up PR, ADR) and when. A deferral without
  a destination is an unanswered comment.

These tags classify feedback; merge requirements follow repository protection and the agreed review process.

---
