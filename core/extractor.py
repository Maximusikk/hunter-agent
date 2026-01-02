from __future__ import annotations

import re
from core.models import Task


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_task(text: str) -> Task:
    """
    Rule-based extractor: raw text -> Task
    No ML/LLM. Simple heuristics only.
    """
    t = _norm(text)

    # Guess input type (still text, but sometimes user explicitly mentions screenshots/photos)
    input_type = "text"
    if any(k in t for k in ["screenshot", "screen shot", "скрин", "скриншот", "photo", "фото", "image", "картинк"]):
        input_type = "image"

    # Domain detection (very simple)
    domain = "general"
    if any(k in t for k in ["windows", "win11", "win 11", "win10", "pc", "laptop", "ноут", "компьютер"]):
        domain = "pc"
    if any(k in t for k in ["android", "андроид", "xiaomi", "samsung", "pixel", "oneplus"]):
        domain = "android"
    if any(k in t for k in ["iphone", "ios", "айфон", "ipad"]):
        domain = "ios"
    if any(k in t for k in ["whatsapp", "telegram", "discord", "chrome", "steam", "spotify", "youtube"]):
        domain = "apps"

    # Intent + output_type
    intent = "understand"
    output_type = "steps"

    if any(k in t for k in ["how to", "как", "help", "помогите", "fix", "починить", "исправить", "решить"]):
        intent = "fix"
        output_type = "steps"

    if any(k in t for k in ["why", "почему", "что за", "что значит", "meaning", "ошибка", "error", "код"]):
        intent = "diagnose"
        output_type = "diagnosis"

    if any(k in t for k in ["best", "which", "choose", "выбрать", "что лучше", "какой лучше", "recommend"]):
        intent = "choose"
        output_type = "recommendation"

    if any(k in t for k in ["recover", "restore", "вернуть", "восстановить", "deleted", "удалил"]):
        intent = "recover"
        output_type = "steps"

    if any(k in t for k in ["optimize", "ускорить", "lag", "лагает", "slow", "тормозит", "performance", "фпс"]):
        intent = "optimize"
        output_type = "steps"

    # Improve problem_statement with a clean sentence
    problem_statement = text.strip()
    if len(problem_statement) > 220:
        problem_statement = problem_statement[:217] + "..."

    return Task(
        intent=intent,
        input_type=input_type,
        output_type=output_type,
        domain=domain,
        problem_statement=problem_statement,
        evidence=[text.strip()],
    )
