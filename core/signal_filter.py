from __future__ import annotations

import re

# Сигналы "объемной работы" и "неопределенности"
PATTERNS = [
    r"\bi spend\b",
    r"\btakes (me )?(hours|days|weeks)\b",
    r"\btoo much time\b",
    r"\btime consuming\b",
    r"\bworkflow\b",
    r"\bprocess\b",
    r"\bhow do (people|you) (usually|typically)\b",
    r"\bis there (a|any) (tool|app|way)\b",
    r"\bi wish there was\b",
    r"\bwhat happens if\b",
    r"\bnot sure (if|whether)\b",
    r"\bhow can i\b",
    r"\bwhat's the best (way|approach)\b",
]

RU_PATTERNS = [
    r"\bя трачу\b",
    r"\bзанимает\b",
    r"\bслишком долго\b",
    r"\bмного времени\b",
    r"\bкак обычно\b",
    r"\bесть ли (способ|инструмент|приложение)\b",
    r"\bхочу (узнать|понять)\b",
    r"\bне уверен(а)?\b",
    r"\bчто будет если\b",
    r"\bкак мне\b",
    r"\bкакой (лучший|оптимальный) способ\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in PATTERNS + RU_PATTERNS]


def is_signal(text: str, min_len: int = 80) -> bool:
    """
    Пропускаем только тексты, похожие на:
      - объемную работу
      - неопределенность/выбор/подготовку
    """
    if not text:
        return False

    t = text.strip()
    if len(t) < min_len:
        return False

    # должен быть вопрос или явная формулировка задачи
    has_question = "?" in t or any(w in t.lower() for w in ["how ", "what ", "why ", "как ", "почему ", "что "])
    if not has_question:
        return False

    return any(rx.search(t) for rx in _COMPILED)
