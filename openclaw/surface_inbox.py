from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .packet_inspector import PacketInspection, inspect_music_session_packet


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_ROOT = REPO_ROOT / ".openclaw-local"
INBOX_ROOT = LOCAL_ROOT / "inbox"
HISTORY_ROOT = INBOX_ROOT / "history"
LATEST_PACKET_PATH = INBOX_ROOT / "latest-music-session-packet.json"


@dataclass(frozen=True)
class PacketImportResult:
    ok: bool
    source_path: Path | None
    latest_path: Path
    history_path: Path | None
    inspection: PacketInspection | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def latest_music_packet_path() -> Path:
    return LATEST_PACKET_PATH


def default_downloads_dir() -> Path:
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    return home / "Downloads"


def find_latest_download_packet(downloads_dir: Path | None = None) -> Path | None:
    root = downloads_dir or default_downloads_dir()
    if not root.exists():
        return None
    candidates: list[Path] = []
    for pattern in ("music-session-packet*.json", "music-*.json", "*music-session*.json"):
        candidates.extend(path for path in root.glob(pattern) if path.is_file())
    seen: set[Path] = set()
    ordered = []
    for path in candidates:
        resolved = path.resolve()
        if resolved not in seen and path.stat().st_size <= 8 * 1024 * 1024:
            ordered.append(path)
            seen.add(resolved)
    ordered.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for path in ordered:
        try:
            if inspect_music_session_packet(path).ok:
                return path
        except Exception:
            continue
    return None


def import_music_packet(packet_path: str | Path) -> PacketImportResult:
    source = Path(packet_path).expanduser().resolve()
    if not source.exists() or not source.is_file():
        return PacketImportResult(
            ok=False,
            source_path=source,
            latest_path=LATEST_PACKET_PATH,
            history_path=None,
            inspection=None,
            errors=(f"packet file not found: {source}",),
        )
    try:
        inspection = inspect_music_session_packet(source)
    except Exception as error:
        return PacketImportResult(
            ok=False,
            source_path=source,
            latest_path=LATEST_PACKET_PATH,
            history_path=None,
            inspection=None,
            errors=(f"packet read failed: {error}",),
        )
    if not inspection.ok:
        return PacketImportResult(
            ok=False,
            source_path=source,
            latest_path=LATEST_PACKET_PATH,
            history_path=None,
            inspection=inspection,
            errors=tuple(inspection.errors),
            warnings=tuple(inspection.warnings),
        )

    INBOX_ROOT.mkdir(parents=True, exist_ok=True)
    HISTORY_ROOT.mkdir(parents=True, exist_ok=True)
    history_path = _history_path(inspection)
    shutil.copyfile(source, LATEST_PACKET_PATH)
    shutil.copyfile(source, history_path)
    return PacketImportResult(
        ok=True,
        source_path=source,
        latest_path=LATEST_PACKET_PATH,
        history_path=history_path,
        inspection=inspection,
        errors=(),
        warnings=tuple(inspection.warnings),
    )


def _history_path(inspection: PacketInspection) -> Path:
    session_id = _safe_name(str(inspection.packet.get("session_id") or "music-session"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return HISTORY_ROOT / f"{stamp}-{session_id}.json"


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-_")
    return cleaned[:96] or "music-session"
