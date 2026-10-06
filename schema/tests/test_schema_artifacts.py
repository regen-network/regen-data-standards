"""Published examples must actually target their declared validation class."""

import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCHEMA = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "schema_artifacts", SCHEMA / "scripts/schema-artifacts.py"
)
artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifacts)


class ExampleEntryPointTests(unittest.TestCase):
    def check_example(self, root_type, nested_claim=False):
        manifest = json.loads((SCHEMA / "versions/manifest.json").read_text())
        entry = copy.deepcopy(manifest["versions"]["0.2.0"])
        entry["examples"] = [
            e for e in entry["examples"]
            if e["path"].endswith("/generic-claim.jsonld")
        ]
        with tempfile.TemporaryDirectory() as temporary:
            versions = Path(temporary)
            shutil.copytree(SCHEMA / "versions/0.2.0", versions / "0.2.0")
            example = versions / entry["examples"][0]["path"]
            document = json.loads(example.read_text())
            if root_type is None:
                document.pop("@type")
            else:
                document["@type"] = root_type
            if nested_claim:
                nested = copy.deepcopy(document)
                nested.pop("@context", None)
                nested["@type"] = "Claim"
                nested["@id"] = "urn:regen:schema-artifact-check:root"
                document["@included"] = [nested]
            example.write_text(json.dumps(document))
            failures = []
            with patch.object(artifacts, "VERSIONS", versions):
                artifacts.check_examples("0.2.0", entry, failures)
            return failures

    def test_valid_claim(self):
        self.assertEqual(self.check_example("Claim"), [])

    def test_expanded_type_is_equivalent(self):
        self.assertEqual(
            self.check_example("https://framework.regen.network/schema/Claim"), []
        )

    def test_unrelated_type_cannot_pass_without_a_shacl_target(self):
        self.assertTrue(self.check_example("UnrelatedRecord"))

    def test_nested_claim_cannot_supply_the_root_type(self):
        failures = self.check_example("UnrelatedRecord", nested_claim=True)
        self.assertIn("root does not have entry-point RDF type", "\n".join(failures))

    def test_missing_type_cannot_pass_without_a_shacl_target(self):
        self.assertTrue(self.check_example(None))


if __name__ == "__main__":
    unittest.main()
