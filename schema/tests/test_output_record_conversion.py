"""Positive conversion control: RDF preservation, not policy or identity conformance."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from rdflib import Graph, Literal, Namespace, RDF, XSD
from rdflib.compare import isomorphic


SCHEMA = Path(__file__).resolve().parents[1]
FIXTURE = "OutputRecord-minimal-complete.yaml"
RICH_FIXTURE = "OutputRecord-meeting-transcript-001.yaml"
RFS = Namespace("https://framework.regen.network/schema/")


class OutputRecordConversionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="output-record-conversion-")
        cls.addClassCleanup(temporary.cleanup)
        data = Path(temporary.name)
        records = data / "OutputRecord"
        records.mkdir()
        for fixture in (FIXTURE, RICH_FIXTURE):
            shutil.copy2(SCHEMA / "data/playground/OutputRecord" / fixture, records)
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
        if result.returncode != 0 or "4 passed, 0 failed out of 4" not in result.stdout:
            raise AssertionError(result.stdout + result.stderr)
        cls.graphs = {}
        cls.documents = {}
        for fixture in (FIXTURE, RICH_FIXTURE):
            stem = records / Path(fixture).stem
            cls.graphs[fixture] = (
                Graph().parse(stem.with_suffix(".ttl"), format="turtle"),
                Graph().parse(stem.with_suffix(".jsonld"), format="json-ld"),
            )
            cls.documents[fixture] = json.loads(stem.with_suffix(".jsonld").read_text())
        cls.turtle, cls.jsonld = cls.graphs[FIXTURE]

    def test_minimal_complete_record_preserves_consent_in_both_formats(self):
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

    def test_minimal_and_rich_records_have_equivalent_rdf_graphs(self):
        for fixture, (turtle, jsonld) in self.graphs.items():
            with self.subTest(fixture=fixture):
                self.assertTrue(isomorphic(turtle, jsonld))

    def test_existing_json_structure_and_values_are_preserved(self):
        def without_types(value):
            if isinstance(value, dict):
                return {key: without_types(nested) for key, nested in value.items() if key != "@type"}
            if isinstance(value, list):
                return [without_types(nested) for nested in value]
            return value

        for fixture, actual in self.documents.items():
            with self.subTest(fixture=fixture):
                baseline = subprocess.run(
                    [
                        "linkml-convert", "-s", str(SCHEMA / "src/schema.yaml"),
                        "--validate", "--input-format", "yaml", "--output-format", "json-ld",
                        "--target-class-from-path", str(SCHEMA / "data/playground/OutputRecord" / fixture),
                    ],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(baseline.returncode, 0, baseline.stderr)
                expected = json.loads(baseline.stdout)
                self.assertEqual(actual["@context"], expected["@context"])
                self.assertEqual(actual["@type"], expected["@type"])
                self.assertEqual(without_types(actual), without_types(expected))

    def test_missing_required_field_still_fails_conversion(self):
        import yaml

        with tempfile.TemporaryDirectory(prefix="output-record-invalid-") as directory:
            data = Path(directory)
            record = yaml.safe_load((SCHEMA / "data/playground/OutputRecord" / FIXTURE).read_text())
            del record["sensorId"]
            invalid = data / "OutputRecord-missing-sensor.yaml"
            invalid.write_text(yaml.safe_dump(record))
            output = data / "invalid.jsonld"
            result = subprocess.run(
                [sys.executable, str(SCHEMA / "scripts/convert-output-record-jsonld.py"),
                 "--schema", str(SCHEMA / "src/schema.yaml"), "--output", str(output), str(invalid)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sensorId", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
