from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import load_manifest, validate_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
STACK_ROOT = REPO_ROOT.parent
LOCAL_ROOT = REPO_ROOT / ".openclaw-local"


@dataclass(frozen=True)
class LocalRunResult:
    ok: bool
    executed: bool
    session_id: str
    connector_id: str
    candidate_id: str
    candidate_dir: Path
    run_log: Path | None
    generate_command: list[str]
    inspect_command: list[str]
    generate_returncode: int | None
    inspect_returncode: int | None
    generate_stdout: str
    inspect_stdout: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class LocalCandidate:
    session_id: str
    candidate_id: str
    path: Path
    has_pattern: bool
    has_midi: bool
    has_preview: bool
    has_meta: bool


def run_local_drum_floor(
    manifest_path: Path,
    *,
    candidate_id: str | None = None,
    python_cmd: str = "python",
    execute: bool = False,
) -> LocalRunResult:
    manifest = load_manifest(manifest_path)
    validation = validate_manifest(manifest)
    if not validation.ok:
        return _failed_result(
            manifest,
            candidate_id or "candidate",
            (),
            (),
            tuple(validation.errors),
            executed=False,
        )

    connector_id = "rawDrumDrive" if "rawDrumDrive" in (manifest.get("connectors") or {}) else "drumFloor"
    connectors = manifest.get("connectors") or {}
    connector = connectors.get(connector_id) or connectors.get("drumFloor") or {}
    intent = connector.get("intent") or {}
    session_id = str(manifest.get("session_id") or "session")
    safe_candidate_id = _safe_name(candidate_id or str(intent.get("candidate_id") or session_id))
    candidate_dir = (LOCAL_ROOT / "candidates" / _safe_name(session_id) / safe_candidate_id).resolve()
    local_candidate_root = (LOCAL_ROOT / "candidates").resolve()
    if candidate_dir == local_candidate_root or local_candidate_root not in candidate_dir.parents:
        return _failed_result(
            manifest,
            safe_candidate_id,
            (),
            (),
            ("candidate_dir escaped .openclaw-local/candidates",),
            executed=False,
            connector_id=connector_id,
            candidate_dir=candidate_dir,
        )

    style = str(intent.get("style") or "nerdy_jazzy_hiphop")
    bpm_range = manifest.get("bpm_range") or {}
    bpm = int(intent.get("bpm") or bpm_range.get("target") or bpm_range.get("min") or 92)
    bars = int(intent.get("bars") or 8)
    energy = int(intent.get("energy") or 42)
    seed = int(intent.get("seed") or 42)
    frame = intent.get("frame")

    generate_command = [
        python_cmd,
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
        generate_command.extend(["--frame", str(frame)])
    generate_command.extend(["--out", str(candidate_dir)])

    inspect_command = [python_cmd, "-m", "drum_floor", "inspect", str(candidate_dir)]

    if not execute:
        return LocalRunResult(
            ok=True,
            executed=False,
            session_id=session_id,
            connector_id=connector_id,
            candidate_id=safe_candidate_id,
            candidate_dir=candidate_dir,
            run_log=None,
            generate_command=generate_command,
            inspect_command=inspect_command,
            generate_returncode=None,
            inspect_returncode=None,
            generate_stdout="",
            inspect_stdout="",
            errors=(),
        )

    if any((candidate_dir / name).exists() for name in ("pattern.json", "drums.mid", "preview.txt", "meta.json")):
        return _failed_result(
            manifest,
            safe_candidate_id,
            generate_command,
            inspect_command,
            (f"candidate already exists: {candidate_dir}",),
            executed=True,
            connector_id=connector_id,
            candidate_dir=candidate_dir,
        )

    drum_floor_repo = STACK_ROOT / "drum-floor"
    if not drum_floor_repo.exists():
        return _failed_result(
            manifest,
            safe_candidate_id,
            generate_command,
            inspect_command,
            (f"drum-floor repo not found: {drum_floor_repo}",),
            executed=True,
            connector_id=connector_id,
            candidate_dir=candidate_dir,
        )

    candidate_dir.parent.mkdir(parents=True, exist_ok=True)
    generate = _run_command(generate_command, drum_floor_repo)
    inspect = _run_command(inspect_command, drum_floor_repo) if generate.returncode == 0 else None
    ok = generate.returncode == 0 and inspect is not None and inspect.returncode == 0
    run_log = _write_local_run_log(
        manifest_path=manifest_path,
        manifest=manifest,
        connector_id=connector_id,
        candidate_id=safe_candidate_id,
        candidate_dir=candidate_dir,
        generate_command=generate_command,
        inspect_command=inspect_command,
        generate=generate,
        inspect=inspect,
        ok=ok,
    )
    return LocalRunResult(
        ok=ok,
        executed=True,
        session_id=session_id,
        connector_id=connector_id,
        candidate_id=safe_candidate_id,
        candidate_dir=candidate_dir,
        run_log=run_log,
        generate_command=generate_command,
        inspect_command=inspect_command,
        generate_returncode=generate.returncode,
        inspect_returncode=inspect.returncode if inspect else None,
        generate_stdout=generate.stdout,
        inspect_stdout=inspect.stdout if inspect else "",
        errors=tuple(_errors_from_completed(generate, inspect)),
    )


def list_local_candidates(session_id: str | None = None) -> list[LocalCandidate]:
    root = LOCAL_ROOT / "candidates"
    if not root.exists():
        return []
    sessions = [root / _safe_name(session_id)] if session_id else [path for path in root.iterdir() if path.is_dir()]
    candidates: list[LocalCandidate] = []
    for session_dir in sessions:
        if not session_dir.exists():
            continue
        for candidate_dir in sorted(path for path in session_dir.iterdir() if path.is_dir()):
            candidates.append(LocalCandidate(
                session_id=session_dir.name,
                candidate_id=candidate_dir.name,
                path=candidate_dir,
                has_pattern=(candidate_dir / "pattern.json").exists(),
                has_midi=(candidate_dir / "drums.mid").exists(),
                has_preview=(candidate_dir / "preview.txt").exists(),
                has_meta=(candidate_dir / "meta.json").exists(),
            ))
    return candidates


def _run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _write_local_run_log(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    connector_id: str,
    candidate_id: str,
    candidate_dir: Path,
    generate_command: list[str],
    inspect_command: list[str],
    generate: subprocess.CompletedProcess[str],
    inspect: subprocess.CompletedProcess[str] | None,
    ok: bool,
) -> Path:
    now = datetime.now(timezone.utc)
    out_dir = LOCAL_ROOT / "runs" / _safe_name(str(manifest.get("session_id") or "session"))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{now.strftime('%Y%m%dT%H%M%SZ')}-{_safe_name(candidate_id)}.json"
    payload = {
        "schema": "openclaw.local-run.v1",
        "created_at": now.isoformat(),
        "ok": ok,
        "manifest_path": str(manifest_path),
        "session_id": manifest.get("session_id"),
        "connector_id": connector_id,
        "candidate_id": candidate_id,
        "candidate_dir": str(candidate_dir),
        "safety": {
            "local_only": True,
            "auto_arm": False,
            "records_audio": False,
            "uploads": False,
            "writes_github": False,
        },
        "generate": {
            "command": generate_command,
            "returncode": generate.returncode,
            "stdout": generate.stdout,
            "stderr": generate.stderr,
        },
        "inspect": {
            "command": inspect_command,
            "returncode": inspect.returncode if inspect else None,
            "stdout": inspect.stdout if inspect else "",
            "stderr": inspect.stderr if inspect else "",
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _errors_from_completed(
    generate: subprocess.CompletedProcess[str],
    inspect: subprocess.CompletedProcess[str] | None,
) -> list[str]:
    errors: list[str] = []
    if generate.returncode != 0:
        errors.append(generate.stderr.strip() or generate.stdout.strip() or "generate failed")
    if inspect is not None and inspect.returncode != 0:
        errors.append(inspect.stderr.strip() or inspect.stdout.strip() or "inspect failed")
    return errors


def _failed_result(
    manifest: dict[str, Any],
    candidate_id: str,
    generate_command: tuple[str, ...] | list[str],
    inspect_command: tuple[str, ...] | list[str],
    errors: tuple[str, ...],
    *,
    executed: bool,
    connector_id: str = "drumFloor",
    candidate_dir: Path | None = None,
) -> LocalRunResult:
    return LocalRunResult(
        ok=False,
        executed=executed,
        session_id=str(manifest.get("session_id") or "session"),
        connector_id=connector_id,
        candidate_id=candidate_id,
        candidate_dir=candidate_dir or LOCAL_ROOT / "candidates" / candidate_id,
        run_log=None,
        generate_command=list(generate_command),
        inspect_command=list(inspect_command),
        generate_returncode=None,
        inspect_returncode=None,
        generate_stdout="",
        inspect_stdout="",
        errors=errors,
    )


def _safe_name(value: str) -> str:
    clean = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value.strip())
    clean = clean.strip(".-")
    return clean or "candidate"
