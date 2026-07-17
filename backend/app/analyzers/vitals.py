"""Analisador de sinais vitais — regras de faixa, tendência e z-score (spec §9.4)."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from app.state import AnalyzerResult

# Faixas clínicas de demonstração — NÃO são protocolo médico validado.
REFERENCE_RANGES: dict[str, tuple[float, float]] = {
    "heart_rate": (60, 100),
    "systolic_bp": (90, 140),
    "diastolic_bp": (60, 90),
    "spo2": (95, 100),
    "respiratory_rate": (12, 20),
    "temperature": (36.0, 37.5),
}

# Limiares críticos
CRITICAL_THRESHOLDS: dict[str, tuple[float, float]] = {
    "heart_rate": (40, 140),
    "spo2": (85, 100),
    "systolic_bp": (80, 180),
    "temperature": (35.0, 39.0),
}

REQUIRED_COLUMNS = {"timestamp"}
VITAL_COLUMNS = {
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "respiratory_rate",
    "temperature",
}


def analyze_vitals(csv_bytes: bytes, max_rows: int = 500) -> AnalyzerResult:
    if not csv_bytes:
        return AnalyzerResult(
            status="missing",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=["CSV de sinais vitais não informado."],
        )

    try:
        df = _parse_csv(csv_bytes, max_rows)
    except ValueError as exc:
        return AnalyzerResult(
            status="failed",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=[f"Erro ao processar CSV: {exc}"],
        )

    findings: list[dict[str, Any]] = []
    total_score = 0

    # 1. Regras de faixa
    range_findings = _check_ranges(df)
    findings.extend(range_findings)
    for f in range_findings:
        total_score += f.get("score_contribution", 0)

    # 2. Tendência de piora
    if len(df) >= 3:
        trend_findings = _check_trends(df)
        findings.extend(trend_findings)
        for f in trend_findings:
            total_score += f.get("score_contribution", 0)

    # 3. Z-score
    if len(df) >= 10:
        zscore_findings = _check_zscore(df)
        findings.extend(zscore_findings)
        for f in zscore_findings:
            total_score += f.get("score_contribution", 0)

    # Normalizar score
    score = min(100, int(total_score * 2)) if findings else 0

    severity = "NORMAL"
    high_findings = [f for f in findings if f.get("severity") == "ALTA"]
    medium_findings = [f for f in findings if f.get("severity") == "MÉDIA"]
    if len(high_findings) >= 3 or score >= 60:
        severity = "ALERTA"
    elif high_findings or len(medium_findings) >= 3 or score >= 30:
        severity = "ATENÇÃO"

    cols_found = [c for c in VITAL_COLUMNS if c in df.columns]
    limitations: list[str] = []
    missing_cols = VITAL_COLUMNS - set(cols_found)
    if missing_cols:
        limitations.append(f"Colunas ausentes no CSV: {', '.join(sorted(missing_cols))}")

    return AnalyzerResult(
        status="ok",
        severity=severity,
        score=score,
        findings=findings,
        evidence=[
            {
                "total_rows": len(df),
                "columns_analyzed": cols_found,
                "anomaly_count": len(findings),
                "high_severity_count": len(high_findings),
                "medium_severity_count": len(medium_findings),
            }
        ],
        limitations=limitations,
    )


def _parse_csv(csv_bytes: bytes, max_rows: int) -> pd.DataFrame:
    content = csv_bytes.decode("utf-8", errors="replace")
    df = pd.read_csv(io.StringIO(content))

    if len(df) > max_rows:
        raise ValueError(f"CSV excede o limite de {max_rows} linhas.")

    if "timestamp" not in df.columns:
        raise ValueError("Coluna 'timestamp' obrigatória não encontrada.")

    vital_cols = [c for c in VITAL_COLUMNS if c in df.columns]
    if not vital_cols:
        raise ValueError("Nenhuma coluna de sinal vital reconhecida.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    for col in vital_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _check_ranges(df: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for col, (low, high) in REFERENCE_RANGES.items():
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        for idx, value in series.items():
            ts = str(df.loc[idx, "timestamp"]) if idx in df.index else "?"
            if value < low:
                severity = "ALTA" if CRITICAL_THRESHOLDS.get(col, (0, 999))[0] > value else "MÉDIA"
                findings.append(
                    {
                        "signal": col,
                        "timestamp": ts,
                        "value": round(float(value), 1),
                        "rule": "below_range",
                        "reference": f"{low}-{high}",
                        "severity": severity,
                        "detail": f"{col}={value} abaixo do mínimo ({low}).",
                        "score_contribution": 15 if severity == "ALTA" else 8,
                    }
                )
            elif value > high:
                severity = "ALTA" if CRITICAL_THRESHOLDS.get(col, (0, 999))[1] < value else "MÉDIA"
                findings.append(
                    {
                        "signal": col,
                        "timestamp": ts,
                        "value": round(float(value), 1),
                        "rule": "above_range",
                        "reference": f"{low}-{high}",
                        "severity": severity,
                        "detail": f"{col}={value} acima do máximo ({high}).",
                        "score_contribution": 15 if severity == "ALTA" else 8,
                    }
                )
    return findings


def _check_trends(df: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for col in ["spo2", "heart_rate", "respiratory_rate"]:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) < 3:
            continue
        x = range(len(series))
        y = series.values
        slope = _linear_slope(x, y)
        mean_val = float(series.mean())
        if abs(slope) < 0.01:
            continue
        normalized_slope = slope / max(abs(mean_val), 1) if mean_val != 0 else slope
        if abs(normalized_slope) > 0.05:
            direction = (
                "piora"
                if (col == "spo2" and slope < 0) or (col != "spo2" and slope > 0)
                else "melhora"
            )
            severity = "MÉDIA" if direction == "piora" else "BAIXA"
            findings.append(
                {
                    "signal": col,
                    "timestamp": str(df["timestamp"].iloc[-1]),
                    "rule": "trend",
                    "slope": round(float(slope), 4),
                    "direction": direction,
                    "severity": severity,
                    "detail": f"Tendência de {direction} em {col} (slope={slope:.4f}).",
                    "score_contribution": 10 if severity == "MÉDIA" else 5,
                }
            )
    return findings


def _check_zscore(df: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for col in VITAL_COLUMNS:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) < 10:
            continue
        mean = series.mean()
        std = series.std()
        if std == 0:
            continue
        z = ((series - mean) / std).abs()
        for idx, z_val in z.items():
            if z_val > 2.5:
                findings.append(
                    {
                        "signal": col,
                        "timestamp": str(df.loc[idx, "timestamp"]),
                        "value": round(float(series[idx]), 1),
                        "rule": "zscore",
                        "z_score": round(float(z_val), 2),
                        "severity": "MÉDIA" if z_val > 3.0 else "BAIXA",
                        "detail": f"{col}={series[idx]:.1f} com Z-score={z_val:.2f} (>2.5).",
                        "score_contribution": 10 if z_val > 3.0 else 5,
                    }
                )
    return findings


def _linear_slope(x: range, y: list[float]) -> float:
    """Coeficiente angular de regressão linear simples."""
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y, strict=True))
    den = sum((xi - mx) ** 2 for xi in x)
    return float(num / den) if den != 0 else 0.0
