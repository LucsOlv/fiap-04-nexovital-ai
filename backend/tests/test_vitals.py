"""Testes do analisador de sinais vitais."""

from app.analyzers.vitals import analyze_vitals

VALID_CSV = (
    "timestamp,heart_rate,spo2,respiratory_rate,temperature\n"
    "2026-07-16T10:00:00Z,78,98,16,36.6\n"
    "2026-07-16T10:05:00Z,82,97,17,36.7\n"
    "2026-07-16T10:10:00Z,80,96,16,36.6\n"
    "2026-07-16T10:15:00Z,79,97,17,36.8\n"
    "2026-07-16T10:20:00Z,81,98,16,36.5\n"
    "2026-07-16T10:25:00Z,78,97,17,36.7\n"
    "2026-07-16T10:30:00Z,82,96,16,36.6\n"
    "2026-07-16T10:35:00Z,80,97,16,36.8\n"
    "2026-07-16T10:40:00Z,79,98,15,36.5\n"
    "2026-07-16T10:45:00Z,81,97,16,36.7\n"
)


def test_empty_csv():
    result = analyze_vitals(b"")
    assert result["status"] == "missing"


def test_valid_csv_parses():
    result = analyze_vitals(VALID_CSV.encode())
    assert result["status"] == "ok"


def test_csv_without_timestamp():
    csv = "heart_rate,spo2\n80,98"
    result = analyze_vitals(csv.encode())
    assert result["status"] == "failed"
    assert any("timestamp" in lim.lower() for lim in result.get("limitations", []))


def test_csv_without_vital_columns():
    csv = "timestamp,x,y\n2026-07-16T10:00:00Z,1,2"
    result = analyze_vitals(csv.encode())
    assert result["status"] == "failed"


def test_out_of_range_spo2_detected():
    csv = "timestamp,spo2\n2026-07-16T10:00:00Z,90\n2026-07-16T10:05:00Z,88\n"
    result = analyze_vitals(csv.encode())
    spo2_findings = [f for f in result["findings"] if f.get("signal") == "spo2"]
    assert len(spo2_findings) > 0
    assert all(f["rule"] == "below_range" for f in spo2_findings)


def test_out_of_range_heart_rate_detected():
    csv = "timestamp,heart_rate\n2026-07-16T10:00:00Z,130\n2026-07-16T10:05:00Z,135\n"
    result = analyze_vitals(csv.encode())
    hr_findings = [f for f in result["findings"] if f.get("signal") == "heart_rate"]
    assert len(hr_findings) > 0


def test_trend_detection():
    # Queda forte: 98 → 82 em 5 pontos, slope normalizado ~0.04 → >0.05
    csv = (
        "timestamp,spo2\n"
        "2026-07-16T10:00:00Z,98\n"
        "2026-07-16T10:05:00Z,94\n"
        "2026-07-16T10:10:00Z,89\n"
        "2026-07-16T10:15:00Z,85\n"
        "2026-07-16T10:20:00Z,78\n"
    )
    result = analyze_vitals(csv.encode())
    trend_findings = [f for f in result["findings"] if f.get("rule") == "trend"]
    assert len(trend_findings) > 0


def test_zscore_detection():
    result = analyze_vitals(VALID_CSV.encode())
    # With normal vitals, z-score should not trigger much
    zscore_findings = [f for f in result["findings"] if f.get("rule") == "zscore"]
    assert len(zscore_findings) == 0


def test_zscore_detects_anomaly():
    csv_lines = ["timestamp,heart_rate"]
    for i in range(20):
        hr = 80 if i != 10 else 160
        csv_lines.append(f"2026-07-16T10:{i:02d}:00Z,{hr}")
    csv = "\n".join(csv_lines)
    result = analyze_vitals(csv.encode())
    zscore_findings = [f for f in result["findings"] if f.get("rule") == "zscore"]
    assert len(zscore_findings) > 0


def test_severity_normal_with_clean_data():
    result = analyze_vitals(VALID_CSV.encode())
    assert result["severity"] == "NORMAL"
    assert result["score"] == 0
