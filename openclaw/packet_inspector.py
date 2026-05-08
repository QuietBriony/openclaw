from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PacketInspection:
    ok: bool
    packet: dict[str, Any]
    drum_floor: dict[str, Any]
    namima: dict[str, Any]
    chill: dict[str, Any]
    mic_follow: dict[str, Any]
    openclaw: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def inspect_music_session_packet(path: str | Path) -> PacketInspection:
    packet = _read_packet(Path(path))
    warnings: list[str] = []
    errors: list[str] = []
    _validate_packet(packet, warnings, errors)
    drum_floor = _translate_drum_floor(packet)
    namima = _translate_namima(packet)
    chill = _translate_chill(packet)
    mic_follow = _mic_follow_summary(packet)
    openclaw = _openclaw_summary(packet)
    return PacketInspection(
        ok=not errors,
        packet=_packet_summary(packet),
        drum_floor=drum_floor,
        namima=namima,
        chill=chill,
        mic_follow=mic_follow,
        openclaw=openclaw,
        warnings=warnings,
        errors=errors,
    )


def inspection_to_dict(inspection: PacketInspection) -> dict[str, Any]:
    return {
        "ok": inspection.ok,
        "packet": inspection.packet,
        "drum_floor": inspection.drum_floor,
        "namima": inspection.namima,
        "chill": inspection.chill,
        "mic_follow": inspection.mic_follow,
        "openclaw": inspection.openclaw,
        "warnings": inspection.warnings,
        "errors": inspection.errors,
    }


