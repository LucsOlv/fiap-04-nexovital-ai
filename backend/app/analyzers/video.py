"""Analisador de vídeo — detecção de sinais de dor via YOLOv8 Pose (spec §9.1).

Indicadores observáveis de dor (baseado em literatura de análise de dor):
- Proteção/guarda: braço(s) junto ao tronco, cotovelo flexionado e colado ao corpo
- Contato mão-corpo: mão tocando cabeça, peito ou abdômen repetidamente
- Tensão corporal: redução do espaço entre ombros (ombros encolhidos)
- Imobilidade seletiva: segmento corporal com amplitude muito abaixo dos demais
- Expressão facial: inclinação da cabeça, sobrancelhas (via keypoints faciais)
- Agitação/desconforto: mudanças rápidas de posição (inquietação)
- Postura antálgica: tronco inclinado para um lado, protegendo região dolorosa
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import numpy as np

from app.state import AnalyzerResult

logger = logging.getLogger("nexovital.analyzers.video")

SAMPLE_RATE_FPS = 2.0

# Keypoints COCO usados para sinais de dor
# 0=nariz, 1-2=olhos, 3-4=orelhas, 5-6=ombros, 7-8=cotovelos, 9-10=punhos
# 11-12=quadris, 13-14=joelhos, 15-16=tornozelos
KP = {
    "nose": 0,
    "left_eye": 1,
    "right_eye": 2,
    "left_ear": 3,
    "right_ear": 4,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_knee": 13,
    "right_knee": 14,
    "left_ankle": 15,
    "right_ankle": 16,
}


def analyze_video(video_bytes: bytes | None) -> AnalyzerResult:
    if not video_bytes:
        return AnalyzerResult(
            status="missing",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=["Vídeo não informado."],
        )

    temp_dir = tempfile.mkdtemp(prefix="nexovital_video_")
    try:
        input_path = Path(temp_dir) / "input.mp4"
        input_path.write_bytes(video_bytes)

        normalized_path = Path(temp_dir) / "normalized.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_path), "-vf", "fps=2", str(normalized_path)],
            capture_output=True,
            check=True,
            timeout=60,
        )

        frames_data = _run_pose_estimation(normalized_path)
        return _analyze_pain(frames_data)
    except Exception as exc:
        logger.exception("Video analysis failed")
        return AnalyzerResult(
            status="failed",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=[f"Falha na análise de vídeo: {exc}"],
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _run_pose_estimation(video_path: Path) -> list[dict[str, Any]]:
    from ultralytics import YOLO  # type: ignore[attr-defined]

    model = YOLO("yolov8n-pose.pt")
    results = cast(Any, model(str(video_path), stream=True, verbose=False))

    frames_data: list[dict[str, Any]] = []
    for result in results:
        if result.keypoints is None or result.keypoints.xy is None:
            frames_data.append({"keypoints": None, "has_person": False})
            continue
        keypoints = result.keypoints.xy.cpu().numpy()
        conf = result.keypoints.conf
        conf_np = conf.cpu().numpy() if conf is not None else None
        if conf_np is not None and len(keypoints) > 1:
            best_idx = int(conf_np.mean(axis=1).argmax())
            kp = keypoints[best_idx]
        elif len(keypoints) > 0:
            kp = keypoints[0]
        else:
            frames_data.append({"keypoints": None, "has_person": False})
            continue
        box = (
            result.boxes.xyxy[0].tolist()
            if result.boxes is not None and len(result.boxes) > 0
            else None
        )
        frames_data.append(
            {
                "frame_index": len(frames_data),
                "keypoints": kp.tolist() if isinstance(kp, np.ndarray) else kp,
                "has_person": True,
                "box": box,
            }
        )
    return frames_data


def _analyze_pain(frames_data: list[dict[str, Any]]) -> AnalyzerResult:
    findings: list[dict[str, Any]] = []
    limitations: list[str] = []
    score = 0
    frame_count = len(frames_data)
    person_frames = [f for f in frames_data if f.get("has_person")]

    if not person_frames:
        return AnalyzerResult(
            status="ok",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=["Nenhuma pessoa detectada."],
        )

    presence_ratio = len(person_frames) / frame_count if frame_count > 0 else 0

    # ── Extrair features de dor por frame ──
    guarding_indices: list[int] = []
    hand_to_body_indices: list[int] = []
    shoulder_tension: list[float] = []
    head_tilt_angles: list[float] = []
    body_tilt_angles: list[float] = []
    elbow_angles: list[float] = []

    def _time_range(indices: list[int]) -> str:
        """Converte frame indices para intervalo de tempo (SAMPLE_RATE_FPS = 2 fps)."""
        if not indices:
            return "N/A"
        start = indices[0] / SAMPLE_RATE_FPS
        end = indices[-1] / SAMPLE_RATE_FPS
        if start == end:
            return f"{start:.1f}s"
        return f"{start:.1f}s–{end:.1f}s"

    for frame in person_frames:
        kp = frame.get("keypoints")
        frame_idx = frame.get("frame_index", 0)
        if kp is None:
            continue

        # ── Guarda protetora: cotovelo muito próximo do quadril ──
        le = _pt(kp, KP["left_elbow"])
        lh = _pt(kp, KP["left_hip"])
        re = _pt(kp, KP["right_elbow"])
        rh = _pt(kp, KP["right_hip"])
        ls = _pt(kp, KP["left_shoulder"])

        guarded = False
        if le is not None and lh is not None and ls is not None:
            shoulder_hip = np.linalg.norm(ls - lh)
            elbow_hip = np.linalg.norm(le - lh)
            if shoulder_hip > 0 and (elbow_hip / shoulder_hip) < 0.6:
                guarded = True
        if re is not None and rh is not None:
            rs = _pt(kp, KP["right_shoulder"])
            if rs is not None:
                shoulder_hip_r = np.linalg.norm(rs - rh)
                elbow_hip_r = np.linalg.norm(re - rh)
                if shoulder_hip_r > 0 and (elbow_hip_r / shoulder_hip_r) < 0.6:
                    guarded = True
        if guarded:
            guarding_indices.append(frame_idx)

        # ── Contato mão-corpo: punho próximo da cabeça ou do peito ──
        lw = _pt(kp, KP["left_wrist"])
        rw = _pt(kp, KP["right_wrist"])
        nose = _pt(kp, KP["nose"])
        if nose is not None:
            if ls is not None:
                chest = (
                    (ls + _pt(kp, KP["right_shoulder"])) / 2
                    if _pt(kp, KP["right_shoulder"]) is not None
                    else ls
                )
                for wrist in [lw, rw]:
                    if wrist is not None:
                        dist_to_head = float(np.linalg.norm(wrist - nose))
                        dist_to_chest = float(np.linalg.norm(wrist - chest))
                        box_h = frame.get("box")
                        height_px = (box_h[3] - box_h[1]) if box_h else 200
                        if dist_to_head < height_px * 0.25 or dist_to_chest < height_px * 0.20:
                            hand_to_body_indices.append(frame_idx)
                            break

        # ── Tensão nos ombros: distância entre eles ──
        rs_pt = _pt(kp, KP["right_shoulder"])
        if ls is not None and rs_pt is not None:
            shoulder_dist = float(np.linalg.norm(ls - rs_pt))
            shoulder_tension.append(shoulder_dist)

        # ── Inclinação da cabeça ──
        leye = _pt(kp, KP["left_eye"])
        reye = _pt(kp, KP["right_eye"])
        _pt(kp, KP["left_ear"])
        _pt(kp, KP["right_ear"])
        if leye is not None and reye is not None:
            dx = float(reye[0] - leye[0])
            dy = float(reye[1] - leye[1])
            angle = abs(float(np.degrees(np.arctan2(dy, dx))))
            head_tilt_angles.append(angle)

        # ── Inclinação antálgica do tronco ──
        if ls is not None and rs_pt is not None and lh is not None:
            mid_shoulder = (ls + rs_pt) / 2
            rh_pt = _pt(kp, KP["right_hip"])
            if rh_pt is not None:
                mid_hip = (lh + rh_pt) / 2
                dx_torso = float(mid_shoulder[0] - mid_hip[0])
                dy_torso = float(mid_shoulder[1] - mid_hip[1])
                tilt = abs(float(np.degrees(np.arctan2(dx_torso, abs(dy_torso)))))
                body_tilt_angles.append(tilt)

        # ── Flexão do cotovelo (cotovelo dobrado = tensão/guarda) ──
        for s, e, w in [
            (KP["left_shoulder"], KP["left_elbow"], KP["left_wrist"]),
            (KP["right_shoulder"], KP["right_elbow"], KP["right_wrist"]),
        ]:
            sp = _pt(kp, s)
            ep = _pt(kp, e)
            wp = _pt(kp, w)
            if sp is not None and ep is not None and wp is not None:
                a = sp - ep
                b = wp - ep
                na = np.linalg.norm(a)
                nb = np.linalg.norm(b)
                if na > 0 and nb > 0:
                    cos_a = np.clip(float(np.dot(a, b) / (na * nb)), -1.0, 1.0)
                    elbow_angles.append(float(np.degrees(np.arccos(cos_a))))

    # ── Avaliar indicadores de dor ──
    person_count = len(person_frames)

    # 1. Guarda protetora
    guard_ratio = len(guarding_indices) / person_count if person_count else 0
    if guard_ratio > 0.4:
        findings.append(
            {
                "type": "guarding",
                "detail": f"Postura de proteção em {guard_ratio:.0%} do vídeo — braço(s) junto ao corpo, sugestivo de dor torácica ou abdominal.",
                "severity": "ALERTA",
                "frame_indices": guarding_indices,
                "time_range_seconds": _time_range(guarding_indices),
                "affected_frames": len(guarding_indices),
            }
        )
        score += 35
    elif guard_ratio > 0.2:
        findings.append(
            {
                "type": "guarding_light",
                "detail": f"Proteção corporal detectada em {guard_ratio:.0%} do vídeo — possível desconforto.",
                "severity": "ATENÇÃO",
                "frame_indices": guarding_indices,
                "time_range_seconds": _time_range(guarding_indices),
                "affected_frames": len(guarding_indices),
            }
        )
        score += 20

    # 2. Contato mão-corpo (autopalpação por dor)
    hand_ratio = len(hand_to_body_indices) / person_count if person_count else 0
    if hand_ratio > 0.3:
        findings.append(
            {
                "type": "hand_to_body",
                "detail": f"Mão na cabeça ou peito em {hand_ratio:.0%} do vídeo — gesto comum em desconforto, cefaleia ou ansiedade.",
                "severity": "ATENÇÃO",
                "frame_indices": hand_to_body_indices,
                "time_range_seconds": _time_range(hand_to_body_indices),
                "affected_frames": len(hand_to_body_indices),
            }
        )
        score += 20

    # 3. Tensão nos ombros (ombros encolhidos = estresse/dor)
    if len(shoulder_tension) >= 3:
        shoulder_mean = float(np.mean(shoulder_tension))
        heights = []
        for f in person_frames:
            b = f.get("box")
            if b:
                heights.append(b[3] - b[1])
        avg_h = float(np.mean(heights)) if heights else 200
        shoulder_ratio = shoulder_mean / avg_h
        if shoulder_ratio < 0.35:
            findings.append(
                {
                    "type": "shoulder_tension",
                    "detail": "Ombros contraídos/encolhidos — sinal de tensão muscular ou estresse.",
                    "severity": "ATENÇÃO",
                    "frame_indices": [f.get("frame_index", 0) for f in person_frames],
                    "time_range_seconds": _time_range([f.get("frame_index", 0) for f in person_frames]),
                    "affected_frames": len(shoulder_tension),
                }
            )
            score += 15

    # 4. Inclinação da cabeça (cabeça baixa = sofrimento)
    if len(head_tilt_angles) >= 3:
        mean_tilt = float(np.mean(head_tilt_angles))
        if 10 < mean_tilt < 80:
            findings.append(
                {
                    "type": "head_tilt",
                    "detail": f"Inclinação lateral da cabeça detectada ({mean_tilt:.0f}°) — pode indicar desconforto cervical ou fadiga.",
                    "severity": "ATENÇÃO",
                    "frame_indices": [f.get("frame_index", 0) for f in person_frames],
                    "time_range_seconds": _time_range([f.get("frame_index", 0) for f in person_frames]),
                    "affected_frames": len(head_tilt_angles),
                }
            )
            score += 15
        if len(head_tilt_angles) >= 5:
            tilt_var = float(np.std(head_tilt_angles))
            if tilt_var > 8:
                findings.append(
                    {
                        "type": "head_restlessness",
                        "detail": "Movimentação repetitiva da cabeça — sinal de inquietação ou desconforto.",
                        "severity": "ATENÇÃO",
                        "frame_indices": [f.get("frame_index", 0) for f in person_frames],
                        "time_range_seconds": _time_range([f.get("frame_index", 0) for f in person_frames]),
                        "affected_frames": len(head_tilt_angles),
                    }
                )
                score += 10

    # 5. Postura antálgica (tronco inclinado protegendo um lado)
    if len(body_tilt_angles) >= 3:
        mean_body_tilt = float(np.mean(body_tilt_angles))
        if mean_body_tilt > 10:
            findings.append(
                {
                    "type": "antalgic_posture",
                    "detail": f"Inclinação lateral do tronco ({mean_body_tilt:.0f}°) — postura antálgica, protegendo região dolorosa.",
                    "severity": "ALERTA",
                    "frame_indices": [f.get("frame_index", 0) for f in person_frames],
                    "time_range_seconds": _time_range([f.get("frame_index", 0) for f in person_frames]),
                    "affected_frames": len(body_tilt_angles),
                }
            )
            score += 30
        elif mean_body_tilt > 6:
            findings.append(
                {
                    "type": "mild_antalgic",
                    "detail": f"Leve inclinação do tronco ({mean_body_tilt:.0f}°) — possível compensação postural.",
                    "severity": "ATENÇÃO",
                    "frame_indices": [f.get("frame_index", 0) for f in person_frames],
                    "time_range_seconds": _time_range([f.get("frame_index", 0) for f in person_frames]),
                    "affected_frames": len(body_tilt_angles),
                }
            )
            score += 10

    # 6. Cotovelos fletidos (braço dobrado = tensão, não relaxado)
    if len(elbow_angles) >= 3:
        mean_elbow = float(np.mean(elbow_angles))
        if mean_elbow < 100:
            findings.append(
                {
                    "type": "elbow_flexion",
                    "detail": f"Braços mantidos flexionados ({mean_elbow:.0f}° em média) — indicativo de tensão muscular ou proteção.",
                    "severity": "ATENÇÃO",
                    "frame_indices": [f.get("frame_index", 0) for f in person_frames],
                    "time_range_seconds": _time_range([f.get("frame_index", 0) for f in person_frames]),
                    "affected_frames": len(elbow_angles),
                }
            )
            score += 15

    # 7. Agitação (mãos se movendo muito = inquietação por dor)
    if len(person_frames) >= 4:
        wrist_positions: list[np.ndarray] = []
        wrist_frame_indices: list[int] = []
        for frame in person_frames:
            kp = frame.get("keypoints")
            if kp is None:
                continue
            lw = _pt(kp, KP["left_wrist"])
            if lw is not None:
                wrist_positions.append(lw)
                wrist_frame_indices.append(frame.get("frame_index", 0))
        if len(wrist_positions) >= 3:
            diffs = [
                float(np.linalg.norm(wrist_positions[i] - wrist_positions[i - 1]))
                for i in range(1, len(wrist_positions))
            ]
            mean_move = float(np.mean(diffs))
            heights_list = []
            for f in person_frames:
                b = f.get("box")
                if b:
                    heights_list.append(b[3] - b[1])
            avg_h = float(np.mean(heights_list)) if heights_list else 200
            if mean_move > avg_h * 0.15:
                findings.append(
                    {
                        "type": "restlessness",
                        "detail": "Agitação/ inquietação dos braços detectada — comum em quadros de dor aguda ou desconforto intenso.",
                        "severity": "ATENÇÃO",
                        "frame_indices": wrist_frame_indices,
                        "time_range_seconds": _time_range(wrist_frame_indices),
                        "affected_frames": len(wrist_positions),
                    }
                )
                score += 20
            elif mean_move < avg_h * 0.02 and len(person_frames) >= 6:
                findings.append(
                    {
                        "type": "immobility",
                        "detail": "Imobilidade incomum dos braços — pessoa pode estar contida pela dor, evitando se movimentar.",
                        "severity": "ATENÇÃO",
                        "frame_indices": wrist_frame_indices,
                        "time_range_seconds": _time_range(wrist_frame_indices),
                        "affected_frames": len(person_frames),
                    }
                )
                score += 15

    # 8. Presença reduzida (evitação — pessoa sai do quadro)
    if presence_ratio < 0.5:
        absent_indices = [f.get("frame_index", 0) for f in frames_data if not f.get("has_person")]
        findings.append(
            {
                "type": "low_presence",
                "detail": f"Pessoa visível em apenas {presence_ratio:.0%} do vídeo — possível evitação ou dificuldade de permanência.",
                "severity": "ATENÇÃO",
                "frame_indices": absent_indices,
                "time_range_seconds": _time_range(absent_indices),
                "affected_frames": len(absent_indices),
            }
        )
        score += 10

    if not findings:
        findings.append(
            {
                "type": "no_pain_signs",
                "detail": "Nenhum sinal evidente de dor detectado no vídeo.",
                "frame_indices": [],
                "time_range_seconds": "N/A",
                "affected_frames": 0,
            }
        )

    severity = "NORMAL"
    if score >= 50:
        severity = "ALERTA"
    elif score >= 25:
        severity = "ATENÇÃO"

    return AnalyzerResult(
        status="ok",
        severity=severity,
        score=min(100, score),
        findings=findings,
        evidence=[
            {
                "total_frames": frame_count,
                "person_frames": len(person_frames),
                "presence_ratio": round(presence_ratio, 2),
                "guarding_ratio": round(len(guarding_indices) / max(len(person_frames), 1), 2),
                "hand_to_body_ratio": round(len(hand_to_body_indices) / max(len(person_frames), 1), 2),
                "sample_rate_fps": SAMPLE_RATE_FPS,
                "total_duration_seconds": round(frame_count / SAMPLE_RATE_FPS, 1),
            }
        ],
        limitations=limitations,
    )


def _pt(kp: list[list[float]], idx: int) -> np.ndarray | None:
    if idx >= len(kp):
        return None
    p = kp[idx]
    if len(p) < 2:
        return None
    if p[0] == 0 and p[1] == 0:
        return None
    return np.array([p[0], p[1]])
