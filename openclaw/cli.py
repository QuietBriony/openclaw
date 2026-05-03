from __future__ import annotations

import argparse
import json
from pathlib import Path

from .connectors import (
    drum_floor_generate_command,
    drum_floor_inspect_command,
    inspect_registry,
)
from .contracts import load_manifest, validate_manifest
from .planner import build_session_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m openclaw",
        description="Dry-run session control contracts for the QuietBriony music stack.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a SessionManifest v1 JSON file.")
    validate.add_argument("manifest", type=Path)

    plan = subparsers.add_parser("plan", help="Print a human-gated dry-run session plan.")
    plan.add_argument("manifest", type=Path)
    plan.add_argument("--candidate-id", help="Override the drum-floor candidate id in dry-run commands.")

    inspect = subparsers.add_parser("inspect-connectors", help="Print the connector registry.")
    inspect.add_argument("--json", action="store_true", help="Emit registry as JSON.")

    drum_floor = subparsers.add_parser(
        "drum-floor-command",
        help="Print safe drum-floor generate and inspect commands. Does not execute them.",
    )
    drum_floor.add_argument("manifest", type=Path)
    drum_floor.add_argument("--candidate-id", help="Override the candidate id.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        manifest = load_manifest(args.manifest)
        result = validate_manifest(manifest)
        _print_validation(result.summary, result.warnings, result.errors)
        return 0 if result.ok else 1

    if args.command == "plan":
        manifest = load_manifest(args.manifest)
        result = validate_manifest(manifest)
        _print_validation(result.summary, result.warnings, result.errors)
        if not result.ok:
            return 1
        print("")
        print("session_plan:")
        for step in build_session_plan(manifest, args.candidate_id):
            gate = step.gate or "-"
            print(f"{step.order}. [{step.phase}] {step.connector}.{step.action}")
            print(f"   gate: {gate}")
            print(f"   writes: {step.writes}")
            print(f"   detail: {step.detail}")
        return 0

    if args.command == "inspect-connectors":
        registry = inspect_registry()
        if args.json:
            print(json.dumps(registry, indent=2, ensure_ascii=False))
            return 0
        for spec in registry:
            print(f"{spec['connector_id']}: {spec['repo']} ({spec['mode']})")
            print(f"  role: {spec['role']}")
            print(f"  capabilities: {', '.join(spec['capabilities'])}")
            print(f"  safety: {', '.join(spec['safety'])}")
            print(f"  surfaces: {', '.join(spec['surfaces'])}")
        return 0

    if args.command == "drum-floor-command":
        manifest = load_manifest(args.manifest)
        result = validate_manifest(manifest)
        if not result.ok:
            _print_validation(result.summary, result.warnings, result.errors)
            return 1
        print("generate:")
        connector_id = "rawDrumDrive" if "rawDrumDrive" in (manifest.get("connectors") or {}) else "drumFloor"
        print("  " + _join_command(drum_floor_generate_command(manifest, args.candidate_id, connector_id)))
        print("inspect:")
        print("  " + _join_command(drum_floor_inspect_command(manifest, args.candidate_id, connector_id)))
        print("note: OpenClaw prints these commands only; it does not execute or arm candidates.")
        return 0

    parser.error("unknown command")
    return 2


def _print_validation(summary: dict[str, object], warnings: list[str], errors: list[str]) -> None:
    print(f"manifest: {summary.get('session_id') or '-'}")
    print(f"title: {summary.get('title') or '-'}")
    print(f"ok: {str(not errors).lower()}")
    connectors = summary.get("connectors") or []
    gates = summary.get("human_gates") or []
    print(f"connectors: {', '.join(connectors) if isinstance(connectors, list) else '-'}")
    print(f"human_gates: {', '.join(gates) if isinstance(gates, list) else '-'}")
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")


def _join_command(command: list[str]) -> str:
    return " ".join(_quote(part) for part in command)


def _quote(part: str) -> str:
    if not part:
        return "''"
    if any(char.isspace() for char in part):
        return f'"{part}"'
    return part
