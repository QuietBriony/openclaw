from __future__ import annotations

import argparse
import json
from pathlib import Path

from .connectors import (
    candidate_connector_id,
    drum_floor_generate_command,
    drum_floor_inspect_command,
    inspect_registry,
)
from .contracts import load_manifest, validate_manifest
from .doctor import doctor_summary, run_doctor
from .local_runner import list_local_candidates, run_local_drum_floor
from .packet_inspector import inspect_music_session_packet, inspection_to_dict
from .planner import build_session_plan
from .surface_inbox import (
    find_latest_download_packet,
    import_music_packet,
    latest_music_packet_path,
)


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

    local = subparsers.add_parser(
        "local-generate",
        help="Generate and inspect a local drum-floor candidate under .openclaw-local. Requires --execute.",
    )
    local.add_argument("manifest", type=Path)
    local.add_argument("--candidate-id", help="Override the candidate id.")
    local.add_argument("--python", default="python", help="Python executable to use inside the drum-floor repo.")
    local.add_argument("--execute", action="store_true", help="Actually run generation and inspect. Without this, print the local commands only.")

    local_list = subparsers.add_parser(
        "local-list",
        help="List generated local candidates under .openclaw-local.",
    )
    local_list.add_argument("--session-id", help="Filter by session id.")

    doctor = subparsers.add_parser(
        "doctor",
        help="Check local Surface producer readiness and external OpenClaw subscription/auth hints.",
    )
    doctor.add_argument("--python", default="python", help="Python executable to use for drum-floor checks.")

    packet = subparsers.add_parser(
        "packet-inspect",
        help="Inspect a local Music session packet and print review-only routing translations.",
    )
    packet.add_argument("packet", nargs="?", type=Path, help="Path to a Music session packet JSON file.")
    packet.add_argument("--latest", action="store_true", help="Inspect .openclaw-local/inbox/latest-music-session-packet.json.")
    packet.add_argument("--json", action="store_true", help="Emit inspection as JSON.")

    packet_import = subparsers.add_parser(
        "packet-import",
        help="Import a Music session packet into the Surface .openclaw-local inbox.",
    )
    packet_import.add_argument("packet", nargs="?", type=Path, help="Path to a Music session packet JSON file.")
    packet_import.add_argument("--latest-download", action="store_true", help="Import the newest valid Music packet from Downloads.")

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
        connector_id = candidate_connector_id(manifest)
        if connector_id is None:
            print("generate:")
            print("  -")
            print("inspect:")
            print("  -")
            print("note: this manifest is observe-only; use sessions/examples/raw-drum-candidate-export.example.json for local drum candidate export.")
            return 0
        print("generate:")
        print("  " + _join_command(drum_floor_generate_command(manifest, args.candidate_id, connector_id)))
        print("inspect:")
        print("  " + _join_command(drum_floor_inspect_command(manifest, args.candidate_id, connector_id)))
        print("note: OpenClaw prints these commands only; it does not execute or arm candidates.")
        return 0

    if args.command == "local-generate":
        result = run_local_drum_floor(
            args.manifest,
            candidate_id=args.candidate_id,
            python_cmd=args.python,
            execute=args.execute,
        )
        print(f"session: {result.session_id}")
        print(f"connector: {result.connector_id}")
        print(f"candidate_id: {result.candidate_id}")
        print(f"candidate_dir: {result.candidate_dir}")
        print(f"executed: {str(result.executed).lower()}")
        print(f"ok: {str(result.ok).lower()}")
        print("generate:")
        print("  " + (_join_command(result.generate_command) if result.generate_command else "-"))
        print("inspect:")
        print("  " + (_join_command(result.inspect_command) if result.inspect_command else "-"))
        if result.generate_returncode is not None:
            print(f"generate_returncode: {result.generate_returncode}")
        if result.inspect_returncode is not None:
            print(f"inspect_returncode: {result.inspect_returncode}")
        if result.run_log:
            print(f"run_log: {result.run_log}")
        for line in _important_lines(result.generate_stdout):
            print(line)
        for line in _important_lines(result.inspect_stdout):
            print(line)
        for error in result.errors:
            print(f"error: {error}")
        for note in result.notes:
            print(f"note: {note}")
        if any("candidate already exists" in error for error in result.errors):
            print("hint: use local-list to view existing candidates, or pass --candidate-id <new-name> for a fresh output path.")
        if not args.execute:
            print("note: add --execute to generate locally. OpenClaw will not arm, record, upload, or push.")
        return 0 if result.ok else 1

    if args.command == "local-list":
        candidates = list_local_candidates(args.session_id)
        print(f"count: {len(candidates)}")
        for candidate in candidates:
            files = []
            if candidate.has_pattern:
                files.append("pattern")
            if candidate.has_midi:
                files.append("midi")
            if candidate.has_preview:
                files.append("preview")
            if candidate.has_meta:
                files.append("meta")
            print(f"- session={candidate.session_id} candidate={candidate.candidate_id} files={','.join(files) or '-'}")
            print(f"  path={candidate.path}")
        return 0

    if args.command == "doctor":
        checks = run_doctor(args.python)
        ok, warnings, failures = doctor_summary(checks)
        print(f"ok: {str(ok).lower()}")
        print(f"required_failures: {failures}")
        print(f"optional_warnings: {warnings}")
        for check in checks:
            status = "ok" if check.ok else ("warn" if not check.required else "fail")
            print(f"{status}: {check.name} - {check.detail}")
        print("subscription_note: external OpenClaw subscription/auth cannot be verified unless its CLI or token is installed; repo-local OpenClaw works without a subscription.")
        return 0 if ok else 1

    if args.command == "packet-inspect":
        packet_path = _packet_path_from_args(parser, args)
        inspection = inspect_music_session_packet(packet_path)
        if args.json:
            print(json.dumps(inspection_to_dict(inspection), indent=2, ensure_ascii=False))
            return 0 if inspection.ok else 1
        _print_packet_inspection(inspection_to_dict(inspection))
        return 0 if inspection.ok else 1

    if args.command == "packet-import":
        if args.latest_download and args.packet:
            parser.error("packet-import accepts either --latest-download or <packet>, not both")
        packet_path = find_latest_download_packet() if args.latest_download else args.packet
        if not packet_path:
            parser.error("packet-import requires <packet> or --latest-download with a valid Music packet in Downloads")
        result = import_music_packet(packet_path)
        _print_packet_import(result)
        return 0 if result.ok else 1

    parser.error("unknown command")
    return 2


