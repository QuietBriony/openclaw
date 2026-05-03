from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "connectors" / "registry.json"


@dataclass(frozen=True)
class ConnectorSpec:
    connector_id: str
    repo: str
    role: str
    mode: str
    capabilities: tuple[str, ...]
    safety: tuple[str, ...]
    surfaces: tuple[str, ...]


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, ConnectorSpec]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    connectors = raw.get("connectors")
    if not isinstance(connectors, dict):
        raise ValueError("connector registry must contain a connectors object")
    return {
        key: ConnectorSpec(
            connector_id=key,
            repo=str(value.get("repo", "")),
            role=str(value.get("role", "")),
            mode=str(value.get("mode", "")),
            capabilities=tuple(value.get("capabilities", [])),
            safety=tuple(value.get("safety", [])),
            surfaces=tuple(value.get("surfaces", [])),
        )
        for key, value in connectors.items()
    }


def inspect_registry(path: Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    registry = load_registry(path)
    return [
        {
            "connector_id": spec.connector_id,
            "repo": spec.repo,
            "role": spec.role,
            "mode": spec.mode,
            "capabilities": list(spec.capabilities),
            "safety": list(spec.safety),
            "surfaces": list(spec.surfaces),
        }
        for spec in registry.values()
    ]


def drum_floor_generate_command(
    manifest: dict[str, Any],
    candidate_id: str | None = None,
    connector_id: str = "drumFloor",
) -> list[str]:
    connectors = manifest.get("connectors") or {}
    drum_floor = connectors.get(connector_id) or connectors.get("drumFloor") or {}
    intent = drum_floor.get("intent") or {}
    bpm_range = manifest.get("bpm_range") or {}

    safe_candidate_id = candidate_id or str(intent.get("candidate_id") or manifest.get("session_id") or "candidate")
    out_root = str(drum_floor.get("candidate_root") or "../drum-floor/live/candidates")
    out_path = f"{out_root.rstrip('/').rstrip('\\\\')}/{safe_candidate_id}"

    style = str(intent.get("style") or "nerdy_jazzy_hiphop")
    bpm = int(intent.get("bpm") or bpm_range.get("target") or bpm_range.get("min") or 92)
    bars = int(intent.get("bars") or 8)
    energy = int(intent.get("energy") or 42)
    seed = int(intent.get("seed") or 42)
    frame = intent.get("frame")

    command = [
        "python",
        "-m",
        "drum_floor",
        "generate",
        "--style",
        style,
        "--bpm",
        str(bpm),
        "--bars",
        str(bars),
        "--energy",
        str(energy),
        "--seed",
        str(seed),
    ]
    if frame:
        command.extend(["--frame", str(frame)])
    command.extend(["--out", out_path])
    return command


def drum_floor_inspect_command(
    manifest: dict[str, Any],
    candidate_id: str | None = None,
    connector_id: str = "drumFloor",
) -> list[str]:
    connectors = manifest.get("connectors") or {}
    drum_floor = connectors.get(connector_id) or connectors.get("drumFloor") or {}
    intent = drum_floor.get("intent") or {}
    safe_candidate_id = candidate_id or str(intent.get("candidate_id") or manifest.get("session_id") or "candidate")
    out_root = str(drum_floor.get("candidate_root") or "../drum-floor/live/candidates")
    out_path = f"{out_root.rstrip('/').rstrip('\\\\')}/{safe_candidate_id}"
    return ["python", "-m", "drum_floor", "inspect", out_path]
