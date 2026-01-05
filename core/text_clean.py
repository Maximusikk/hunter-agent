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
