# core/signature.py
from __future__ import annotations

import re
from typing import List, Optional

from core.subtopics import pick_subtopic

_STOP = {
    "how", "what", "why", "does", "do", "is", "are", "to", "in", "on", "for", "with",
    "and", "or", "a", "the", "of", "my", "i", "can", "it", "this", "when", "then",
    "error", "issue", "problem", "help",
    "using", "use", "used", "trying", "try", "want", "need",
    "getting", "get", "gives", "give", "make", "made", "work", "working",
    "doesnt", "doesn", "dont", "didnt", "cant", "cannot",
    "python", "fastapi", "vscode", "pylance", "pytest", "asyncio",
}

_WORD_RX = re.compile(r"[a-z0-9]+|[а-я0-9]+", re.IGNORECASE)


def keyword_hint(text: str, tags: Optional[List[str]] = None) -> str:
    """
    Самое частое содержательное слово в начале текста.
    Если есть теги — добавляем их как доп. источник, чтобы не падать в "import".
    """
    t = (text or "").lower()
    words = [w.lower() for w in _WORD_RX.findall(t)]
    words = [w for w in words if len(w) >= 5 and w not in _STOP]

    # добавим теги как токены (они очень полезны в SE)
    for tg in (tags or []):
        tg = (tg or "").lower().replace("-", "")
        if tg and tg not in _STOP and len(tg) >= 5:
            words.append(tg)

    head = words[:80]
    if not head:
        return "misc"

    freq: dict[str, int] = {}
    for w in head:
        freq[w] = freq.get(w, 0) + 1

    return max(freq.items(), key=lambda kv: kv[1])[0]


def build_signature(
    domain: str,
    intent: str,
    output_type: str,
    problem_text: str,
    tags: Optional[List[str]] = None,
    query: Optional[str] = None,
) -> str:
    d = (domain or "general").lower()
    i = (intent or "understand").lower()
    o = (output_type or "summary").lower()

    sub = pick_subtopic(problem_text, tags=tags, query=query)
    kh = keyword_hint(problem_text, tags=tags)

    return f"{d}|{i}|{o}|{sub}|{kh}"
