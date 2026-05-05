from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HarvestInspection:
    ok: bool
    source: dict[str, Any]
    classification: dict[str, Any]
    evaluation: dict[str, Any]
    harvest: dict[str, Any]
    routing: dict[str, Any]
    safety: dict[str, Any]
    promotion: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def inspect_repo_harvest_sidecar(path: str | Path) -> HarvestInspection:
    sidecar = _read_sidecar(Path(path))
    warnings: list[str] = []
    errors: list[str] = []
    _validate_sidecar(sidecar, warnings, errors)
    return HarvestInspection(
        ok=not errors,
        source=_source_summary(sidecar),
        classification=_classification_summary(sidecar),
        evaluation=_evaluation_summary(sidecar, warnings),
        harvest=_harvest_summary(sidecar),
        routing=_routing_summary(sidecar),
        safety=_safety_summary(sidecar),
        promotion=_promotion_summary(sidecar),
        warnings=warnings,
        errors=errors,
    )


def harvest_inspection_to_dict(inspection: HarvestInspection) -> dict[str, Any]:
    return {
        "ok": inspection.ok,
        "source": inspection.source,
        "classification": inspection.classification,
        "evaluation": inspection.evaluation,
        "harvest": inspection.harvest,
        "routing": inspection.routing,
        "safety": inspection.safety,
        "promotion": inspection.promotion,
        "warnings": inspection.warnings,
        "errors": inspection.errors,
    }


def _read_sidecar(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Repo harvest sidecar must be a JSON object")
    return data


def _validate_sidecar(sidecar: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    required = (
        "version",
        "source",
        "classification",
        "evaluation",
        "harvest",
        "routing",
        "safety",
        "promotion",
    )
    for key in required:
        if key not in sidecar:
            errors.append(f"missing required sidecar field: {key}")

    source = _obj(sidecar.get("source"))
    if not source.get("repo_full_name"):
        errors.append("source.repo_full_name must be present")
    if not source.get("repo_url"):
        warnings.append("source.repo_url is missing")

    classification = _obj(sidecar.get("classification"))
    targets = classification.get("target_repos")
    if not isinstance(targets, list) or not targets:
        errors.append("classification.target_repos must include at least one target")

    evaluation = _obj(sidecar.get("evaluation"))
    if evaluation.get("has_audio_files") is True:
        warnings.append("evaluation.has_audio_files is true; keep this review-only")
    if evaluation.get("has_samples") is True:
        warnings.append("evaluation.has_samples is true; do not import samples or sample URLs")
    if evaluation.get("has_model_weights") is True:
        warnings.append("evaluation.has_model_weights is true; do not import model weights")
    if evaluation.get("has_github_actions") is True:
        warnings.append("evaluation.has_github_actions is true; do not copy workflows")

    harvest = _obj(sidecar.get("harvest"))
    if not isinstance(harvest.get("useful_ideas"), list):
        errors.append("harvest.useful_ideas must be an array")
    if not isinstance(harvest.get("do_not_copy"), list):
        errors.append("harvest.do_not_copy must be an array")

    safety = _obj(sidecar.get("safety"))
    expected_true = (
        "metadata_only",
        "human_review_required",
        "no_direct_code_copy",
        "no_audio_import",
        "no_sample_import",
        "no_dependency_import",
        "no_workflow_change",
    )
    for key in expected_true:
        if safety.get(key) is not True:
            errors.append(f"safety.{key} must be true")

    promotion = _obj(sidecar.get("promotion"))
    if promotion.get("status") == "approved-for-runtime-pr":
        warnings.append("promotion is runtime-approved; require a small repo-specific PR and rollback")


def _source_summary(sidecar: dict[str, Any]) -> dict[str, Any]:
    source = _obj(sidecar.get("source"))
    return {
        "repo_full_name": str(source.get("repo_full_name") or ""),
        "repo_url": str(source.get("repo_url") or ""),
        "owner": str(source.get("owner") or ""),
        "visibility": str(source.get("visibility") or "unknown"),
        "internal_or_external": str(source.get("internal_or_external") or "unknown"),
        "license": source.get("license"),
        "inspected_at": str(source.get("inspected_at") or ""),
    }


def _classification_summary(sidecar: dict[str, Any]) -> dict[str, Any]:
    classification = _obj(sidecar.get("classification"))
    targets = classification.get("target_repos")
    return {
        "category": str(classification.get("category") or ""),
        "current_role": str(classification.get("current_role") or ""),
        "target_repos": [str(item) for item in targets] if isinstance(targets, list) else [],
        "risk_level": str(classification.get("risk_level") or "unknown"),
    }


def _evaluation_summary(sidecar: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    evaluation = _obj(sidecar.get("evaluation"))
    risk_flags = [
        key
        for key in ("has_audio_files", "has_samples", "has_model_weights", "has_github_actions")
        if evaluation.get(key) is True
    ]
    if risk_flags:
        warnings.append("risk flags present: " + ", ".join(risk_flags))
    return {
        "dependency_weight": str(evaluation.get("dependency_weight") or "unknown"),
        "maintenance_status": str(evaluation.get("maintenance_status") or "unknown"),
        "browser_compatible": evaluation.get("browser_compatible") is True,
        "demo_available": evaluation.get("demo_available") is True,
        "risk_flags": risk_flags,
    }


def _harvest_summary(sidecar: dict[str, Any]) -> dict[str, Any]:
    harvest = _obj(sidecar.get("harvest"))
    return {
        "useful_ideas": _string_list(harvest.get("useful_ideas")),
        "do_not_copy": _string_list(harvest.get("do_not_copy")),
        "production_translation": _obj(harvest.get("production_translation")),
        "recommended_next_pr": str(harvest.get("recommended_next_pr") or ""),
    }


def _routing_summary(sidecar: dict[str, Any]) -> dict[str, Any]:
    routing = _obj(sidecar.get("routing"))
    summary: dict[str, Any] = {}
    for key in ("music", "drum_floor", "namima", "chill", "openclaw"):
        route = _obj(routing.get(key))
        summary[key] = {
            "enabled": route.get("enabled") is True,
            "intent": str(route.get("intent") or ""),
        }
    return summary


def _safety_summary(sidecar: dict[str, Any]) -> dict[str, Any]:
    safety = _obj(sidecar.get("safety"))
    return {
        "metadata_only": safety.get("metadata_only") is True,
        "human_review_required": safety.get("human_review_required") is True,
        "no_direct_code_copy": safety.get("no_direct_code_copy") is True,
        "no_audio_import": safety.get("no_audio_import") is True,
        "no_sample_import": safety.get("no_sample_import") is True,
        "no_dependency_import": safety.get("no_dependency_import") is True,
        "no_workflow_change": safety.get("no_workflow_change") is True,
    }


def _promotion_summary(sidecar: dict[str, Any]) -> dict[str, Any]:
    promotion = _obj(sidecar.get("promotion"))
    return {
        "status": str(promotion.get("status") or "not-reviewed"),
        "reviewer_notes": str(promotion.get("reviewer_notes") or ""),
        "rollback_plan": str(promotion.get("rollback_plan") or ""),
    }


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
