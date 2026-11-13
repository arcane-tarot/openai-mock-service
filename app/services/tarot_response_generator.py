import hashlib

from app.services.prompt_parser import TarotPrompt

OPENINGS = (
    (
        "{card} aparece como una invitación a mirar {meaning}. "
        "En el contexto de «{question}», la carta sugiere distinguir lo que ya "
        "es claro de aquello que todavía necesita tiempo y observación."
    ),
    (
        "La energía de {card} conecta esta consulta con {meaning}. "
        "Frente a «{question}», puede ayudarte a reconocer qué parte de la "
        "situación depende de tus decisiones presentes."
    ),
    (
        "{card} pone el foco en {meaning}. Al considerar «{question}», toma "
        "esta carta como una perspectiva para ordenar tus prioridades, no como "
        "una certeza absoluta sobre el futuro."
    ),
)

ACTIONS = (
    (
        "Como paso práctico, anota una acción pequeña que puedas realizar hoy y "
        "una señal concreta que te permita evaluar el resultado. Avanza con "
        "curiosidad y ajusta el rumbo según los hechos."
    ),
    (
        "Para llevar el mensaje a la práctica, separa lo que puedes controlar de "
        "lo que no. Elige un siguiente paso realista y revísalo con calma antes "
        "de tomar una decisión mayor."
    ),
    (
        "Date un momento para escribir qué necesitas, qué temes y qué evidencia "
        "tienes ahora. Esa comparación puede convertir la intuición de la carta "
        "en una decisión más consciente."
    ),
)


def generate_interpretation(prompt: TarotPrompt, seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    opening = OPENINGS[digest[0] % len(OPENINGS)].format(
        card=prompt.card_name,
        meaning=prompt.base_meaning.rstrip("."),
        question=prompt.question,
    )
    action = ACTIONS[digest[1] % len(ACTIONS)]
    return f"{opening}\n\n{action}"
