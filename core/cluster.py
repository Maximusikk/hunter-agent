# core/cluster.py
from __future__ import annotations

import re
from typing import Iterable, Dict, Any, List

WS_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def norm_text(text: str) -> str:
    """
    Нормализация для дедупа / грубого сравнения.
    """
    if not text:
        return ""
    t = text.strip().lower()
    t = WS_RE.sub(" ", t)
    return t


def simple_topic_key(text: str) -> str:
    """
    Упрощённый ключ для кластеризации по "похожести" (очень грубо).
    Нужен только как fallback, если нет нормальной сигнатуры.
    """
    t = norm_text(text)
    t = NON_ALNUM_RE.sub(" ", t)
    t = WS_RE.sub(" ", t).strip()
    parts = t.split(" ")
    # берём первые 6 токенов как грубый "топик"
    return "_".join(parts[:6]) if parts else "misc"


def cluster_by_key(tasks: Iterable[Any], sample_size: int = 3) -> List[Dict[str, Any]]:
    """
    Fallback кластеризация, если тебе нужно быстро "что-то сгруппировать".
    Ожидаем, что task имеет поля domain/intent/output_type/problem_statement.
    """
    buckets: Dict[str, Dict[str, Any]] = {}

    for t in tasks:
        key = f"{t.domain}|{t.intent}|{t.output_type}|{simple_topic_key(t.problem_statement)}"
        b = buckets.get(key)
        if not b:
            b = {
                "key": key,
                "domain": t.domain,
                "intent": t.intent,
                "output_type": t.output_type,
                "topic": key.split("|", 3)[-1],
                "count": 0,
                "examples": [],
            }
            buckets[key] = b

        b["count"] += 1
        if len(b["examples"]) < sample_size:
            b["examples"].append(t.problem_statement)

    # сортировка по count desc
    return sorted(buckets.values(), key=lambda x: x["count"], reverse=True)


import re

WS_RE = re.compile(r"\s+")


def norm_text(text: str) -> str:
    """
    Normalization for dedup / signatures:
    - lowercase
    - collapse whitespace
    - strip
    """
    if not text:
        return ""
    t = text.strip().lower()
    t = WS_RE.sub(" ", t)
    return t
