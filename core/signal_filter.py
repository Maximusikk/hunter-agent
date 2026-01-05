from __future__ import annotations

import re

_STRICT = [
    r"\bi spend\b",
    r"\btoo much time\b",
    r"\btakes (me )?(hours|days|weeks)\b",
    r"\bworkflow\b",
    r"\bprocess\b",
    r"\bis there (a|any) (tool|app|way)\b",
    r"\bi wish there was\b",
    r"\bnot sure (if|whether)\b",
    r"\bfastest way\b",
    r"\bbest way\b",
    r"\bhow can i\b",
]

_SOFT = [
    r"\bnot working\b",
    r"\bdoesn'?t work\b",
    r"\bkeeps\b",
    r"\bdisconnect(ing|ed)?\b",
    r"\berror\b",
    r"\bissue\b",
    r"\bproblem\b",
    r"\bcrash\b",
    r"\bcan'?t\b",
    r"\bwon'?t\b",
]

STRICT_RX = [re.compile(p, re.IGNORECASE) for p in _STRICT]
SOFT_RX = [re.compile(p, re.IGNORECASE) for p in _SOFT]


def is_signal_strict(text: str, min_len: int = 140) -> bool:
    t = (text or "").strip()
    if len(t) < min_len:
        return False
    return any(rx.search(t) for rx in STRICT_RX)


def is_signal_soft(text: str, min_len: int = 25) -> bool:
    t = (text or "").strip()
    if len(t) < min_len:
        return False
    return any(rx.search(t) for rx in SOFT_RX)
