from __future__ import annotations

import re


_SUPPORT = [
    r"\bnot working\b",
    r"\bdoesn'?t work\b",
    r"\berror\b",
    r"\bissue\b",
    r"\bproblem\b",
    r"\bcrash\b",
    r"\bfails?\b",
    r"\btimeout\b",
]

_WORKFLOW = [
    r"\btoo much time\b",
    r"\btakes forever\b",
    r"\bmany times\b",
    r"\b20-30\b",
    r"\bevery day\b",
    r"\bworkflow\b",
    r"\btransfer\b.*\bfiles?\b",
    r"\brewrite\b.*\bnotes\b",
    r"\bsummarize\b.*\btranscript\b",
]

_DECISION = [
    r"\bwhich\b.*\bbetter\b",
    r"\bcompare\b",
    r"\bchoose\b",
    r"\bestimate\b",
    r"\bcalories\b",
    r"\blook like\b",
    r"\bpreview\b",
]


def classify_need(text: str) -> str:
    t = (text or "").lower()

    if any(re.search(p, t) for p in _WORKFLOW):
        return "workflow_time_saver"
    if any(re.search(p, t) for p in _DECISION):
        return "decision_preview"
    if any(re.search(p, t) for p in _SUPPORT):
        return "support_fix"

    return "unknown"
