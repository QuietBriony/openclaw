from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Any

from .connectors import candidate_connector_id, drum_floor_generate_command, drum_floor_inspect_command


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
    drum_connector = candidate_connector_id(manifest)
    generate = _command_to_text(drum_floor_generate_command(manifest, candidate_id, drum_connector)) if drum_connector else ""
    inspect = _command_to_text(drum_floor_inspect_command(manifest, candidate_id, drum_connector)) if drum_connector else ""
    if _is_chill_trio(manifest):
        return _build_chill_trio_plan()

    steps = [
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
    ]

    if drum_connector:
        steps.extend([
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
        ])
    else:
        steps.append(PlanStep(
            order=4,
            phase="listen",
            connector="human",
            action="review runtime state",
            gate="before_arm",
            writes="human notes only",
            detail="This manifest is observe-only; it has no generate_enabled connector. Use raw-drum-candidate-export for local drum generation.",
        ))

    steps.extend([
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
    ])
    return _renumber(steps)


def _is_chill_trio(manifest: dict[str, Any]) -> bool:
    roles = manifest.get("roles") or {}
    return manifest.get("session_mode") in {"chill_trio", "chill_trio_live"} or any(
        key in roles for key in ("chillPiano", "chillBass", "drumFloorDrums")
    )


def _build_chill_trio_plan() -> list[PlanStep]:
    return _renumber([
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
            detail="Read window.chillTrioSession.snapshot() for flow, mixMeter, pressureStatus, bassPreview, sessionShape, and drumAdapter snapshot.",
        ),
        PlanStep(
            order=3,
            phase="observe",
            connector="drumFloor",
            action="browser adapter boundary",
            gate=None,
            writes="none",
            detail="The chill page owns drum-floor adapter scheduling; OpenClaw only observes the snapshot and does not recreate chill's flow director.",
        ),
        PlanStep(
            order=4,
            phase="route",
            connector="openclaw",
            action="candidate export pointer",
            gate="before_arm",
            writes="none",
            detail="This live manifest is observe-only. Use sessions/examples/raw-drum-candidate-export.example.json when a local drum MIDI candidate is needed.",
        ),
        PlanStep(
            order=5,
            phase="listen",
            connector="human",
            action="choose BASS/DRUMS/AUTO/PANIC",
            gate="before_arm",
            writes="human notes only",
            detail="OpenClaw does not start browser audio, arm live slots, upload, record, or duplicate chill's live trio decisions.",
        ),
        PlanStep(
            order=6,
            phase="observe",
            connector="music",
            action="optional producer context",
            gate=None,
            writes="none",
            detail="Music may be checked as context, but this session keeps chill as the piano/bass master.",
        ),
        PlanStep(
            order=7,
            phase="merge",
            connector="github",
            action="repo-specific tuning proposal",
            gate="before_merge",
            writes="code review notes or explicit PR only",
            detail="Convert listening observations into small changes in chill, drum-floor, or OpenClaw.",
        ),
    ])


def _renumber(steps: list[PlanStep]) -> list[PlanStep]:
    return [
        PlanStep(
            order=index,
            phase=step.phase,
            connector=step.connector,
            action=step.action,
            gate=step.gate,
            writes=step.writes,
            detail=step.detail,
        )
        for index, step in enumerate(steps, start=1)
    ]


def _command_to_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)
