from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Tuple

from core.models import Task

# --- Topic rules (без ML) ---
_TOPIC_RULES: list[tuple[str, list[str]]] = [
    ("meeting_notes_summary", [
        r"\bmeeting(s)?\b",
        r"\btranscript(s)?\b",
        r"\bminutes\b",
        r"\baction items?\b",
        r"\bnotes?\b",
        r"\bsummariz(e|ing|ation)\b",
        r"\bscattered\b",
        r"\bdocs?\b",
        r"\bchats?\b",
        r"\bworkflow\b",
        r"\brewriting\b",
        r"\bmanually\b",
    ]),
]

_COMPILED_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    (name, [re.compile(p, re.IGNORECASE) for p in pats])
    for name, pats in _TOPIC_RULES
]

_STOPWORDS = {
    # EN
    "a", "an", "the", "and", "or", "to", "for", "of", "on", "in", "at", "is", "are",
    "with", "my", "your", "this", "that", "it", "does", "do", "not", "keeps", "keep",
    "cant", "can't", "cannot", "won't", "wont", "why", "how", "what", "when",
    # RU
    "и", "или", "на", "в", "во", "к", "ко", "по", "из", "у", "с", "со", "это",
    "не", "почему", "как", "что", "когда",
}


def _norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def classify_topic(text: str) -> str:
    """
    Стабильный topic для кластеров.
    1) Сначала пытаемся попасть в rule bucket (например meeting_notes_summary)
    2) Если не попали — fallback: первые 2-4 "значимых" слова
    """
    t = _norm_text(text)
    if not t:
        return "unknown"

    best_name = None
    best_hits = 0

    for name, regs in _COMPILED_RULES:
        hits = sum(1 for rx in regs if rx.search(t))
        if hits > best_hits:
            best_hits = hits
            best_name = name

    if best_name and best_hits >= 2:
        return best_name

    # fallback
    words = re.findall(r"[a-z0-9]+|[а-я0-9]+", t, flags=re.IGNORECASE)
    words = [w for w in words if w not in _STOPWORDS and len(w) >= 3]
    if not words:
        return "misc"

    uniq = []
    for w in words:
        if w not in uniq:
            uniq.append(w)
        if len(uniq) >= 4:
            break
    return "_".join(uniq)


def cluster_tasks(tasks: List[Task], sample_size: int = 3) -> List[Dict]:
    """
    Groups tasks into clusters using key:
      (domain, intent, output_type, topic)
    where topic is rule-based classification from problem_statement.
    """
    buckets: Dict[Tuple[str, str, str, str], Dict] = defaultdict(lambda: {"count": 0, "examples": []})

    for task in tasks:
        topic = classify_topic(task.problem_statement)
        key = (task.domain, task.intent, task.output_type, topic)

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
