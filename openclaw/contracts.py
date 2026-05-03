from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = (
    "session_id",
    "title",
    "duration_target",
    "bpm_range",
    "energy_arc",
    "roles",
    "connectors",
    "human_gates",
)

REQUIRED_CONNECTORS = ("music", "drumFloor", "chill", "namima")
REQUIRED_GATES = ("before_arm", "before_record", "before_merge")
RECOMMENDED_ROLES = ("musicProducer", "pocketDrummer", "softPiano", "giMood")

DISALLOWED_AUTOMATION = (
    "auto_arm",
    "upload_audio",
    "record_audio",
    "write_samples",
    "copy_reference_melody",
    "modify_workflows",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def read_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("session manifest must be a JSON object")
    return data


def load_manifest(path: str | Path) -> dict[str, Any]:
    return read_manifest(Path(path))


def validate_manifest(manifest: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in manifest:
            errors.append(f"missing required field: {key}")

    session_id = manifest.get("session_id")
    title = manifest.get("title")
    if not isinstance(session_id, str) or not session_id.strip():
        errors.append("session_id must be a non-empty string")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")

    _validate_duration(manifest.get("duration_target"), errors)
    _validate_bpm_range(manifest.get("bpm_range"), errors)
    _validate_energy_arc(manifest.get("energy_arc"), errors, warnings)
    _validate_roles(manifest.get("roles"), errors, warnings)
    _validate_connectors(manifest.get("connectors"), errors, warnings)
    _validate_human_gates(manifest.get("human_gates"), errors, warnings)
    _validate_guardrails(manifest.get("guardrails"), warnings)

    summary = {
        "session_id": session_id or "",
        "title": title or "",
        "connectors": sorted((manifest.get("connectors") or {}).keys())
        if isinstance(manifest.get("connectors"), dict)
        else [],
        "human_gates": sorted((manifest.get("human_gates") or {}).keys())
        if isinstance(manifest.get("human_gates"), dict)
        else [],
    }

    return ValidationResult(ok=not errors, summary=summary, warnings=warnings, errors=errors)


def _validate_duration(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("duration_target must be an object")
        return
    minutes = value.get("minutes")
    if not isinstance(minutes, (int, float)) or minutes <= 0:
        errors.append("duration_target.minutes must be a positive number")


def _validate_bpm_range(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("bpm_range must be an object")
        return
    minimum = value.get("min")
    maximum = value.get("max")
    if not isinstance(minimum, int) or not isinstance(maximum, int):
        errors.append("bpm_range.min and bpm_range.max must be integers")
        return
    if minimum < 40 or maximum > 240 or minimum > maximum:
        errors.append("bpm_range must stay within 40..240 and min must be <= max")


def _validate_energy_arc(value: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("energy_arc must be a non-empty list")
        return
    last_at = -1.0
    for index, point in enumerate(value):
        if not isinstance(point, dict):
            errors.append(f"energy_arc[{index}] must be an object")
            continue
        at = point.get("at")
        energy = point.get("energy")
        if not isinstance(at, (int, float)) or at < 0 or at > 1:
            errors.append(f"energy_arc[{index}].at must be between 0 and 1")
        elif at < last_at:
            warnings.append("energy_arc points are not sorted by at")
        else:
            last_at = at
        if not isinstance(energy, (int, float)) or energy < 0 or energy > 1:
            errors.append(f"energy_arc[{index}].energy must be between 0 and 1")


def _validate_roles(value: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("roles must be an object")
        return
    for role in RECOMMENDED_ROLES:
        if role not in value:
            warnings.append(f"recommended role missing: {role}")


def _validate_connectors(value: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("connectors must be an object")
        return
    for connector in REQUIRED_CONNECTORS:
        if connector not in value:
            errors.append(f"missing required connector: {connector}")
            continue
        config = value[connector]
        if not isinstance(config, dict):
            errors.append(f"connector {connector} must be an object")
            continue
        if config.get("enabled") is not True:
            warnings.append(f"connector {connector} is present but not enabled")
    drum_floor = value.get("drumFloor")
    if isinstance(drum_floor, dict):
        out_root = str(drum_floor.get("candidate_root", ""))
        normalized = out_root.replace("\\", "/")
        if normalized and "live/candidates" not in normalized:
            errors.append("drumFloor.candidate_root must stay under live/candidates")
        if drum_floor.get("allow_auto_arm") is True:
            errors.append("drumFloor.allow_auto_arm must not be true")


def _validate_human_gates(value: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("human_gates must be an object")
        return
    for gate in REQUIRED_GATES:
        gate_value = value.get(gate)
        if not isinstance(gate_value, dict):
            errors.append(f"missing required human gate: {gate}")
            continue
        if gate_value.get("required") is not True:
            errors.append(f"human gate {gate} must be required")
        if not gate_value.get("owner"):
            warnings.append(f"human gate {gate} should name an owner")


def _validate_guardrails(value: Any, warnings: list[str]) -> None:
    if not isinstance(value, dict):
        warnings.append("guardrails object is recommended")
        return
    for key in DISALLOWED_AUTOMATION:
        if value.get(key) is not False:
            warnings.append(f"guardrails.{key} should be false")
