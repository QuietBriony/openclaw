from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openclaw.cli import main as cli_main
from openclaw.harvest_inspector import harvest_inspection_to_dict, inspect_repo_harvest_sidecar


def sample_sidecar() -> dict:
    return {
        "version": 1,
        "source": {
            "repo_full_name": "QuietBriony/chill",
            "repo_url": "https://github.com/QuietBriony/chill",
            "owner": "QuietBriony",
            "default_branch": "main",
            "visibility": "public",
            "internal_or_external": "internal",
            "license": None,
            "inspected_at": "2026-05-05T00:00:00Z",
        },
        "classification": {
            "category": "ambient-surface",
            "current_role": "harvest-only",
            "target_repos": ["Music", "namima", "OpenClaw"],
            "risk_level": "medium",
        },
        "evaluation": {
            "has_audio_files": False,
            "has_samples": True,
            "has_model_weights": False,
            "has_external_dependencies": True,
            "has_github_actions": False,
            "demo_available": True,
            "browser_compatible": True,
            "dependency_weight": "light",
            "maintenance_status": "active",
        },
        "harvest": {
            "useful_ideas": ["macro controls", "soft piano memory"],
            "do_not_copy": ["sample URLs", "direct runtime code"],
            "production_translation": {
                "music": ["performance macro grouping"],
                "namima": ["public controls"],
            },
            "recommended_next_pr": "docs: define chill light-surface continuation decision",
        },
        "routing": {
            "music": {"enabled": True, "intent": "macro controls"},
            "drum_floor": {"enabled": False, "intent": "no drum routing"},
            "namima": {"enabled": True, "intent": "public ambient controls"},
            "chill": {"enabled": True, "intent": "possible light surface"},
            "openclaw": {"enabled": True, "intent": "review card"},
        },
        "safety": {
            "metadata_only": True,
            "human_review_required": True,
            "no_direct_code_copy": True,
            "no_audio_import": True,
            "no_sample_import": True,
            "no_dependency_import": True,
            "no_workflow_change": True,
        },
        "promotion": {
            "status": "review-only",
            "reviewer_notes": "No sample import.",
            "rollback_plan": "Drop sidecar or revert consuming PR.",
        },
    }


class HarvestInspectorTests(unittest.TestCase):
    def test_harvest_inspection_summarizes_review_only_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar_path = Path(tmp) / "chill.sidecar.json"
            sidecar_path.write_text(json.dumps(sample_sidecar()), encoding="utf-8")
            inspection = harvest_inspection_to_dict(inspect_repo_harvest_sidecar(sidecar_path))
            self.assertTrue(inspection["ok"])
            self.assertEqual(inspection["source"]["repo_full_name"], "QuietBriony/chill")
            self.assertEqual(inspection["classification"]["current_role"], "harvest-only")
            self.assertIn("has_samples", inspection["evaluation"]["risk_flags"])
            self.assertIn("do not import samples", "\n".join(inspection["warnings"]))

    def test_cli_harvest_inspect_prints_targets_and_safety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sidecar_path = Path(tmp) / "chill.sidecar.json"
            sidecar_path.write_text(json.dumps(sample_sidecar()), encoding="utf-8")
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(cli_main(["harvest-inspect", str(sidecar_path)]), 0)
            text = out.getvalue()
            self.assertIn("repo: QuietBriony/chill", text)
            self.assertIn("targets: Music, namima, OpenClaw", text)
            self.assertIn("music: on - macro controls", text)
            self.assertIn("metadata_only=true", text)


if __name__ == "__main__":
    unittest.main()
