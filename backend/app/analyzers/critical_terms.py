"""Termos críticos para análise de texto e áudio (lista transparente para demonstração).

Estes termos NÃO constituem protocolo médico validado. São heurísticas
demonstrativas usadas exclusivamente para o MVP acadêmico."""

# Pares (termo, severidade) — severidade: "ALERTA" | "ATENÇÃO"
CRITICAL_TERMS: list[tuple[str, str]] = [
    # Respiratórios
    ("falta de ar", "ALERTA"),
    ("dispneia", "ALERTA"),
    ("dificuldade para respirar", "ALERTA"),
    ("cianose", "ALERTA"),
    ("taquipneia", "ATENÇÃO"),
    ("saturação baixa", "ALERTA"),
    ("dessaturação", "ALERTA"),

    # Cardiovasculares
    ("dor no peito", "ALERTA"),
    ("dor torácica", "ALERTA"),
    ("palpitação", "ATENÇÃO"),
    ("taquicardia", "ATENÇÃO"),
    ("bradicardia", "ATENÇÃO"),
    ("hipotensão", "ATENÇÃO"),
    ("hipertensão severa", "ALERTA"),

    # Neurológicos
    ("confusão mental", "ALERTA"),
    ("sonolência excessiva", "ATENÇÃO"),
    ("perda de consciência", "ALERTA"),
    ("desmaio", "ALERTA"),
    ("convulsão", "ALERTA"),
    ("tontura intensa", "ATENÇÃO"),
    ("fraqueza súbita", "ALERTA"),
    ("dormência", "ATENÇÃO"),

    # Gerais
    ("cansaço extremo", "ATENÇÃO"),
    ("fadiga intensa", "ATENÇÃO"),
    ("febre alta", "ATENÇÃO"),
    ("dor intensa", "ATENÇÃO"),
    ("mal-estar generalizado", "ATENÇÃO"),
    ("piora significativa", "ATENÇÃO"),
    ("não responde", "ALERTA"),
    ("inconsciente", "ALERTA"),

    # Fala / áudio
    ("não consegue falar", "ALERTA"),
    ("fala arrastada", "ATENÇÃO"),
    ("voz trêmula", "ATENÇÃO"),
]

CRITICAL_TERMS_LOWER: dict[str, str] = {
    term.lower(): severity for term, severity in CRITICAL_TERMS
}
