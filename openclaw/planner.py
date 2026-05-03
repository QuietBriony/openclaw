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
    if _is_chill_trio(manifest):
        return _build_chill_trio_plan(drum_connector, generate, inspect)

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
            writes="printed raw command targets ../drum-floor/live/candidates; Surface local-generate writes .openclaw-local/candidates",
            detail=f"{generate} | Surface actual: python .\\openclaw_cli.py local-generate <manifest> --execute --python <python.exe>",
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


def _is_chill_trio(manifest: dict[str, Any]) -> bool:
    roles = manifest.get("roles") or {}
    return manifest.get("session_mode") == "chill_trio" or any(
        key in roles for key in ("chillPiano", "chillBass", "drumFloorDrums")
    )


def _build_chill_trio_plan(drum_connector: str, generate: str, inspect: str) -> list[PlanStep]:
    return [
        PlanStep(
            order=1,
            phase="open",
            connector="chill",
            action="manual trio page",
            gate=None,
            writes="browser audio only after human START",
            detail="Open https://quietbriony.github.io/chill/session.html; use START, BASS, DRUMS, AUTO, and PANIC manually.",
        ),
        PlanStep(
            order=2,
            phase="observe",
            connector="chill",
            action="trio snapshot",
            gate=None,
            writes="none",
            detail="Read window.chillTrioSession.snapshot() for bassOn, drumsOn, auto, barIndex, sessionShape, bassPreview, and drumAdapter snapshot.",
        ),
        PlanStep(
            order=3,
            phase="observe",
            connector="drumFloor",
            action="browser adapter preview",
            gate=None,
            writes="none",
            detail="The chill page loads createDrumFloorSessionAdapter(); previewBar and diagnostics.previewSession stay read-only unless the human enables DRUMS.",
        ),
        PlanStep(
            order=4,
            phase="generate",
            connector=drum_connector,
            action="print drum candidate command",
            gate="before_arm",
            writes="printed raw command targets ../drum-floor/live/candidates; Surface local-generate writes .openclaw-local/candidates",
            detail=f"{generate} | Surface actual: python .\\openclaw_cli.py local-generate <manifest> --execute --python <python.exe>",
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
            action="choose BASS/DRUMS/arm/skip",
            gate="before_arm",
            writes="human notes only",
            detail="OpenClaw does not start browser audio, arm live slots, upload, or record; the trio remains human-gated.",
        ),
        PlanStep(
            order=7,
            phase="observe",
            connector="music",
            action="optional producer context",
            gate=None,
            writes="none",
            detail="Music may be checked as context, but this session keeps chill as the piano/bass master.",
        ),
        PlanStep(
            order=8,
            phase="merge",
            connector="github",
            action="repo-specific tuning proposal",
            gate="before_merge",
            writes="code review notes or explicit PR only",
            detail="Convert listening observations into small changes in chill, drum-floor, or OpenClaw.",
        ),
    ]


def _command_to_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)
