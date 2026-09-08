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
directory containing the minimal and existing rich meeting fixtures. It requires
both formats to convert and yield isomorphic RDF graphs for each fixture. The minimal
record's consent snapshot fields, policy reference, address, processing state and
raw hash must survive, without an inline raw payload. A comparison with the original
LinkML JSON-LD output checks that only node types are added: the context, root type,
other fields, values and JSON structure stay the same. A missing required sensor ID
must still fail conversion. CI runs these checks after the ordinary conversion pass.
Generated test outputs stay in the temporary directory.

`make -C schema all` also invokes `update-graph`, which clears and uploads to a
configured graph store. Use the conversion/test commands above for local conformance
checks; a full build or deployment is a separate check against an isolated destination.

## Nested RDF types in JSON-LD

The unmodified converter has a difference with `linkml==1.8.6` and
`linkml-runtime==1.9.5`: Turtle includes the snapshot's `rdf:type rfs:ConsentDirective`
triple; parsing the generated JSON-LD does not produce that triple. The remaining
triples in this minimal fixture match up to blank-node identity. JSON-LD's context
maps `consentAtEmission` with `@type: rfs:ConsentDirective`, which does not assert a
class type on its nested object. The existing rich meeting fixture also loses
nested ConsentDirective, ParticipantRef and SpeakerRef type triples in JSON-LD.

The cause is the pinned runtime's
[root-only type injection](https://github.com/linkml/linkml-runtime/blob/v1.9.5/linkml_runtime/utils/yamlutils.py)
through its [JSON dumper](https://github.com/linkml/linkml-runtime/blob/v1.9.5/linkml_runtime/dumpers/json_dumper.py).
The loaded nested objects retain their generated model class URIs. JSON-LD
[node types](https://www.w3.org/TR/json-ld11/#specifying-the-type) must be stated on
the node; the generated slot's datatype coercion is not that assertion.

`gen-rdf.sh` now routes only `OutputRecord-*.yaml` JSON-LD conversion through
`convert-output-record-jsonld.py`. This compatibility shim uses the same pinned
model generator, YAML loader, object validation, context generator and JSON dumper.
It copies loaded model nodes and adds their existing class URIs as explicit nested
`@type` values before dumping. Enum/scalar serialization stays with LinkML. The
original Turtle path and every other target class's conversion path remain unchanged.
Schema source, dependency pins, identifier values and consent fields are unchanged.

The strict expected-failure marker is removed because the minimal and rich fixtures
now satisfy the ordinary graph-equivalence assertion. This is bounded fixture parity,
not a general guarantee about arbitrary future schemas or all LinkML conversions.
If OutputRecord gains polymorphic/type-designating slots or changes nested object
shape, extend the parity fixtures when reviewing that schema change. In particular,
this does not select canonical bytes, fingerprint substance, policy enforcement or
the proposed contract itself. The broader #62 layers remain open.

## Remaining test layers

| Layer | Prerequisite and expected result |
|---|---|
| Consent policy | A validator with a supplied current-policy resolver. Valid-schema data with raw forbidden by either snapshot or current policy must be denied specifically for residency; an unresolved policy denies use. These expected-negative cases stay outside the all-success conversion corpus. |
| Replay and supersession | A consumer/store harness plus an agreed mapping from the source/sensor update key to record/version identity. Re-emitting one source/sensor must not create duplicate live records; supersession history is tested separately. |
| Canonicalization and fingerprint parity | A selected canonicalizer, pinned input-substance/schema-reference policy and expected canonical bytes/digests. Equivalent RDF serializations must match the agreed expected result; changed inputs must follow that selected identity policy. Fixture graph parity does not establish canonical bytes or fingerprint parity. |

The illustrative `schema/examples/output-record.INVALID-sovereign-inline-raw.yaml`
remains a policy counterexample. A schema/conversion failure cannot stand in for the
cross-record policy assertion, and accepting the example at the schema layer does
not authorize any use of its payload.

The broader issue remains open until these separate harnesses and their expected
results are reviewed and exercised. None are claimed to pass by this milestone.
