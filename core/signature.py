# core/signature.py
from __future__ import annotations

import re
from typing import List

STOPWORDS = {
    "the", "a", "an", "is", "are", "to", "of", "and", "or",
    "in", "on", "for", "with", "when", "while", "using",
    "how", "what", "why", "does", "do", "can", "cannot",
    "i", "my", "we", "our", "you",
}

KEYWORD_MAP = [
    # domain / product
    (r"\bfastapi\b", "fastapi"),
    (r"\bwindows\b|\bwindows 10\b|\bwindows 11\b", "windows"),
    (r"\biphone\b|\bios\b", "iphone"),
    (r"\bandroid\b", "android"),

    # problem types
    (r"\b(upload|download|transfer)\b", "file_transfer"),
    (r"\b(jwt|oauth|token|auth)\b", "auth"),
    (r"\b(wifi|bluetooth|network)\b", "network"),
    (r"\b(mock|pytest|test)\b", "testing"),
    (r"\b(summary|summarize|notes|transcript)\b", "summarization"),
    (r"\b(error|exception|traceback|fail)\b", "error"),
]


def normalize_words(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def extract_topic(title: str, body: str) -> str:
    text = f"{title} {body}".lower()

    for pattern, label in KEYWORD_MAP:
        if re.search(pattern, text):
            return label

    words = normalize_words(text)
    return words[0] if words else "misc"


def extract_domain(tags: List[str]) -> str:
    if not tags:
        return "general"

    if "fastapi" in tags or "python" in tags:
        return "dev"

    if "windows" in tags:
        return "pc"

    if "iphone" in tags or "ios" in tags:
        return "mobile"

    return "general"


def make_signature(*, title: str, body: str, tags: List[str]) -> str:
    """
    Stable clustering key:
    domain | intent | output | topic
    """

    domain = extract_domain(tags)
    intent = "understand"
    output = "summary"
    topic = extract_topic(title, body)

    return f"{domain}|{intent}|{output}|{topic}"
