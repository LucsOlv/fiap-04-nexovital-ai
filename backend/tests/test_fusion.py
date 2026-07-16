"""Testes da fusão determinística."""

from app.analyzers.fusion import fuse_evidence


def _ok(severity="NORMAL", score=0):
    return {"status": "ok", "severity": severity, "score": score, "findings": [], "evidence": [], "limitations": []}


def _missing():
    return {"status": "missing", "severity": "NORMAL", "score": 0, "findings": [], "evidence": [], "limitations": []}


def test_all_missing():
    score, level, corr, limits = fuse_evidence(None, None, None, None, None)
    assert score == 0
    assert level == "NORMAL"


def test_single_normal():
    score, level, corr, limits = fuse_evidence(
        video=_ok("NORMAL", 5), audio=None, text=None, vitals=None, medications=None,
    )
    assert level == "NORMAL"
    assert score <= 20


def test_alert_in_vitals_elevates():
    score, level, corr, limits = fuse_evidence(
        video=_ok("NORMAL", 10),
        audio=None,
        text=None,
        vitals=_ok("ALERTA", 60),
        medications=None,
    )
    assert level in ("ATENÇÃO", "ALERTA")
    assert score >= 60


def test_convergent_evidence():
    score, level, corr, limits = fuse_evidence(
        video=_ok("ALERTA", 50),
        audio=_ok("ALERTA", 40),
        text=None,
        vitals=_ok("ALERTA", 60),
        medications=None,
    )
    assert level == "ALERTA"
    assert score >= 70
    assert any(c["type"] == "convergent" for c in corr)


def test_no_history_reduces_confidence():
    score, level, corr, limits = fuse_evidence(
        video=_ok("ALERTA", 50), audio=None, text=None, vitals=None, medications=None,
        has_history=False,
    )
    assert any("histórico" in lim.lower() for lim in limits)


def test_missing_modality_logged():
    _, _, _, limits = fuse_evidence(
        video=None, audio=None, text=None, vitals=None, medications=None,
    )
    assert len(limits) > 0


def test_failed_modality_logged():
    failed = {"status": "failed", "severity": "NORMAL", "score": 0, "findings": [], "evidence": [], "limitations": ["erro de teste"]}
    _, _, _, limits = fuse_evidence(
        video=failed, audio=None, text=None, vitals=None, medications=None,
    )
    assert any("falhou" in lim.lower() for lim in limits)
