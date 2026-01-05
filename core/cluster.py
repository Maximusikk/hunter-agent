from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Tuple

from core.models import Task


_STOPWORDS = {
    # EN
    "a", "an", "the", "and", "or", "to", "for", "of", "on", "in", "at", "is", "are",
    "with", "my", "your", "this", "that", "it", "does", "do", "not", "keeps", "keep",
    "cant", "can't", "cannot", "won't", "wont", "why", "how", "what", "when",
    # RU
    "и", "или", "на", "в", "во", "к", "ко", "по", "из", "у", "с", "со", "это",
    "не", "почему", "как", "что", "когда", "у меня", "мой", "моя", "мои",
}

_TOPIC_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("wifi_disconnect", ["wifi", "wi-fi", "disconnect", "disconnected", "drops", "drop", "падает", "отваливается"]),
    ("bluetooth", ["bluetooth", "bt", "блютуз", "блютус"]),
    ("battery_drain", ["battery", "drain", "overnight", "разряжается", "батарея"]),
    ("storage_space", ["storage", "space", "disk", "ssd", "hdd", "место", "память", "диск"]),
    ("performance_slow", ["slow", "lag", "stutter", "freeze", "тормозит", "лагает", "фризы", "подвисает"]),
    ("update_failed", ["update", "updating", "failed", "error", "обнов", "ошибка", "код"]),
    ("login_auth", ["login", "sign in", "auth", "password", "войти", "логин", "пароль"]),
    ("audio_mic", ["mic", "microphone", "sound", "audio", "speaker", "микрофон", "звук", "аудио"]),
    ("camera", ["camera", "webcam", "камера", "вебкам"]),
    ("notifications", ["notification", "notify", "уведом", "push"]),
    ("app_crash", ["crash", "stops", "close", "force close", "вылетает", "краш"]),
]


def norm_text(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def guess_topic(text: str) -> str:
    t = norm_text(text)

    for topic, keys in _TOPIC_KEYWORDS:
        if any(k in t for k in keys):
            return topic

    # fallback: take 2-4 "meaningful" words
    words = re.findall(r"[a-z0-9]+|[а-я0-9]+", t, flags=re.IGNORECASE)
    words = [w for w in words if w not in _STOPWORDS and len(w) >= 3]
    if not words:
        return "unknown"

    # take first few unique words
    uniq = []
    for w in words:
        if w not in uniq:
            uniq.append(w)
        if len(uniq) >= 4:
            break
    return "_".join(uniq)


def cluster_tasks(tasks: List[Task], sample_size: int = 3) -> List[Dict]:
    """
    Groups tasks into clusters using a simple key:
      (domain, intent, output_type, topic)

    Returns list of dict clusters:
      { key, domain, intent, output_type, topic, count, examples }
    """
    buckets: Dict[Tuple[str, str, str, str], Dict] = defaultdict(lambda: {"count": 0, "examples": []})

    for task in tasks:
        topic = guess_topic(task.problem_statement)
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
