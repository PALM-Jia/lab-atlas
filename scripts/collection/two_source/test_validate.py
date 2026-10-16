"""Reject mixed rules, modified inputs, and unfrozen request evidence."""

import tempfile
import unittest
from pathlib import Path
from pipeline import read, save, digest
from validate import provenance


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.output = self.run / "iterations/final"
        self.output.mkdir(parents=True)
        config = {
            "rules_version": "test",
            "allowed_fact_sources": ["lab_homepage", "lab_user_roster", "openalex"],
            "stages": [
                {"id": s}
                for s in ["homepage", "identity", "lab-details", "external", "features"]
            ],
        }
        save(self.output / "protocol.json", config)
        (self.output / "pipeline.py").write_bytes(b"# frozen collector\n")
        paths = [
            "homepage.html",
            "current-students.json",
            "graduated-students.json",
            "vocabulary.json",
            "identity-audit.txt",
            "keywords.txt",
        ]
        (self.run / "inputs").mkdir()
        for name in paths:
            (self.run / "inputs" / name).write_bytes(b"frozen input")
        sources = {
            "files": [
                {"path": "inputs/" + n, "sha256": digest(b"frozen input")}
                for n in paths
            ]
        }
        save(self.run / "source-manifest.json", sources)
        save(
            self.output / "run-manifest.json",
            {
                "rules_version": "test",
                "rules_sha256": digest(config),
                "script_sha256": digest(b"# frozen collector\n"),
                "fact_sources": config["allowed_fact_sources"],
                "input_manifest_sha256": digest(sources),
                "offline": False,
            },
        )
        self.url = "https://api.openalex.org/works/W123?select=id"
        envelope = {
            "url": self.url,
            "state": "ready",
            "reason": "response_received",
            "payload": {"id": "https://openalex.org/W123"},
            "http": 200,
            "attempts": [],
            "received_at": "frozen",
        }
        envelope["sha256"] = digest(envelope["payload"])
        self.response = self.run / "responses" / (digest(self.url.encode()) + ".json")
        save(self.response, envelope)
        save(
            self.output / "02-identity.json",
            {"request": {k: v for k, v in envelope.items() if k != "payload"}},
        )
        for name in ("03-lab-details.json", "04-external.json"):
            save(self.output / name, {})

    def test_valid_frozen_provenance(self):
        _, _, used = provenance(self.output)
        self.assertEqual(used, {self.response.name: digest(self.response.read_bytes())})

    def test_old_iteration_without_protocol_is_rejected(self):
        (self.output / "protocol.json").unlink()
        with self.assertRaisesRegex(AssertionError, "Missing frozen protocol"):
            provenance(self.output)

    def test_modified_protocol_is_rejected(self):
        value = read(self.output / "protocol.json")
        value["rules_version"] = "other"
        save(self.output / "protocol.json", value)
        with self.assertRaisesRegex(AssertionError, "protocol hash"):
            provenance(self.output)

    def test_modified_input_is_rejected(self):
        (self.run / "inputs/homepage.html").write_bytes(b"changed")
        with self.assertRaisesRegex(AssertionError, "source hash"):
            provenance(self.output)

    def test_modified_script_is_rejected(self):
        (self.output / "pipeline.py").write_bytes(b"changed")
        with self.assertRaisesRegex(AssertionError, "collector hash"):
            provenance(self.output)

    def test_modified_response_is_rejected(self):
        value = read(self.response)
        value["payload"]["id"] = "https://openalex.org/W999"
        save(self.response, value)
        with self.assertRaisesRegex(AssertionError, "integrity"):
            provenance(self.output)

    def test_modified_event_is_rejected(self):
        value = read(self.output / "02-identity.json")
        value["request"]["state"] = "query_failed"
        save(self.output / "02-identity.json", value)
        with self.assertRaisesRegex(AssertionError, "event differs"):
            provenance(self.output)

    def test_missing_response_is_rejected(self):
        self.response.unlink()
        with self.assertRaisesRegex(AssertionError, "response absent"):
            provenance(self.output)

    def test_legacy_dependency_is_rejected_even_with_updated_manifest(self):
        sources = read(self.run / "source-manifest.json")
        sources["files"].append({"path": "_legacy/data.json", "sha256": digest(b"old")})
        save(self.run / "source-manifest.json", sources)
        manifest = read(self.output / "run-manifest.json")
        manifest["input_manifest_sha256"] = digest(sources)
        save(self.output / "run-manifest.json", manifest)
        with self.assertRaisesRegex(AssertionError, "legacy dependency"):
            provenance(self.output)


if __name__ == "__main__":
    unittest.main()
