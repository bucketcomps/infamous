#!/usr/bin/env python3
"""Regression probes for the fail-closed public repository checker."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
CHECKER = Path("scripts/check_site.py")
STATUS_DRIFTS = (
    (("schema_version",), 2),
    (("as_of",), "2099-01-01"),
    (("renderer", "steps_done"), 5),
    (("renderer", "steps_total"), 14),
    (("renderer", "draws"), 1),
    (("renderer", "flips"), 1),
    (("renderer", "captures"), 1),
    (("renderer", "verified_frames"), 1),
    (("lifted_fallback", "functions"), 20299),
    (("lifted_fallback", "inventory_total"), 20299),
    (("lifted_fallback", "clean_source_proof"), True),
    (("save_system", "checks_represented"), 5),
    (("save_system", "checks_total"), 35),
    (("save_system", "end_to_end_gameplay_cycle"), True),
    (("texture_decode", "percent"), 99.0),
    (("texture_decode", "records"), 15438),
    (("model", "name"), "unreviewed"),
    (("model", "verified_pass"), 19),
    (("model", "verified_total"), 76),
    (("model", "accuracy_percent"), 25.0),
    (("model", "accepted_into_source"), 1),
    (("finish_line",), "first frame"),
)


class CheckerRegressions(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = Path(self.temporary.name) / "repo"
        shutil.copytree(
            ROOT,
            self.fixture,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_checker(self, *, expect_success: bool = False) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                "--root",
                str(self.fixture),
                "--skip-history",
            ],
            cwd=self.fixture,
            env=environment,
            capture_output=True,
            text=True,
        )
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_reviewed_repository_passes_without_history_fixture(self) -> None:
        result = self.run_checker(expect_success=True)
        self.assertIn("23 repository files", result.stdout)
        self.assertIn("base /infamous/", result.stdout)

    def test_rejects_extra_file_outside_published_site(self) -> None:
        (self.fixture / "notes.txt").write_text("extra\n", encoding="utf-8")
        result = self.run_checker()
        self.assertIn("repository inventory mismatch", result.stderr)

    def test_rejects_extra_file_inside_published_site(self) -> None:
        (self.fixture / "site/extra.html").write_text("<h1>extra</h1>\n", encoding="utf-8")
        result = self.run_checker()
        self.assertIn("repository inventory mismatch", result.stderr)

    def test_rejects_missing_allowlisted_file(self) -> None:
        (self.fixture / "CONTRIBUTING.md").unlink()
        result = self.run_checker()
        self.assertIn("repository inventory mismatch", result.stderr)

    def test_rejects_forbidden_text_outside_site(self) -> None:
        forbidden = "/" + "var" + "/" + "home" + "/private"
        readme = self.fixture / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + forbidden, encoding="utf-8")
        result = self.run_checker()
        self.assertIn("forbidden disclosure marker", result.stderr)

    def test_rejects_every_declared_status_leaf_drift(self) -> None:
        original = json.loads(
            (self.fixture / "site/data/status.json").read_text(encoding="utf-8")
        )
        for path, replacement in STATUS_DRIFTS:
            with self.subTest(path=".".join(path)):
                status = json.loads(json.dumps(original))
                target = status
                for component in path[:-1]:
                    target = target[component]
                target[path[-1]] = replacement
                (self.fixture / "site/data/status.json").write_text(
                    json.dumps(status, indent=2) + "\n",
                    encoding="utf-8",
                )
                result = self.run_checker()
                self.assertIn("status snapshot drifted", result.stderr)
        (self.fixture / "site/data/status.json").write_text(
            json.dumps(original, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_rejects_project_base_path_drift(self) -> None:
        page = self.fixture / "site/404.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace("/infamous/", "/wrong/"),
            encoding="utf-8",
        )
        result = self.run_checker()
        self.assertIn("escapes /infamous/", result.stderr)

    def test_rejects_architecture_content_map_base_drift(self) -> None:
        architecture = self.fixture / "docs/ARCHITECTURE.md"
        architecture.write_text(
            architecture.read_text(encoding="utf-8").replace(
                "`/infamous/devlog/`",
                "`/devlog/`",
            ),
            encoding="utf-8",
        )
        result = self.run_checker()
        self.assertIn("architecture content map", result.stderr)

    def test_rejects_low_contrast_callout_kicker(self) -> None:
        css = self.fixture / "site/assets/site.css"
        css.write_text(
            css.read_text(encoding="utf-8").replace("#284b50", "#62f4ff"),
            encoding="utf-8",
        )
        result = self.run_checker()
        self.assertIn("callout kicker color", result.stderr)

    def test_rejects_generic_circuit_container(self) -> None:
        page = self.fixture / "site/method/index.html"
        text = page.read_text(encoding="utf-8")
        text = text.replace(
            '<ol class="circuit" aria-labelledby="flow-title">',
            '<div class="circuit" aria-label="flow">',
        ).replace("</ol>", "</div>", 1)
        page.write_text(text, encoding="utf-8")
        result = self.run_checker()
        self.assertIn("generic metric/circuit container", result.stderr)


if __name__ == "__main__":
    unittest.main()
