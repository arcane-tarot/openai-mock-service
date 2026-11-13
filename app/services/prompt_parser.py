from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TarotPrompt:
    question: str = "la situación consultada"
    deck_type: str = "desconocido"
    card_name: str = "La carta elegida"
    card_type: str = "carta de tarot"
    base_meaning: str = "una invitación a observar la situación con atención"


FIELD_NAMES = {
    "Pregunta": "question",
    "Tipo de mazo seleccionado": "deck_type",
    "Carta": "card_name",
    "Tipo de carta": "card_type",
    "Significado base": "base_meaning",
}


def normalize_input(value: str | list[dict[str, Any]]) -> str:
    if isinstance(value, str):
        return value.strip()

    chunks: list[str] = []
    for item in value:
        content = item.get("content", "")
        if isinstance(content, str):
            chunks.append(content)
            continue
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
    return "\n".join(chunks).strip()


def parse_tarot_prompt(prompt: str) -> TarotPrompt:
    values: dict[str, str] = {}
    for line in prompt.splitlines():
        label, separator, value = line.partition(":")
        field_name = FIELD_NAMES.get(label.strip())
        if separator and field_name and value.strip():
            values[field_name] = value.strip()

    return TarotPrompt(**values)