def _read_packet(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Music session packet must be a JSON object")
    return data


def _validate_packet(packet: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    required = (
        "version",
        "source_repo",
        "created_at",
        "session_id",
        "mode",
        "reference_gradient",
        "ucm_state",
        "music_intent",
        "routing",
        "safety",
    )
    for key in required:
        if key not in packet:
            errors.append(f"missing required packet field: {key}")

    if packet.get("source_repo") != "Music":
        errors.append("source_repo must be Music")
    if not packet.get("session_id"):
        errors.append("session_id must be present")

    safety = _obj(packet.get("safety"))
    if safety.get("metadata_only") is not True:
        errors.append("safety.metadata_only must be true")
    if safety.get("human_review_required") is not True:
        errors.append("safety.human_review_required must be true")
    for key in ("stores_audio", "stores_samples", "stores_lyrics"):
        if safety.get(key) is not False:
            errors.append(f"safety.{key} must be false")

    routing = _obj(packet.get("routing"))
    for key in ("drum_floor", "namima", "chill", "openclaw"):
        if key not in routing:
            warnings.append(f"routing.{key} is missing")
    if _obj(routing.get("openclaw")).get("human_review_required") is not True:
        warnings.append("routing.openclaw.human_review_required should be true")

    mic = _obj(_obj(packet.get("performance_state")).get("mic_follow"))
    if mic:
        if mic.get("metadata_only") is not True:
            warnings.append("performance_state.mic_follow.metadata_only should be true")
        if mic.get("stores_audio") is not False:
            warnings.append("performance_state.mic_follow.stores_audio should be false")


def _packet_summary(packet: dict[str, Any]) -> dict[str, Any]:
    gradient = _obj(_obj(packet.get("reference_gradient")).get("weights"))
    ucm = _obj(packet.get("ucm_state"))
    return {
        "session_id": str(packet.get("session_id") or ""),
        "mode": str(packet.get("mode") or ""),
        "created_at": str(packet.get("created_at") or ""),
        "version": packet.get("version"),
        "reference_gradient": {
            "haze": _unit(gradient.get("haze")),
            "memory": _unit(gradient.get("memory")),
            "micro": _unit(gradient.get("micro")),
            "ghost": _unit(gradient.get("ghost")),
            "chrome": _unit(gradient.get("chrome")),
            "organic": _unit(gradient.get("organic")),
        },
        "ucm": {
            "energy": _percent(ucm.get("energy")),
            "void": _percent(ucm.get("void")),
            "circle": _percent(ucm.get("circle")),
            "body": _percent(ucm.get("body")),
            "resource": _percent(ucm.get("resource")),
            "observer": _percent(ucm.get("observer")),
        },
    }


def _translate_drum_floor(packet: dict[str, Any]) -> dict[str, Any]:
    routing = _obj(packet.get("routing"))
    drum = _obj(routing.get("drum_floor"))
    groove = _obj(drum.get("groove_intent"))
    gradient = _obj(_obj(packet.get("reference_gradient")).get("weights"))
    ucm = _obj(packet.get("ucm_state"))
    density = _unit(drum.get("density"), _percent(ucm.get("energy")) / 100)
    pressure = _unit(drum.get("pressure"), _percent(ucm.get("body")) / 100)
    section = _section(drum.get("section") or _obj(packet.get("performance_state")).get("active_pad"))
    profile = _drum_profile(packet, drum, gradient, density, pressure)
    frame = _drum_frame(profile, packet, drum, gradient, pressure)
    style = str(groove.get("style") or "soft_pocket")
    resource = _percent(ucm.get("resource")) / 100
    voidness = _percent(ucm.get("void")) / 100
    micro = _unit(gradient.get("micro"))
    ghost = _unit(gradient.get("ghost"))
    organic = _unit(gradient.get("organic"))

    controls = {
        "bpm": _estimate_bpm(packet, density, pressure),
        "section": section,
        "energy": round(_clamp(_percent(ucm.get("energy"), density * 100), 0, 100)),
        "density": round(_clamp(density * 72 + resource * 18 + pressure * 10, 8, 92)),
        "swing": round(_clamp(4 + micro * 7 + organic * 5 - pressure * 2, 0, 18)),
        "humanize": round(_clamp(30 + micro * 24 + ghost * 20 + organic * 12, 18, 92)),
        "kit": _drum_kit(profile, packet, drum, pressure),
        "frame": frame,
        "risk": round(_clamp(16 + pressure * 24 + micro * 12, 8, 58)),
        "space": round(_clamp(24 + voidness * 38 + _unit(gradient.get("haze")) * 18 - pressure * 12, 12, 86)),
        "lift": round(_clamp(22 + resource * 30 + pressure * 24 + density * 16, 12, 86)),
        "fillDemand": round(_clamp(10 + micro * 24 + pressure * 18 + (12 if section == "chorus" else 0), 4, 68)),
        "crashGate": pressure > 0.62 and section != "bridge",
    }
    return {
        "enabled": drum.get("enabled") is not False,
        "review_only": True,
        "style": style,
        "profile": profile,
        "frame": frame,
        "controls": controls,
        "density": round(density, 3),
        "pressure": round(pressure, 3),
        "next": "preview via drum-floor adapter; use raw-drum-candidate-export only after human review",
    }


def _translate_namima(packet: dict[str, Any]) -> dict[str, Any]:
    routing = _obj(packet.get("routing"))
    namima = _obj(routing.get("namima"))
    mood_intent = _obj(namima.get("mood_intent"))
    gradient = _obj(_obj(packet.get("reference_gradient")).get("weights"))
    ucm = _obj(packet.get("ucm_state"))
    energy = _percent(ucm.get("energy")) / 100
    voidness = _percent(ucm.get("void")) / 100
    circle = _percent(ucm.get("circle")) / 100
    observer = _percent(ucm.get("observer")) / 100
    calm = circle * 0.3 + observer * 0.28 + voidness * 0.2 + _unit(gradient.get("haze")) * 0.22
    mood_text = str(mood_intent.get("mood") or namima.get("mood_intent") or "").lower()
    if namima.get("family_safe") is False:
        mood = "family_room"
    elif "transparent" in mood_text or voidness > 0.58:
        mood = "soft_sleep" if energy < 0.28 else "transparent_evening"
    elif "garden" in mood_text or calm > 0.62:
        mood = "garden_morning"
    elif "family" in mood_text or energy > 0.52:
        mood = "family_room"
    elif "sleep" in mood_text:
        mood = "soft_sleep"
    else:
        mood = "water_day"

    water_motion = _unit(namima.get("water_motion"), _percent(ucm.get("wave"), 35) / 100)
    brightness = min(_unit(namima.get("brightness"), _unit(gradient.get("chrome"), 0.42)), 0.78)
    calm_continuity = _unit((circle + observer) / 2, 0.45)
    energy_cap = min(_unit(mood_intent.get("safe_energy_cap"), 0.54), 0.62)
    return {
        "enabled": namima.get("enabled") is not False,
        "review_only": True,
        "mood": mood,
        "family_safe": namima.get("family_safe") is not False,
        "intent": {
            "water_motion": round(water_motion, 3),
            "brightness": round(brightness, 3),
            "calm_continuity": round(calm_continuity, 3),
            "energy_cap": round(energy_cap, 3),
            "foreground_energy": round(min(energy, 0.52), 3),
        },
        "next": "review safe mood only; no dark glitch, bass pressure, upload, or raw trace",
    }


def _mic_follow_summary(packet: dict[str, Any]) -> dict[str, Any]:
    mic = _obj(_obj(packet.get("performance_state")).get("mic_follow"))
    confidence = _unit(mic.get("confidence"))
    enabled = mic.get("enabled") is True and confidence > 0.08
    return {
        "enabled": enabled,
        "gesture": str(mic.get("gesture") or "silent"),
        "drive": round(_unit(mic.get("drive")), 3),
        "pulse": round(_unit(mic.get("pulse")), 3),
        "phrase": round(_unit(mic.get("phrase")), 3),
        "hum": round(_unit(mic.get("hum")), 3),
        "air": round(_unit(mic.get("air")), 3),
        "noisy": round(_unit(mic.get("noisy")), 3),
        "bpm_lock": _tempo(mic.get("bpm_lock")),
        "confidence": round(confidence, 3),
        "metadata_only": mic.get("metadata_only") is True,
        "stores_audio": False if mic.get("stores_audio") is False else True,
        "next": "use as a production hint only; never record, upload, or auto-start audio",
    }


def _openclaw_summary(packet: dict[str, Any]) -> dict[str, Any]:
    openclaw = _obj(_obj(packet.get("routing")).get("openclaw"))
    return {
        "enabled": openclaw.get("enabled") is not False,
        "promotion_status": str(openclaw.get("promotion_status") or "draft"),
        "human_review_required": openclaw.get("human_review_required") is True,
        "next_action": _normalize_next_action(openclaw.get("next_action")),
        "next": "turn listening notes into a small repo-specific PR only after human approval",
    }


def _translate_chill(packet: dict[str, Any]) -> dict[str, Any]:
    routing = _obj(packet.get("routing"))
    chill = _obj(routing.get("chill"))
    intent = _obj(chill.get("trio_intent"))
    gradient = _obj(_obj(packet.get("reference_gradient")).get("weights"))
    ucm = _obj(packet.get("ucm_state"))
    energy = _percent(ucm.get("energy"), 32) / 100
    creation = _percent(ucm.get("creation"), 28) / 100
    voidness = _percent(ucm.get("void"), 24) / 100
    observer = _percent(ucm.get("observer"), 48) / 100
    memory = _unit(gradient.get("memory"), 0.34)
    haze = _unit(gradient.get("haze"), 0.38)
    micro = _unit(gradient.get("micro"), 0.24)
    ghost = _unit(gradient.get("ghost"), 0.24)
    reference_text = str(intent.get("reference_id") or intent.get("referenceId") or "").lower()
    if reference_text in ("piano-jazz-chill", "rainy-lofi-room", "soft-solo-drift"):
        reference = reference_text
    elif memory > 0.5:
        reference = "soft-solo-drift"
    elif haze > 0.52 or _unit(gradient.get("chrome")) > 0.46:
        reference = "rainy-lofi-room"
    else:
        reference = "piano-jazz-chill"
    touch = _unit(intent.get("touch"), _clamp(0.16 + energy * 0.24 + micro * 0.12 - voidness * 0.1, 0.08, 0.68))
    phrase = _unit(intent.get("phrase"), _clamp(0.12 + creation * 0.22 + memory * 0.16 + ghost * 0.08, 0.08, 0.72))
    room = _unit(intent.get("room"), _clamp(0.54 + voidness * 0.2 + observer * 0.12 + haze * 0.12 - energy * 0.12, 0.42, 0.94))
    drum_support = _unit(chill.get("drum_support"), energy * 0.28 + ghost * 0.2 + micro * 0.12 - voidness * 0.18)
    pressure_target = intent.get("pressure_target")
    if pressure_target not in ("safe", "warm", "full"):
        pressure_target = "safe" if energy > 0.58 else "warm"
    return {
        "enabled": chill.get("enabled") is not False,
        "review_only": True,
        "reference": reference,
        "trio": {
            "touch": round(touch, 3),
            "phrase": round(phrase, 3),
            "room": round(room, 3),
            "bass_on": intent.get("bass_on") is not False,
            "flow_on": intent.get("flow_on") is not False,
            "drums_suggested": bool(intent.get("drums_suggested", drum_support > 0.34 and voidness < 0.58)),
            "pressure_target": pressure_target,
        },
        "piano_memory": round(_unit(chill.get("piano_memory"), memory * 0.45 + haze * 0.22), 3),
        "drum_support": round(drum_support, 3),
        "next": "open chill session; START remains human-operated",
    }


def _normalize_next_action(value: Any) -> dict[str, Any]:
    action = _obj(value)
    destination = str(action.get("destination") or "").strip() or "openclaw"
    labels = {
        "music": "Musicで削る",
        "chill": "chillで聴く",
        "drum_floor": "drum-floorで押す",
        "namima": "namimaで空気に逃がす",
        "openclaw": "OpenClawで見る",
    }
    return {
        "destination": destination,
        "label": str(action.get("label") or labels.get(destination) or destination),
        "reason": str(action.get("reason") or "Musicのpacketを安全に見立てる。"),
        "action": str(action.get("action") or "OpenClawで結果を見て、必要ならこのチャットへ投げる。"),
        "confidence": round(_unit(action.get("confidence"), 0.28), 3),
        "manual_start_required": action.get("manual_start_required") is not False,
        "metadata_only": action.get("metadata_only") is not False,
    }


def _drum_profile(packet: dict[str, Any], drum: dict[str, Any], gradient: dict[str, Any], density: float, pressure: float) -> str:
    style = str(_obj(drum.get("groove_intent")).get("style") or "").lower()
    section = str(drum.get("section") or "").lower()
    mode = str(packet.get("mode") or "").lower()
    if "dry_grid" in style or "techno" in mode:
        return "breakbeat_live"
    if "ghost_pressure" in style or pressure > 0.68 or section == "punch":
        return "raw_live_drum_drive"
    if "broken" in style or "idm" in mode or _unit(gradient.get("micro")) > 0.48:
        return "nerdy_jazzy_hiphop"
    if section == "void" or _unit(gradient.get("haze")) > 0.56 or density < 0.26:
        return "dubby_half_time"
    return "nerdy_jazzy_hiphop"


def _drum_frame(profile: str, packet: dict[str, Any], drum: dict[str, Any], gradient: dict[str, Any], pressure: float) -> str:
    section = str(drum.get("section") or "").lower()
    style = str(_obj(drum.get("groove_intent")).get("style") or "").lower()
    mode = str(packet.get("mode") or "").lower()
    if profile == "raw_live_drum_drive":
        return "raw_live_break_drive"
    if "dry_grid" in style or pressure > 0.66:
        return "live_break_pressure"
    if section == "void" or _unit(gradient.get("haze")) > 0.58 or mode == "ambient":
        return "dub_space_lift"
    if "broken" in style or _unit(gradient.get("micro")) > 0.46:
        return "jazzy_ghost_glue"
    return "deep_neo_soul_pocket"


def _drum_kit(profile: str, packet: dict[str, Any], drum: dict[str, Any], pressure: float) -> str:
    section = str(drum.get("section") or "").lower()
    style = str(_obj(drum.get("groove_intent")).get("style") or "").lower()
    mode = str(packet.get("mode") or "").lower()
    if section == "void" or mode == "ambient":
        return "dub_space"
    if profile == "raw_live_drum_drive" or pressure > 0.66:
        return "live_breaker"
    if "broken" in style or "soft" in style:
        return "dusty_pocket"
    return "hard_bop_room"


def _estimate_bpm(packet: dict[str, Any], density: float, pressure: float) -> int:
    mode = str(packet.get("mode") or "").lower()
    if "techno" in mode:
        return 126
    if "idm" in mode or "reference_gradient" in mode:
        return round(96 + density * 28 + pressure * 10)
    if "ambient" in mode:
        return round(72 + density * 18)
    return round(84 + density * 34 + pressure * 10)


def _section(value: Any) -> str:
    mapping = {
        "drift": "verse",
        "repeat": "chorus",
        "punch": "chorus",
        "void": "bridge",
        "self_running": "verse",
        "manual": "verse",
        "intro": "verse",
        "verse": "verse",
        "chorus": "chorus",
        "bridge": "bridge",
        "end": "end",
    }
    return mapping.get(str(value or "").lower(), "verse")


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _unit(value: Any, fallback: float = 0.0) -> float:
    try:
        return _clamp(float(value), 0, 1)
    except (TypeError, ValueError):
        return fallback


def _percent(value: Any, fallback: float = 0.0) -> float:
    try:
        return _clamp(float(value), 0, 100)
    except (TypeError, ValueError):
        return fallback


def _tempo(value: Any) -> int:
    try:
        return round(_clamp(float(value), 0, 240))
    except (TypeError, ValueError):
        return 0


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))
