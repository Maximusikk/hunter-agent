from __future__ import annotations

import re

# Простые rules. Дальше расширишь словарём по доменам.
_RULES: list[tuple[str, list[str]]] = [
    ("meeting_notes_summary", [
        r"\bmeeting(s)?\b",
        r"\btranscript(s)?\b",
        r"\bminutes\b",
        r"\baction items?\b",
        r"\bnotes?\b",
        r"\bsummariz(e|ing|ation)\b",
        r"\bscattered\b",
        r"\bdocs?\b",
        r"\bchats?\b",
        r"\bworkflow\b",
    ]),
    ("resume_review", [
        r"\bresume\b",
        r"\bcv\b",
        r"\bcover letter\b",
        r"\bjob\b",
        r"\binterview\b",
    ]),
    ("shopping_compare", [
        r"\bwhich\b",
        r"\bbetter\b",
        r"\bcompare\b",
        r"\bchoose\b",
        r"\bbuy\b",
        r"\blaptop\b",
        r"\bphone\b",
    ]),
]

_COMPILED: list[tuple[str, list[re.Pattern[str]]]] = [
    (name, [re.compile(p, re.IGNORECASE) for p in pats])
    for name, pats in _RULES
]


def classify_topic(text: str) -> str:
    """
    Возвращает устойчивый topic для кластеров.
    Без ML: только правила + порог совпадений.
    """
    t = (text or "").strip()
    if not t:
        return "unknown"

    best_name = "misc"
    best_hits = 0

    for name, regs in _COMPILED:
        hits = sum(1 for rx in regs if rx.search(t))
        if hits > best_hits:
            best_hits = hits
            best_name = name

    # Порог: если совпадений слишком мало — не считаем это уверенным топиком
    if best_hits >= 2:
        return best_name

    return "misc"
