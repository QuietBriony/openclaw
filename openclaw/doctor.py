from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STACK_ROOT = REPO_ROOT.parent


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str
    required: bool = True


def run_doctor(python_cmd: str = "python") -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    checks.append(_path_check("openclaw_repo", REPO_ROOT))
    checks.append(_path_check("local_cli_shim", REPO_ROOT / "openclaw_cli.py"))

    for repo in ("Music", "drum-floor", "chill", "namima"):
      checks.append(_path_check(f"stack_repo:{repo}", STACK_ROOT / repo))

    checks.append(_python_check(python_cmd))
    checks.append(_drum_floor_check(python_cmd))
    checks.append(_external_openclaw_check())
    checks.extend(_subscription_env_checks())
    return checks


def doctor_summary(checks: list[DoctorCheck]) -> tuple[bool, int, int]:
    required = [check for check in checks if check.required]
    ok = all(check.ok for check in required)
    warnings = len([check for check in checks if not check.required and not check.ok])
    failures = len([check for check in required if not check.ok])
    return ok, warnings, failures


def _path_check(name: str, path: Path) -> DoctorCheck:
    return DoctorCheck(name=name, ok=path.exists(), detail=str(path))


def _python_check(python_cmd: str) -> DoctorCheck:
    try:
        result = subprocess.run(
            [python_cmd, "--version"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        return DoctorCheck("python", False, str(error))
    version = (result.stdout or result.stderr).strip()
    return DoctorCheck("python", result.returncode == 0, f"{python_cmd} / {version}")


def _drum_floor_check(python_cmd: str) -> DoctorCheck:
    drum_floor = STACK_ROOT / "drum-floor"
    if not drum_floor.exists():
        return DoctorCheck("drum_floor_cli", False, f"missing repo: {drum_floor}")
    try:
        result = subprocess.run(
            [python_cmd, "-m", "drum_floor", "--help"],
            cwd=str(drum_floor),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        return DoctorCheck("drum_floor_cli", False, str(error))
    ok = result.returncode == 0 and "generate" in result.stdout and "inspect" in result.stdout
    detail = "python -m drum_floor --help ok" if ok else (result.stderr.strip() or result.stdout.strip()[:180])
    return DoctorCheck("drum_floor_cli", ok, detail)


def _external_openclaw_check() -> DoctorCheck:
    found = shutil.which("openclaw")
    if not found:
        return DoctorCheck(
            "external_openclaw_cli",
            False,
            "not found on PATH; using repo-local openclaw_cli.py",
            required=False,
        )
    return DoctorCheck("external_openclaw_cli", True, found, required=False)


def _subscription_env_checks() -> list[DoctorCheck]:
    names = ("OPENCLAW_API_KEY", "OPENCLAW_TOKEN", "OPENAI_API_KEY")
    checks: list[DoctorCheck] = []
    for name in names:
        value = os.environ.get(name)
        detail = f"present length={len(value)}" if value else "absent"
        checks.append(DoctorCheck(
            f"env:{name}",
            bool(value),
            detail,
            required=False,
        ))
    return checks
