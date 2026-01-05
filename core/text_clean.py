# core/text_clean.py
from __future__ import annotations

import html
import re

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(text)
    text = TAG_RE.sub(" ", text)
    text = text.replace("'", " ").replace('"', " ")
    text = WS_RE.sub(" ", text).strip()
    return text


# alias для старого имени, чтобы IDE не ругалась и старый код не падал
def html_to_text(text: str) -> str:
    return clean_text(text)
