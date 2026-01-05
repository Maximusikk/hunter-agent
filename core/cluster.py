from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from core.models import Task

_WS_RX = re.compile(r"\s+")
_WORD_RX = re.compile(r"[a-z0-9]+|[а-я0-9]+", re.IGNORECASE)

_STOP = {
    "how", "what", "why", "does", "do", "is", "are", "to", "in", "on", "for", "with",
    "and", "or", "a", "the", "of", "my", "i", "can", "it", "this", "when", "then",
    "using", "use", "used", "work", "works", "working", "problem", "issue", "error",
    "help", "need", "question", "trying",
    "windows", "android", "iphone", "ios",
}

def norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = _WS_RX.sub(" ", s)
    return s

def _top_keyword(text: str) -> str:
    t = norm_text(text)
    words = [w.lower() for w in _WORD_RX.findall(t)]
    words = [w for w in words if len(w) >= 4 and w not in _STOP]
    if not words:
        return "misc"
    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    # 1 ключевое слово — чтобы topic не дробился
    return sorted(freq.items(), key=lambda x: (-x[1], x[0]))[0][0]

def _topic_from_tags(tags: Optional[List[str]], k: int = 2) -> str:
    if not tags:
        return ""
    clean = [t.strip().lower() for t in tags if t and t.strip()]
    clean = sorted(set(clean))
    if not clean:
        return ""
    return "tags:" + "+".join(clean[:k])

def _topic_from_query(query: Optional[str]) -> str:
    q = (query or "").strip().lower()
    if not q:
        return ""
    # query у тебя типа "windows-11;wifi" — уже отличный coarse topic
    return "q:" + q.replace(";", "+")

def cluster_task_pairs(
    pairs: List[Tuple[Task, Optional[List[str]], Optional[str], str]],
    sample_size: int = 3,
) -> List[Dict]:
    """
    pairs: (task, tags, query, raw_text)
    topic приоритет:
      1) tags (2 штуки)
      2) query (tagged string)
      3) fallback: 1 ключевое слово из текста
    """
    buckets: Dict[Tuple[str, str, str, str], Dict] = defaultdict(lambda: {"count": 0, "examples": []})

    for task, tags, query, raw_text in pairs:
        domain = task.domain or "general"
        intent = task.intent or "understand"
        output_type = task.output_type or "summary"

        topic = _topic_from_tags(tags)
        if not topic:
            topic = _topic_from_query(query)
        if not topic:
            topic = "kw:" + _top_keyword(raw_text or task.problem_statement)

        key = (domain, intent, output_type, topic)
        b = buckets[key]
        b["count"] += 1
        if len(b["examples"]) < sample_size:
            b["examples"].append(task.problem_statement)

    clusters: List[Dict] = []
    for (domain, intent, output_type, topic), data in buckets.items():
        clusters.append(
            {
                "key": f"{domain}|{intent}|{output_type}|{topic}",
                "domain": domain,
                "intent": intent,
                "output_type": output_type,
                "topic": topic,
                "count": data["count"],
                "examples": data["examples"],
            }
        )

    clusters.sort(key=lambda c: c["count"], reverse=True)
    return clusters