def _packet_path_from_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Path:
    if args.latest and args.packet:
        parser.error("packet-inspect accepts either --latest or <packet>, not both")
    if args.latest:
        latest = latest_music_packet_path()
        if not latest.exists():
            parser.error(f"latest packet not found: {latest}; run packet-import first")
        return latest
    if args.packet:
        return args.packet
    parser.error("packet-inspect requires <packet> or --latest")
    raise AssertionError("unreachable")


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


def _important_lines(output: str) -> list[str]:
    prefixes = (
        "generated:",
        "candidate:",
        "frame:",
        "ok:",
        "style:",
        "bpm:",
        "bars:",
        "energy:",
        "seed:",
        "event_count:",
    )
    return [line for line in output.splitlines() if line.startswith(prefixes)]


def _print_packet_import(result: object) -> None:
    inspection = result.inspection
    inspection_dict = inspection_to_dict(inspection) if inspection else {}
    packet = inspection_dict.get("packet") if isinstance(inspection_dict.get("packet"), dict) else {}
    openclaw = inspection_dict.get("openclaw") if isinstance(inspection_dict.get("openclaw"), dict) else {}
    next_action = openclaw.get("next_action") if isinstance(openclaw.get("next_action"), dict) else {}
    print(f"ok: {str(bool(result.ok)).lower()}")
    print(f"source: {result.source_path or '-'}")
    print(f"latest: {result.latest_path}")
    print(f"history: {result.history_path or '-'}")
    print(f"packet: {packet.get('session_id') or '-'}")
    print(f"next_action: {next_action.get('label') or '-'}")
    print(f"destination: {next_action.get('destination') or '-'}")
    if next_action.get("action"):
        print(f"action: {next_action.get('action')}")
    print("surface_next:")
    print("  python .\\openclaw_cli.py packet-inspect --latest")
    if next_action.get("destination") == "drum_floor":
        print("  $py = \"$env:LOCALAPPDATA\\Programs\\Python\\Python313\\python.exe\"")
        print("  python .\\openclaw_cli.py local-generate sessions\\examples\\raw-drum-candidate-export.example.json --candidate-id raw-drive-001 --execute --python $py")
    for warning in result.warnings:
        print(f"warning: {warning}")
    for error in result.errors:
        print(f"error: {error}")


