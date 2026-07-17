"""Analisador de medicamentos — compara lista atual com anterior (spec §9.5)."""

from __future__ import annotations

from typing import Any

from app.state import AnalyzerResult


def analyze_medications(
    current: list[dict[str, Any]] | None,
    previous: list[dict[str, Any]] | None,
) -> AnalyzerResult:
    if current is None:
        return AnalyzerResult(
            status="missing",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=["Nenhum medicamento informado."],
        )

    if previous is None:
        return AnalyzerResult(
            status="ok",
            severity="NORMAL",
            score=0,
            findings=[
                {
                    "type": "no_baseline",
                    "description": "Sem histórico de medicamentos para comparação.",
                }
            ],
            evidence=[
                {
                    "current_medications": current,
                    "previous_medications": None,
                }
            ],
            limitations=["Sem baseline para comparação de prescrição."],
        )

    previous_names = {m.get("name", "") for m in previous}
    current_names = {m.get("name", "") for m in current}

    changes: list[dict[str, Any]] = []
    score = 0

    added_names = current_names - previous_names
    removed_names = previous_names - current_names
    common_names = current_names & previous_names

    for med in current:
        name = med.get("name", "")
        if name in added_names:
            changes.append(
                {
                    "type": "added",
                    "medication": name,
                    "dose": med.get("dose", ""),
                    "frequency": med.get("frequency", ""),
                    "detail": f"Medicamento '{name}' adicionado à prescrição.",
                }
            )
            score += 20

    for med in previous:
        name = med.get("name", "")
        if name in removed_names:
            changes.append(
                {
                    "type": "removed",
                    "medication": name,
                    "detail": f"Medicamento '{name}' removido da prescrição.",
                }
            )
            score += 15

    current_by_name = {m.get("name", ""): m for m in current}
    previous_by_name = {m.get("name", ""): m for m in previous}

    for name in common_names:
        cur = current_by_name[name]
        prev = previous_by_name[name]
        dose_changed = cur.get("dose") != prev.get("dose")
        freq_changed = cur.get("frequency") != prev.get("frequency")
        detail_parts: list[str] = []
        if dose_changed:
            detail_parts.append(f"dose de '{prev.get('dose')}' para '{cur.get('dose')}'")
            score += 10
        if freq_changed:
            detail_parts.append(
                f"frequência de '{prev.get('frequency')}' para '{cur.get('frequency')}'"
            )
            score += 10
        if detail_parts:
            changes.append(
                {
                    "type": "modified",
                    "medication": name,
                    "dose": cur.get("dose", ""),
                    "frequency": cur.get("frequency", ""),
                    "previous_dose": prev.get("dose", ""),
                    "previous_frequency": prev.get("frequency", ""),
                    "detail": f"Medicamento '{name}': " + ", ".join(detail_parts) + ".",
                }
            )

    severity = "NORMAL"
    if score >= 30:
        severity = "ATENÇÃO"
    if score >= 50:
        severity = "ALERTA"

    return AnalyzerResult(
        status="ok",
        severity=severity,
        score=min(100, score),
        findings=changes
        if changes
        else [{"type": "no_changes", "description": "Sem alterações detectadas."}],
        evidence=[
            {
                "current_medications": current,
                "previous_medications": previous,
                "total_changes": len(changes),
                "added": len(added_names),
                "removed": len(removed_names),
                "modified": sum(1 for c in changes if c.get("type") == "modified"),
            }
        ],
        limitations=[],
    )
