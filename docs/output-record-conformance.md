# OutputRecord conformance work

The first milestone of [#62](https://github.com/regen-network/regen-data-standards/issues/62)
is a positive schema/conversion control. This branch is based on the proposed schema in
[#55 at `a0f73711d3845f0f472b0276c8bb137967fcf1fd`](https://github.com/regen-network/regen-data-standards/tree/a0f73711d3845f0f472b0276c8bb137967fcf1fd).
It makes no change to that schema or to production identity behavior. Passing this
control is not acceptance of the proposed contract or proof of full conformance.

## Executable conversion control

`schema/data/playground/OutputRecord/OutputRecord-minimal-complete.yaml` is synthetic:
a COMPLETE record with the required source/sensor fields, consent snapshot, policy
reference and a format-valid raw hash. Its raw payload is absent; the SOVEREIGN
snapshot forbids inline raw data and anchoring. The `example.org` policy reference
is not resolved by this test, and the hash value is not a digest oracle.

The existing `gen-rdf.sh` discovers `OutputRecord-*.yaml` and infers `OutputRecord`
from the filename. The fixture sits in the existing `OutputRecord` directory; a
lowercase `output-record` target-class convention must not be substituted.

Install the repository's `requirements.txt` pins, then run:

```sh
make -C schema gen-rdf
python -m unittest discover -s schema/tests -p test_output_record_conversion.py
```

The focused test calls the same conversion target with `DATA_DIR` set to a temporary
fixture directory. It requires both conversions to succeed and the consent snapshot fields, policy
reference, record address, processing state and raw hash to survive in each format. It also checks that
no inline raw payload appears. CI runs it after the ordinary conversion pass.
Generated test outputs stay in the temporary directory.

`make -C schema all` also invokes `update-graph`, which clears and uploads to a
configured graph store. Use the conversion/test commands above for local conformance
checks; a full build or deployment is a separate check against an isolated destination.

## Observed RDF parity gap

The focused fixture exposes an existing difference with `linkml==1.8.6` and
`linkml-runtime==1.9.5`: Turtle includes the snapshot's `rdf:type rfs:ConsentDirective`
triple; parsing the generated JSON-LD does not produce that triple. The remaining
triples in this minimal fixture match up to blank-node identity. JSON-LD's context
maps `consentAtEmission` with `@type: rfs:ConsentDirective`, which does not assert a
class type on its nested object. The field-preservation test intentionally makes
no full graph-parity claim. A separate normative graph-equivalence assertion remains
a strict `unittest.expectedFailure`, tracked in #62: an unexpected success fails
the suite until the marker is removed. Conversion/parsing failures happen in test
setup and are never expected failures. The expected result is one positive test
and one expected failure, not full conformance. The existing rich meeting fixture
also loses nested ConsentDirective, ParticipantRef and SpeakerRef type triples in
JSON-LD. Resolve or specify this conversion difference before
using the two outputs as interchangeable input graphs for identity tests.

## Remaining test layers

| Layer | Prerequisite and expected result |
|---|---|
| Consent policy | A validator with a supplied current-policy resolver. Valid-schema data with raw forbidden by either snapshot or current policy must be denied specifically for residency; an unresolved policy denies use. These expected-negative cases stay outside the all-success conversion corpus. |
| Replay and supersession | A consumer/store harness plus an agreed mapping from the source/sensor update key to record/version identity. Re-emitting one source/sensor must not create duplicate live records; supersession history is tested separately. |
| Canonicalization and fingerprint parity | A selected canonicalizer, pinned input-substance/schema-reference policy and expected canonical bytes/digests. Equivalent RDF serializations must match the agreed expected result; changed inputs must follow that selected identity policy. The positive field-preservation control establishes neither RDF graph parity nor a canonical byte representation. |

The illustrative `schema/examples/output-record.INVALID-sovereign-inline-raw.yaml`
remains a policy counterexample. A schema/conversion failure cannot stand in for the
cross-record policy assertion, and accepting the example at the schema layer does
not authorize any use of its payload.

The broader issue remains open until these separate harnesses and their expected
results are reviewed and exercised. None are claimed to pass by this milestone.