def _print_packet_inspection(inspection: dict[str, object]) -> None:
    packet = inspection.get("packet") if isinstance(inspection.get("packet"), dict) else {}
    drum = inspection.get("drum_floor") if isinstance(inspection.get("drum_floor"), dict) else {}
    namima = inspection.get("namima") if isinstance(inspection.get("namima"), dict) else {}
    chill = inspection.get("chill") if isinstance(inspection.get("chill"), dict) else {}
    openclaw = inspection.get("openclaw") if isinstance(inspection.get("openclaw"), dict) else {}
    next_action = openclaw.get("next_action") if isinstance(openclaw.get("next_action"), dict) else {}
    print(f"ok: {str(bool(inspection.get('ok'))).lower()}")
    print(f"packet: {packet.get('session_id') or '-'}")
    print(f"mode: {packet.get('mode') or '-'}")
    print(f"created_at: {packet.get('created_at') or '-'}")
    print("")
    print("drum_floor:")
    print(f"  enabled: {str(bool(drum.get('enabled'))).lower()}")
    print(f"  profile: {drum.get('profile') or '-'}")
    print(f"  frame: {drum.get('frame') or '-'}")
    print(f"  style: {drum.get('style') or '-'}")
    print(f"  density: {drum.get('density')}")
    print(f"  pressure: {drum.get('pressure')}")
    controls = drum.get("controls") if isinstance(drum.get("controls"), dict) else {}
    control_text = ", ".join(f"{key}={value}" for key, value in controls.items())
    print(f"  controls: {control_text or '-'}")
    print(f"  next: {drum.get('next') or '-'}")
    print("")
    print("namima:")
    print(f"  enabled: {str(bool(namima.get('enabled'))).lower()}")
    print(f"  mood: {namima.get('mood') or '-'}")
    print(f"  family_safe: {str(bool(namima.get('family_safe'))).lower()}")
    intent = namima.get("intent") if isinstance(namima.get("intent"), dict) else {}
    intent_text = ", ".join(f"{key}={value}" for key, value in intent.items())
    print(f"  intent: {intent_text or '-'}")
    print(f"  next: {namima.get('next') or '-'}")
    print("")
    print("chill:")
    print(f"  enabled: {str(bool(chill.get('enabled'))).lower()}")
    print(f"  reference: {chill.get('reference') or '-'}")
    trio = chill.get("trio") if isinstance(chill.get("trio"), dict) else {}
    trio_text = ", ".join(f"{key}={value}" for key, value in trio.items())
    print(f"  trio: {trio_text or '-'}")
    print(f"  piano_memory: {chill.get('piano_memory')}")
    print(f"  drum_support: {chill.get('drum_support')}")
    print(f"  next: {chill.get('next') or '-'}")
    print("")
    print("openclaw:")
    print(f"  promotion_status: {openclaw.get('promotion_status') or '-'}")
    print(f"  human_review_required: {str(bool(openclaw.get('human_review_required'))).lower()}")
    print(f"  next_action: {next_action.get('label') or '-'}")
    print(f"  destination: {next_action.get('destination') or '-'}")
    print(f"  action: {next_action.get('action') or '-'}")
    print(f"  next: {openclaw.get('next') or '-'}")
    for warning in inspection.get("warnings") or []:
        print(f"warning: {warning}")
    for error in inspection.get("errors") or []:
        print(f"error: {error}")
