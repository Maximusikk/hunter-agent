# core/radar.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from collections import Counter, defaultdict


@dataclass
class RadarItem:
    signature: str
    count: int

    # aggregate metrics
    score: float
    total_views: int
    total_answers: int
    answered_ratio: float
    avg_votes: float
    age_days: float

    # meta
    label: str
    tags_top: List[str]
    sources: List[str]
    examples: List[str]


def _now_ts() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def _age_days_from_ts(ts: int) -> float:
    if not ts or ts <= 0:
        return 9999.0
    delta = _now_ts() - int(ts)
    if delta < 0:
        delta = 0
    return delta / 86400.0


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _pick_label(labels: Iterable[str]) -> str:
    """
    Берём самый частый label, но если есть что-то кроме 'unknown', предпочтём не-unknown.
    """
    c = Counter([l for l in labels if l])
    if not c:
        return "unknown"
    if len(c) == 1:
        return next(iter(c.keys()))
    # prefer non-unknown if present
    non_unknown = {k: v for k, v in c.items() if k != "unknown"}
    if non_unknown:
        return Counter(non_unknown).most_common(1)[0][0]
    return c.most_common(1)[0][0]


def _score_row(row: Dict[str, Any]) -> float:
    """
    Композитный скоринг "актуальность/массовость/полезность".

    row ожидаемо содержит:
      - view_count (int)
      - score (votes) (int)  # да, поле часто называется score у тебя
      - answer_count (int)
      - is_answered (bool)
      - days_since_activity (через last_activity_at)
    """
    views = _safe_int(row.get("view_count"), 0)
    votes = _safe_int(row.get("score"), 0)
    answers = _safe_int(row.get("answer_count"), 0)
    is_answered = bool(row.get("is_answered") or False)

    age_days = _age_days_from_ts(_safe_int(row.get("last_activity_at"), 0))
    # затухание: свежие важнее
    recency = 1.0 / (1.0 + age_days / 14.0)  # 14 дней "половинит" вклад

    # просмотры: логарифм, чтобы 100k не ломали всё
    views_term = (views + 1) ** 0.35  # мягче, чем log, но без math
    votes_term = max(votes, 0) * 2.0 + (abs(min(votes, 0)) * -1.0)  # штраф за минуса
    answers_term = min(answers, 10) * 1.5
    answered_bonus = 3.0 if is_answered else 0.0

    base = views_term + votes_term + answers_term + answered_bonus

    # если нет метрик вообще — пусть будет маленький, но не ноль
    if views == 0 and votes == 0 and answers == 0:
        base = 1.0

    return base * recency


def build_radar(
    items: List[Dict[str, Any]],
    min_count: int = 2,
    limit: int = 30,
) -> List[RadarItem]:
    """
    items: список "тасков" (или строк), где у каждой есть как минимум:
      - signature: str
      - text: str (пример/проблема)
      - tags: list[str]
      - source: str
      - last_activity_at: unix ts (int)  (может отсутствовать)
      - view_count / score / answer_count / is_answered (могут отсутствовать)
      - label (опционально)

    Возвращает агрегированные RadarItem по signature.
    """
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for row in items or []:
        sig = (row.get("signature") or "").strip()
        if not sig:
            continue
        buckets[sig].append(row)

    out: List[RadarItem] = []

    for sig, rows in buckets.items():
        if len(rows) < int(min_count):
            continue

        # агрегаты
        total_views = sum(_safe_int(r.get("view_count"), 0) for r in rows)
        total_answers = sum(_safe_int(r.get("answer_count"), 0) for r in rows)
        answered_cnt = sum(1 for r in rows if bool(r.get("is_answered") or False))
        answered_ratio = answered_cnt / max(len(rows), 1)

        votes_list = [_safe_int(r.get("score"), 0) for r in rows]
        avg_votes = sum(votes_list) / max(len(votes_list), 1)

        # age: берём "самую свежую активность" в кластере
        last_ts = max(_safe_int(r.get("last_activity_at"), 0) for r in rows)
        age_days = _age_days_from_ts(last_ts)

        # label
        label = _pick_label((str(r.get("label") or "unknown") for r in rows))

        # tags + sources
        tag_counter = Counter()
        src_counter = Counter()
        for r in rows:
            src = (r.get("source") or "unknown").strip()
            if src:
                src_counter[src] += 1
            tags = r.get("tags") or []
            if isinstance(tags, list):
                for t in tags:
                    t = str(t).strip().lower()
                    if t:
                        tag_counter[t] += 1

        tags_top = [t for t, _ in tag_counter.most_common(8)]
        sources = [s for s, _ in src_counter.most_common(5)]

        # score кластера: сумма композитных скорингов строк
        cluster_score = sum(_score_row(r) for r in rows)

        # примеры: топ по score_row
        ranked_rows = sorted(rows, key=_score_row, reverse=True)
        examples: List[str] = []
        for r in ranked_rows[:5]:
            txt = (r.get("text") or "").strip()
            if txt:
                # чуть режем, чтобы ответ не раздувался
                if len(txt) > 2200:
                    txt = txt[:2200] + "…"
                examples.append(txt)

        out.append(
            RadarItem(
                signature=sig,
                count=len(rows),
                score=float(cluster_score),
                total_views=int(total_views),
                total_answers=int(total_answers),
                answered_ratio=float(answered_ratio),
                avg_votes=float(avg_votes),
                age_days=float(age_days),
                label=label,
                tags_top=tags_top,
                sources=sources,
                examples=examples,
            )
        )

    # сортировка: сначала score, потом count
    out.sort(key=lambda x: (x.score, x.count), reverse=True)

    if limit and limit > 0:
        out = out[: int(limit)]

    return out
