from __future__ import annotations

import re
from core.models import Task

STOP = {
    "i", "im", "i'm", "me", "my", "we", "you", "they", "it",
    "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with",
    "this", "that", "these", "those",
    "please", "help",
    # мусор SE/тех. форумов
    "using", "import", "code", "error", "issue", "problem",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")

def _topic_bucket(text: str) -> str:
    t = (text or "").lower()

    if any(k in t for k in ("calories", "nutrition", "macro", "ingredients")):
        return "calories_from_photo"
    if any(k in t for k in ("outfit", "style", "hairstyle", "haircut", "how do i look")):
        return "style_from_photo"
    if any(k in t for k in ("plant", "mushroom", "insect", "bug", "snake", "spider")):
        return "identify_living_thing"
    if any(k in t for k in ("scam", "fake", "legit", "authentic", "real or fake")):
        return "verify_authenticity"
    if any(k in t for k in ("which one", "choose", "recommend", "better option")):
        return "choose_between_options"

    return "misc_decision"

def make_signature(task: Task) -> str:
    topic = _topic_bucket(task.problem_statement)
    # Кластер строим по “структуре задачи”, а не по текстовому шуму
    return f"{task.domain}|{task.intent}|{task.output_type}|{topic}"
