from __future__ import annotations

import re

_RULES: list[tuple[str, list[str]]] = [
    # work / meetings
    ("meeting_notes_summary", [
        r"\bmeeting(s)?\b",
        r"\btranscript(s)?\b",
        r"\bminutes\b",
        r"\baction items?\b",
        r"\bnotes?\b",
        r"\bsummariz(e|ing|ation)\b",
    ]),
    # generic summarization
    ("summarize_long_text", [
        r"\bsummariz(e|ing|ation)\b",
        r"\blong\b",
        r"\btoo much time\b",
        r"\bfastest way\b",
        r"\btakes forever\b",
    ]),
    # fallback
]

_COMPILED: list[tuple[str, list[re.Pattern]]] = [
    (name, [re.compile(p, re.IGNORECASE) for p in pats])
    for name, pats in _RULES
]


def classify_topic(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "unknown"

    for name, regs in _COMPILED:
        hits = sum(1 for rx in regs if rx.search(t))
        # порог: хотя бы 2 совпадения, чтобы не схватывать лишнее
        if hits >= 2:
            return name

    return "misc"
