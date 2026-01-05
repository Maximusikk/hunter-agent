from __future__ import annotations

import re
from core.models import Task
from core.signal_filter import has_decision_signal

WS_RE = re.compile(r"\s+")

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = WS_RE.sub(" ", s)
    return s

def _guess_input_type(t: str) -> str:
    if any(k in t for k in ("photo", "picture", "image", "screenshot", "camera", "scan")):
        return "image"
    # если вопрос явно “что на фото” даже без слова photo
    if any(k in t for k in ("what is this", "identify", "recognize", "does this look")):
        return "image"
    return "text"

def _guess_intent_output_domain(t: str) -> tuple[str, str, str]:
    # Food / calories
    if any(k in t for k in ("calories", "macro", "nutrition", "ingredients")):
        return ("estimate", "score", "health")

    # Style / outfit / haircut
    if any(k in t for k in ("outfit", "style", "hairstyle", "haircut", "how do i look")):
        return ("compare", "recommendation", "style")

    # Identify living thing
    if any(k in t for k in ("plant", "mushroom", "insect", "bug", "snake", "spider")):
        # часто хотят “что это и опасно ли”
        if any(k in t for k in ("dangerous", "poisonous", "safe")):
            return ("identify", "risk", "nature")
        return ("identify", "summary", "nature")

    # Scam / authenticity
    if any(k in t for k in ("scam", "fake", "legit", "authentic", "real or fake")):
        return ("verify", "verdict", "shopping")

    # General “which should I choose”
    if any(k in t for k in ("which one", "choose", "recommend", "better option")):
        return ("choose", "recommendation", "general")

    # fallback: decision but unclear
    return ("understand", "summary", "general")

def extract_task(text: str) -> Task:
    t = _norm(text)

    # даже если текст странный — создадим задачу, но domain/intent будут общими
    input_type = _guess_input_type(t)
    intent, output_type, domain = _guess_intent_output_domain(t)

    # если нет decision-сигнала, всё равно отдадим “general understand”,
    # но по проекту такие штуки должны отфильтроваться раньше signal_filter-ом
    if not has_decision_signal(t):
        intent, output_type, domain = ("understand", "summary", "general")

    return Task(
        intent=intent,
        input_type=input_type,
        output_type=output_type,
        domain=domain,
        problem_statement=text.strip(),
        evidence=[text.strip()],
    )
