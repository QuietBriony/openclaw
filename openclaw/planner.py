from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Any

from .connectors import drum_floor_generate_command, drum_floor_inspect_command


@dataclass(frozen=True)
class PlanStep:
    order: int
    phase: str
    connector: str
    action: str
    gate: str | None
    writes: str
    detail: str


def build_session_plan(manifest: dict[str, Any], candidate_id: str | None = None) -> list[PlanStep]:
    drum_connector = "rawDrumDrive" if "rawDrumDrive" in (manifest.get("connectors") or {}) else "drumFloor"
    generate = _command_to_text(drum_floor_generate_command(manifest, candidate_id, drum_connector))
    inspect = _command_to_text(drum_floor_inspect_command(manifest, candidate_id, drum_connector))

    return [
        PlanStep(
            order=1,
            phase="observe",
            connector="music",
            action="snapshot",
            gate=None,
            writes="none",
            detail="Read window.MusicRuntimeState, including producerHabits, genreTimbreKits, signatureCells, humanGroove.",
        ),
        PlanStep(
            order=2,
            phase="observe",
            connector="chill",
            action="snapshot",
            gate=None,
            writes="none",
            detail="Read window.chillAdapter.getRuntimeConfig() and diagnostics preview state; Soft Melody remains behind Music unless selected.",
        ),
        PlanStep(
            order=3,
            phase="observe",
            connector="namima",
            action="snapshot",
            gate=None,
            writes="localStorage summary only",
            detail="Read mood, auto state, and coarse namima:session-trace:v1 summaries; never audio or raw pointer streams.",
        ),
        PlanStep(
            order=4,
            phase="generate",
            connector=drum_connector,
            action="print generate candidate command",
            gate="before_arm",
            writes="../drum-floor/live/candidates/<candidate_id>",
            detail=generate,
        ),
        PlanStep(
            order=5,
            phase="inspect",
            connector=drum_connector,
            action="print inspect command",
            gate="before_arm",
            writes="none",
            detail=inspect,
        ),
        PlanStep(
            order=6,
            phase="listen",
            connector="human",
            action="listen and choose arm/skip",
            gate="before_arm",
            writes="human notes only",
            detail="OpenClaw never writes live/armed, Ableton, EP-133, or Music runtime control without explicit human action.",
        ),
        PlanStep(
            order=7,
            phase="record",
            connector="music",
            action="manual recording window",
            gate="before_record",
            writes="browser recorder only after user starts it",
            detail="Music remains the main runtime; OUTPUT and recorder are operated by the user.",
        ),
        PlanStep(
            order=8,
            phase="merge",
            connector="github",
            action="PR tuning proposal",
            gate="before_merge",
            writes="code review notes or explicit PR only",
            detail="Convert listening observations into small PRs; no automatic external upload or workflow edits.",
        ),
    ]


def _command_to_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)
