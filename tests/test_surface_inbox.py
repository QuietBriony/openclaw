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

from openclaw import surface_inbox
from openclaw.cli import main as cli_main
from openclaw.packet_inspector import inspect_music_session_packet, inspection_to_dict


def sample_packet(session_id: str = "music-test-session") -> dict:
    return {
        "version": 1,
        "source_repo": "Music",
        "created_at": "2026-05-04T00:00:00Z",
        "session_id": session_id,
        "mode": "reference_gradient",
        "reference_gradient": {
            "weights": {
                "haze": 0.42,
                "memory": 0.48,
                "micro": 0.52,
                "ghost": 0.33,
                "chrome": 0.24,
                "organic": 0.58,
            }
        },
        "ucm_state": {
            "energy": 54,
            "wave": 42,
            "mind": 50,
            "creation": 44,
            "void": 18,
            "circle": 60,
            "body": 48,
            "resource": 55,
            "observer": 62,
        },
        "music_intent": {
            "timbre": ["memory"],
            "rhythm": ["ghost"],
            "space": ["safe"],
            "structure": ["review"],
            "gesture": ["sync"],
            "safety": ["metadata-only"],
        },
        "routing": {
            "drum_floor": {
                "enabled": True,
                "density": 0.55,
                "pressure": 0.38,
                "groove_intent": {"style": "broken_soft_pocket"},
                "section": "verse",
            },
            "namima": {
                "enabled": True,
                "mood_intent": {"mood": "garden"},
                "family_safe": True,
                "water_motion": 0.4,
                "brightness": 0.36,
            },
            "chill": {
                "enabled": True,
                "trio_intent": {"reference_id": "piano-jazz-chill", "bass_on": True},
                "piano_memory": 0.48,
                "drum_support": 0.22,
            },
            "openclaw": {
                "enabled": True,
                "promotion_status": "draft",
                "human_review_required": True,
                "next_action": {
                    "destination": "chill",
                    "label": "chillで聴く",
                    "action": "chill sessionを開いてSTART。",
                    "confidence": 0.64,
                },
            },
        },
        "safety": {
            "stores_audio": False,
            "stores_samples": False,
            "stores_lyrics": False,
            "metadata_only": True,
            "human_review_required": True,
        },
    }


class SurfaceInboxTests(unittest.TestCase):
    def test_import_writes_latest_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_inbox = surface_inbox.INBOX_ROOT
            old_history = surface_inbox.HISTORY_ROOT
            old_latest = surface_inbox.LATEST_PACKET_PATH
            local_root = Path(tmp) / ".openclaw-local"
            surface_inbox.INBOX_ROOT = local_root / "inbox"
            surface_inbox.HISTORY_ROOT = surface_inbox.INBOX_ROOT / "history"
            surface_inbox.LATEST_PACKET_PATH = surface_inbox.INBOX_ROOT / "latest-music-session-packet.json"
            try:
                packet_path = Path(tmp) / "music-session-packet.music-test-session.json"
                packet_path.write_text(json.dumps(sample_packet()), encoding="utf-8")
                result = surface_inbox.import_music_packet(packet_path)
                self.assertTrue(result.ok)
                self.assertTrue(result.latest_path.exists())
                self.assertTrue(result.history_path and result.history_path.exists())
                self.assertEqual(json.loads(result.latest_path.read_text(encoding="utf-8"))["session_id"], "music-test-session")
            finally:
                surface_inbox.INBOX_ROOT = old_inbox
                surface_inbox.HISTORY_ROOT = old_history
                surface_inbox.LATEST_PACKET_PATH = old_latest

    def test_cli_import_and_inspect_latest_use_surface_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_inbox = surface_inbox.INBOX_ROOT
            old_history = surface_inbox.HISTORY_ROOT
            old_latest = surface_inbox.LATEST_PACKET_PATH
            local_root = Path(tmp) / ".openclaw-local"
            surface_inbox.INBOX_ROOT = local_root / "inbox"
            surface_inbox.HISTORY_ROOT = surface_inbox.INBOX_ROOT / "history"
            surface_inbox.LATEST_PACKET_PATH = surface_inbox.INBOX_ROOT / "latest-music-session-packet.json"
            try:
                packet_path = Path(tmp) / "music-session-packet.music-cli.json"
                packet_path.write_text(json.dumps(sample_packet("music-cli")), encoding="utf-8")
                out = StringIO()
                with redirect_stdout(out):
                    self.assertEqual(cli_main(["packet-import", str(packet_path)]), 0)
                self.assertIn("latest-music-session-packet.json", out.getvalue())

                inspect_out = StringIO()
                with redirect_stdout(inspect_out):
                    self.assertEqual(cli_main(["packet-inspect", "--latest"]), 0)
                text = inspect_out.getvalue()
                self.assertIn("chill:", text)
                self.assertIn("next_action: chillで聴く", text)
            finally:
                surface_inbox.INBOX_ROOT = old_inbox
                surface_inbox.HISTORY_ROOT = old_history
                surface_inbox.LATEST_PACKET_PATH = old_latest

    def test_find_latest_download_packet_requires_valid_music_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            downloads = Path(tmp)
            (downloads / "music-session-packet.bad.json").write_text("{}", encoding="utf-8")
            good = downloads / "music-session-packet.good.json"
            good.write_text(json.dumps(sample_packet("music-good")), encoding="utf-8")
            self.assertEqual(surface_inbox.find_latest_download_packet(downloads), good)

    def test_packet_inspection_includes_chill_and_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = Path(tmp) / "packet.json"
            packet_path.write_text(json.dumps(sample_packet()), encoding="utf-8")
            inspection = inspection_to_dict(inspect_music_session_packet(packet_path))
            self.assertEqual(inspection["chill"]["reference"], "piano-jazz-chill")
            self.assertEqual(inspection["openclaw"]["next_action"]["destination"], "chill")


if __name__ == "__main__":
    unittest.main()
