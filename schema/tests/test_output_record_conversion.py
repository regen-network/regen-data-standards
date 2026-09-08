"""Positive conversion control: RDF preservation, not policy or identity conformance."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from rdflib import Graph, Literal, Namespace, RDF, XSD
from rdflib.compare import isomorphic


SCHEMA = Path(__file__).resolve().parents[1]
FIXTURE = "OutputRecord-minimal-complete.yaml"
RFS = Namespace("https://framework.regen.network/schema/")


class OutputRecordConversionTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="output-record-conversion-")
        self.addCleanup(temporary.cleanup)
        data = Path(temporary.name)
        records = data / "OutputRecord"
        records.mkdir()
        shutil.copy2(SCHEMA / "data/playground/OutputRecord" / FIXTURE, records)
        result = subprocess.run(
            ["make", "-C", str(SCHEMA), "gen-rdf"],
            env={
                **os.environ,
                "DATA_DIR": str(data),
                "SCHEMA_PATH": str(SCHEMA / "src/schema.yaml"),
            },
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("2 passed, 0 failed out of 2", result.stdout)
        stem = records / Path(FIXTURE).stem
        self.turtle = Graph().parse(stem.with_suffix(".ttl"), format="turtle")
        self.jsonld = Graph().parse(stem.with_suffix(".jsonld"), format="json-ld")

    def test_minimal_complete_record_preserves_consent_in_both_formats(self):
        # LinkML 1.8.6 omits nested rdf:type triples from JSON-LD; see
        # docs/output-record-conformance.md. Check field preservation in
        # each format without claiming full RDF graph parity.
        for format_name, graph in (("turtle", self.turtle), ("json-ld", self.jsonld)):
            with self.subTest(format=format_name):
                subjects = list(graph.subjects(RDF.type, RFS.OutputRecord))
                self.assertEqual(len(subjects), 1)
                record = subjects[0]
                self.assertEqual(
                    graph.value(record, RFS.rid),
                    Literal("https://example.org/output-records/minimal-complete", datatype=XSD.anyURI),
                )
                self.assertEqual(graph.value(record, RFS.processingState), Literal("COMPLETE"))
                self.assertEqual(
                    graph.value(record, RFS.consentRef),
                    Literal("https://example.org/consent/minimal-complete", datatype=XSD.anyURI),
                )
                snapshot = graph.value(record, RFS.consentAtEmission)
                self.assertIsNotNone(snapshot)
                self.assertEqual(graph.value(snapshot, RFS.consentStatus), Literal("GRANTED"))
                self.assertEqual(graph.value(snapshot, RFS.dataSovereigntyTier), Literal("SOVEREIGN"))
                self.assertEqual(graph.value(snapshot, RFS.rawDataStaysAtSource), Literal(True))
                self.assertEqual(graph.value(snapshot, RFS.onChainAnchorAllowed), Literal(False))
                self.assertEqual(
                    graph.value(record, RFS.rawContentHash), Literal("b2s256:" + "a" * 64)
                )
                self.assertIsNone(graph.value(record, RFS.rawContentInline))

    @unittest.expectedFailure
    def test_rdf_graph_equivalence_known_gap_issue_62(self):
        # Strict expected failure: once fixed, unexpected success fails the run
        # until this marker is removed. Tracked in regen-data-standards#62.
        # Conversion and parse failures happen in setUp and are never expected.
        self.assertTrue(
            isomorphic(self.turtle, self.jsonld),
            "#62: JSON-LD omits the nested ConsentDirective rdf:type triple",
        )


if __name__ == "__main__":
    unittest.main()
