"""Exercise the publication validator's optional interface-contract inventory."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/ai-development-workflow"
BASH_EXECUTABLE = shutil.which("bash") or "bash"


class ApiContractManifestTest(unittest.TestCase):
    def test_contract_inventory_accepts_valid_entries_and_rejects_invalid_ones(self):
        with tempfile.TemporaryDirectory() as temporary:
            skill = Path(temporary).resolve() / "skill"
            shutil.copytree(SKILL, skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            manifest = skill / "assets/manifest-template.json"
            base = json.loads(manifest.read_text())
            cases = [
                ({}, 0),
                ({"contracts/api.md": {"algorithm": "sha256", "sha256": "a" * 64},
                  "contracts/associate.request.schema.json": {"algorithm": "sha256", "sha256": "b" * 64}}, 0),
                ([], 1),
                ({"../outside.json": {"algorithm": "sha256", "sha256": "a" * 64}}, 1),
                ({"contracts/../outside.json": {"algorithm": "sha256", "sha256": "a" * 64}}, 1),
                ({"contracts//api.md": {"algorithm": "sha256", "sha256": "a" * 64}}, 1),
                ({"contracts/api.md": {"algorithm": "sha256", "sha256": "bad"}}, 1),
                ({"contracts/api.md": {"algorithm": "md5", "sha256": "a" * 64}}, 1),
                ({"contracts/api.md": {"algorithm": "sha256", "sha256": "a" * 64, "extra": True}}, 1),
            ]
            for inventory, expected in cases:
                with self.subTest(inventory=inventory):
                    document = {**base, "contract_files": inventory}
                    manifest.write_text(json.dumps(document))
                    result = subprocess.run([BASH_EXECUTABLE, str(ROOT / "scripts/validate-publication.sh"), str(skill)],
                                            capture_output=True, encoding="utf-8", check=False)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            # Version-1 packages without the optional inventory stay readable.
            base.pop("contract_files", None)
            manifest.write_text(json.dumps(base))
            result = subprocess.run([BASH_EXECUTABLE, str(ROOT / "scripts/validate-publication.sh"), str(skill)],
                                    capture_output=True, encoding="utf-8", check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
