"""Testes da fusão determinística."""

from app.analyzers.fusion import fuse_evidence


def _ok(severity="NORMAL", score=0):
    return {
        "status": "ok",
        "severity": severity,
        "score": score,
        "findings": [],
        "evidence": [],
        "limitations": [],
    }


def _missing():
    return {
        "status": "missing",
        "severity": "NORMAL",
        "score": 0,
        "findings": [],
        "evidence": [],
        "limitations": [],
    }


def test_all_missing():
    score, level, corr, limits = fuse_evidence(None, None, None, None, None)
    assert score == 0
    assert level == "NORMAL"


def test_single_normal():
    score, level, corr, limits = fuse_evidence(
        video=_ok("NORMAL", 5),
        audio=None,
        text=None,
        vitals=None,
        medications=None,
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
    assert score >= 50


def test_convergent_evidence():
    score, level, corr, limits = fuse_evidence(
        video=_ok("ALERTA", 80),
        audio=_ok("ALERTA", 75),
        text=None,
        vitals=_ok("ALERTA", 85),
        medications=None,
    )
    assert level == "ALERTA"
    assert score >= 70
    assert any(c["type"] == "convergent" for c in corr)


def test_weighted_average_keeps_zero_to_one_hundred_scale():
    score, level, _, _ = fuse_evidence(
        video=_ok("ATENÇÃO", 30),
        audio=_ok("ATENÇÃO", 30),
        text=None,
        vitals=None,
        medications=None,
    )
    assert score == 30
    assert level == "ATENÇÃO"


def test_low_scores_do_not_saturate():
    score, level, _, _ = fuse_evidence(
        video=_ok("NORMAL", 5),
        audio=_ok("NORMAL", 10),
        text=_ok("NORMAL", 15),
        vitals=None,
        medications=None,
    )
    assert score < 20
    assert level == "NORMAL"


def test_no_history_reduces_confidence():
    score, level, corr, limits = fuse_evidence(
        video=_ok("ALERTA", 50),
        audio=None,
        text=None,
        vitals=None,
        medications=None,
        has_history=False,
    )
    assert any("histórico" in lim.lower() for lim in limits)


def test_missing_modality_logged():
    _, _, _, limits = fuse_evidence(
        video=None,
        audio=None,
        text=None,
        vitals=None,
        medications=None,
    )
    assert len(limits) > 0


def test_failed_modality_logged():
    failed = {
        "status": "failed",
        "severity": "NORMAL",
        "score": 0,
        "findings": [],
        "evidence": [],
        "limitations": ["erro de teste"],
    }
    _, _, _, limits = fuse_evidence(
        video=failed,
        audio=None,
        text=None,
        vitals=None,
        medications=None,
    )
    assert any("falhou" in lim.lower() for lim in limits)
