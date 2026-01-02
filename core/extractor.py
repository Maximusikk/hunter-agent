from __future__ import annotations

import re
from core.models import Task


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_task(text: str) -> Task:
    t = _norm(text)

    input_type = "text"
    if any(k in t for k in ["screenshot", "screen shot", "скрин", "скриншот", "photo", "фото", "image", "картинк"]):
        input_type = "image"

    domain = "general"
    if any(k in t for k in ["windows", "win11", "win 11", "win10", "pc", "laptop", "ноут", "компьютер"]):
        domain = "pc"
    if any(k in t for k in ["android", "андроид", "xiaomi", "samsung", "pixel", "oneplus"]):
        domain = "android"
    if any(k in t for k in ["iphone", "ios", "айфон", "ipad"]):
        domain = "ios"
    if any(k in t for k in ["whatsapp", "telegram", "discord", "chrome", "steam", "spotify", "youtube"]):
        domain = "apps"

    # defaults
    intent = "understand"
    output_type = "summary"

    # diagnose signals
    if any(k in t for k in ["error", "ошибка", "код", "0x", "crash", "вылетает", "stuck", "failed", "не запускается"]):
        intent = "diagnose"
        output_type = "diagnosis"

    # fix signals (complaint style)
    if any(
        k in t
        for k in [
            "not working", "doesn't work", "doesnt work", "не работает",
            "keeps", "постоянно", "отваливается", "disconnect", "disconnecting", "drops", "падает",
            "cant", "can't", "cannot", "не могу",
        ]
    ):
        intent = "fix"
        output_type = "steps"

    # explicit help/how-to
    if any(k in t for k in ["how to", "как", "fix", "починить", "исправить", "решить", "help", "помогите"]):
        intent = "fix"
        output_type = "steps"

    # choose/recommend
    if any(k in t for k in ["best", "which", "choose", "выбрать", "что лучше", "какой лучше", "recommend"]):
        intent = "choose"
        output_type = "recommendation"

    # recover
    if any(k in t for k in ["recover", "restore", "вернуть", "восстановить", "deleted", "удалил"]):
        intent = "recover"
        output_type = "steps"

    # optimize
    if any(k in t for k in ["optimize", "ускорить", "lag", "лагает", "slow", "тормозит", "performance", "фпс"]):
        intent = "optimize"
        output_type = "steps"

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
