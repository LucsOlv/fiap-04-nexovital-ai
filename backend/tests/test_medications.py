"""Testes do analisador de medicamentos."""

from app.analyzers.medications import analyze_medications


def test_no_current_medications():
    result = analyze_medications(None, None)
    assert result["status"] == "missing"
    assert result["findings"] == []


def test_no_baseline():
    current = [{"name": "Dipirona", "dose": "500mg", "frequency": "6/6h"}]
    result = analyze_medications(current, None)
    assert result["status"] == "ok"
    assert result["findings"][0]["type"] == "no_baseline"
    assert result["score"] == 0


def test_no_history_empty_list():
    current = [{"name": "Dipirona", "dose": "500mg", "frequency": "6/6h"}]
    result = analyze_medications(current, [])
    # Lista vazia significa baseline existe mas sem medicamentos — é adição
    added = [f for f in result["findings"] if f["type"] == "added"]
    assert len(added) == 1



def test_no_history_flag_false_skips_comparison():
    """has_history=False → sem baseline, mesmo com lista vazia no previous."""
    current = [{"name": "Dipirona", "dose": "500mg", "frequency": "6/6h"}]
    result = analyze_medications(current, [], has_history=False)
    assert result["status"] == "ok"
    assert result["findings"][0]["type"] == "no_baseline"
    assert result["score"] == 0
    assert "sem baseline histórica" in result["limitations"][0].lower()

def test_unchanged_medications():
    meds = [{"name": "A", "dose": "10mg", "frequency": "12/12h"}]
    result = analyze_medications(meds, meds)
    assert result["findings"][0]["type"] == "no_changes"


def test_added_medication():
    current = [{"name": "A", "dose": "10mg", "frequency": "8/8h"}]
    previous = []
    result = analyze_medications(current, previous)
    added = [f for f in result["findings"] if f["type"] == "added"]
    assert len(added) == 1


def test_removed_medication():
    current = []
    previous = [{"name": "A", "dose": "10mg", "frequency": "8/8h"}]
    result = analyze_medications(current, previous)
    removed = [f for f in result["findings"] if f["type"] == "removed"]
    assert len(removed) == 1


def test_dose_change_detected():
    current = [{"name": "A", "dose": "20mg", "frequency": "8/8h"}]
    previous = [{"name": "A", "dose": "10mg", "frequency": "8/8h"}]
    result = analyze_medications(current, previous)
    modified = [f for f in result["findings"] if f["type"] == "modified"]
    assert len(modified) == 1


def test_frequency_change_detected():
    current = [{"name": "A", "dose": "10mg", "frequency": "12/12h"}]
    previous = [{"name": "A", "dose": "10mg", "frequency": "8/8h"}]
    result = analyze_medications(current, previous)
    modified = [f for f in result["findings"] if f["type"] == "modified"]
    assert len(modified) == 1


def test_multiple_changes_increase_score():
    current = [
        {"name": "A", "dose": "20mg", "frequency": "8/8h"},
        {"name": "C", "dose": "5mg", "frequency": "24/24h"},
    ]
    previous = [
        {"name": "A", "dose": "10mg", "frequency": "8/8h"},
        {"name": "B", "dose": "5mg", "frequency": "12/12h"},
    ]
    result = analyze_medications(current, previous)
    assert result["score"] >= 30
    changed_types = {f["type"] for f in result["findings"]}
    assert "added" in changed_types
    assert "removed" in changed_types
    assert "modified" in changed_types
