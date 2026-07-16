"""Analisador de áudio — Azure Speech to Text + métricas acústicas + termos (spec §9.2)."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from app.analyzers.critical_terms import CRITICAL_TERMS_LOWER
from app.state import AnalyzerResult

logger = logging.getLogger("nexovital.analyzers.audio")


def analyze_audio(
    audio_bytes: bytes | None,
    azure_speech_key: str = "",
    azure_speech_region: str = "",
    azure_language_key: str = "",
    azure_language_endpoint: str = "",
) -> AnalyzerResult:
    if not audio_bytes:
        return AnalyzerResult(
            status="missing",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=["Áudio não informado."],
        )

    limitations: list[str] = []
    findings: list[dict] = []
    score = 0

    # Salvar áudio temporário
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = Path(tmp.name)
        try:
            # Normalizar para WAV 16kHz mono com ffmpeg
            normalized = _normalize_audio(audio_bytes, wav_path)
        except Exception as exc:
            return AnalyzerResult(
                status="failed",
                severity="NORMAL",
                score=0,
                findings=[],
                evidence=[],
                limitations=[f"Falha ao processar áudio: {exc}"],
            )

    try:
        # 1. Azure Speech to Text
        transcription = ""
        if azure_speech_key and azure_speech_region:
            try:
                transcription = _transcribe_azure(normalized, azure_speech_key, azure_speech_region)
                findings.append({
                    "type": "transcription",
                    "detail": f"Transcrição obtida ({len(transcription)} caracteres).",
                    "excerpt": transcription[:500],
                })
            except Exception as exc:
                logger.warning("Azure Speech failed: %s", exc)
                limitations.append(f"Azure Speech to Text falhou: {exc}")
        else:
            limitations.append("Azure Speech to Text não configurado — transcrição indisponível.")

        # 2. Métricas acústicas
        acoustic = _acoustic_metrics(normalized)
        findings.append({
            "type": "acoustic",
            "duration_sec": acoustic["duration_sec"],
            "silence_ratio": acoustic["silence_ratio"],
            "pause_count": acoustic["pause_count"],
            "speech_rate": acoustic["speech_rate"],
            "detail": (
                f"Duração: {acoustic['duration_sec']:.1f}s, "
                f"Silêncio: {acoustic['silence_ratio']:.0%}, "
                f"Pausas: {acoustic['pause_count']}, "
                f"Ritmo: {acoustic['speech_rate']:.1f} sílabas/s"
            ),
        })

        # Heurísticas de fadiga/dificuldade
        if acoustic["duration_sec"] > 30 and acoustic["speech_rate"] < 2.0:
            findings.append({
                "type": "speech_anomaly",
                "detail": "Ritmo de fala reduzido — possível cansaço ou dificuldade respiratória.",
                "severity": "ATENÇÃO",
            })
            score += 15
        if acoustic["silence_ratio"] > 0.3:
            findings.append({
                "type": "speech_anomaly",
                "detail": "Alta proporção de silêncio — pausas frequentes.",
                "severity": "ATENÇÃO",
            })
            score += 10

        # 3. Termos críticos na transcrição
        if transcription:
            text_lower = transcription.lower()
            for term, sev in CRITICAL_TERMS_LOWER.items():
                if term in text_lower:
                    score += 20 if sev == "ALERTA" else 10
                    findings.append({
                        "type": "critical_term_audio",
                        "term": term,
                        "severity": sev,
                        "detail": f"Termo crítico na fala: '{term}'.",
                    })

        severity = "NORMAL"
        if score >= 40:
            severity = "ALERTA"
        elif score >= 20:
            severity = "ATENÇÃO"

        return AnalyzerResult(
            status="ok",
            severity=severity,
            score=min(100, score),
            findings=findings,
            evidence=[{
                "transcription": transcription,
                "acoustic": acoustic,
                "audio_size_bytes": len(audio_bytes),
            }],
            limitations=limitations,
        )
    finally:
        normalized.unlink(missing_ok=True)


def _normalize_audio(raw_bytes: bytes, output_path: Path) -> Path:
    """Converte áudio para WAV 16kHz mono com ffmpeg."""
    input_path = output_path.with_suffix(".input.tmp")
    input_path.write_bytes(raw_bytes)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(input_path),
                "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
                str(output_path),
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        input_path.unlink(missing_ok=True)
    return output_path


def _transcribe_azure(wav_path: Path, key: str, region: str) -> str:
    """Transcrição via Azure Speech to Text."""
    import azure.cognitiveservices.speech as speechsdk

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_recognition_language = "pt-BR"
    audio_config = speechsdk.audio.AudioConfig(filename=str(wav_path))
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )

    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "[Fala não reconhecida]"
    else:
        raise RuntimeError(f"Speech recognition failed: {result.reason}")


def _acoustic_metrics(wav_path: Path) -> dict:
    """Métricas acústicas simples usando ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(wav_path),
        ],
        capture_output=True, text=True, check=True,
    )
    duration = float(result.stdout.strip())

    # Detecta silêncio com ffmpeg silencedetect
    silence_result = subprocess.run(
        [
            "ffmpeg", "-i", str(wav_path),
            "-af", "silencedetect=noise=-30dB:d=0.5",
            "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )

    silence_duration = 0.0
    pause_count = 0
    for line in silence_result.stderr.splitlines():
        if "silence_duration:" in line:
            try:
                silence_duration += float(line.split("silence_duration:")[1].strip())
            except (ValueError, IndexError):
                pass
        if "silence_start:" in line:
            pause_count += 1

    silence_ratio = silence_duration / duration if duration > 0 else 0

    # Estimativa de ritmo de fala (sílabas/segundo) — aproximação grosseira
    # Contagem de energia (RMS) como proxy
    rms_result = subprocess.run(
        [
            "ffmpeg", "-i", str(wav_path),
            "-af", f"volumedetect", "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )
    mean_volume = -30.0
    for line in rms_result.stderr.splitlines():
        if "mean_volume:" in line:
            try:
                mean_volume = float(line.split("mean_volume:")[1].strip().split()[0])
            except (ValueError, IndexError):
                pass

    # Mapeamento heurístico: volume médio → estimativa de sílabas/s
    # Quanto mais alto o volume médio (menos negativo), mais "fala"
    speech_ratio = 1.0 - silence_ratio
    speech_rate = max(0.5, speech_ratio * 4.0 * (1.0 + (mean_volume + 30) / 60))

    return {
        "duration_sec": round(duration, 2),
        "silence_ratio": round(silence_ratio, 3),
        "pause_count": pause_count,
        "speech_rate": round(speech_rate, 1),
        "mean_volume_db": round(mean_volume, 1),
    }
