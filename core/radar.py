# core/radar.py
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class RadarItem:
    signature: str
    count: int
    score: float

    # aggregates
    total_views: int
    total_answers: int
    answered_ratio: float  # доля вопросов, где is_answered=True
    avg_votes: float
    last_activity_at: int
    age_days: float

    # labels
    label: str
    examples: List[str]
    tags_top: List[str]
    sources: List[str]


def _now_ts() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def _days_ago(ts: int, now_ts: int) -> float:
    if ts <= 0:
        return 9999.0
    return max(0.0, (now_ts - ts) / 86400.0)


def _freshness(days_since_activity: float, half_life_days: float = 14.0) -> float:
    return math.exp(-days_since_activity / half_life_days)


def _log1p(x: float) -> float:
    return math.log1p(max(0.0, x))


def build_radar(
    rows: List[Dict],
    min_count: int = 2,
    limit: int = 30,
    now_ts: Optional[int] = None,
) -> List[RadarItem]:
    """
    rows: список объектов вида:
      {
        "signature": str,
        "text": str,
        "tags": [...],
        "source": "...",
        "url": "...",
        "created_at": int,
        "last_activity_at": int,
        "view_count": int,
        "score": int,
        "answer_count": int,
        "is_answered": bool,
        "label": str
      }
    """
    now = now_ts or _now_ts()

    buckets: Dict[str, Dict] = {}

    for r in rows:
        sig = r["signature"]
        b = buckets.setdefault(
            sig,
            {
                "count": 0,
                "views": 0,
                "answers": 0,
                "votes_sum": 0,
                "answered_cnt": 0,   # <- фикс
                "last_activity": 0,
                "examples": [],
                "tags_freq": {},
                "sources": set(),
                "label_freq": {},
            },
        )

        b["count"] += 1
        b["views"] += int(r.get("view_count") or 0)
        b["answers"] += int(r.get("answer_count") or 0)
        b["votes_sum"] += int(r.get("score") or 0)
        b["answered_cnt"] += 1 if r.get("is_answered") else 0  # <- фикс
        b["last_activity"] = max(b["last_activity"], int(r.get("last_activity_at") or 0))
        b["sources"].add(str(r.get("source") or "unknown"))

        lab = str(r.get("label") or "unknown")
        b["label_freq"][lab] = b["label_freq"].get(lab, 0) + 1

        for t in (r.get("tags") or []):
            t = str(t).lower().strip()
            if not t:
                continue
            b["tags_freq"][t] = b["tags_freq"].get(t, 0) + 1

        txt = str(r.get("text") or "").strip()
        if txt and len(b["examples"]) < 4:
            b["examples"].append(txt)

    radar: List[RadarItem] = []

    for sig, b in buckets.items():
        cnt = b["count"]
        if cnt < min_count:
            continue

        views = b["views"]
        answers = b["answers"]
        avg_votes = b["votes_sum"] / max(1, cnt)
        last_act = b["last_activity"]
        days_since = _days_ago(last_act, now)
        fresh = _freshness(days_since)

        # "дырка": много просмотров, мало ответов
        unanswered_gap = 1.0 if (views >= 2000 and answers <= max(1, cnt // 3)) else 0.0

        mass_term = _log1p(cnt)
        views_term = _log1p(views / 50.0)
        fresh_term = fresh
        gap_term = unanswered_gap
        votes_term = max(0.0, _log1p(avg_votes + 1))

        score = (
            35.0 * mass_term +
            40.0 * views_term +
            18.0 * fresh_term +
            12.0 * gap_term +
            6.0 * votes_term
        )

        label = max(b["label_freq"].items(), key=lambda kv: kv[1])[0]

        tags_sorted = sorted(b["tags_freq"].items(), key=lambda kv: kv[1], reverse=True)
        top_tags = [t for t, _ in tags_sorted[:5]]

        answered_ratio = b["answered_cnt"] / max(1, cnt)  # <- фикс

        radar.append(
            RadarItem(
                signature=sig,
                count=cnt,
                score=score,
                total_views=views,
                total_answers=answers,
                answered_ratio=answered_ratio,
                avg_votes=avg_votes,
                last_activity_at=last_act,
                age_days=days_since,
                label=label,
                examples=b["examples"],
                tags_top=top_tags,
                sources=sorted(list(b["sources"])),
            )
        )

    radar.sort(key=lambda x: x.score, reverse=True)
    return radar[:limit]
