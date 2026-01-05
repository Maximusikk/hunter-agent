# scripts/collect_se_and_ingest.py
from __future__ import annotations

import os
from typing import Optional

import requests

from collectors.stackexchange import fetch_questions_with_body
from core.signal_filter import is_signal_strict, is_signal_soft
from core.text_clean import clean_text
from core.signature import make_signature

API_BASE = "http://127.0.0.1:8000"


def ingest(
    *,
    text: str,
    source: str,
    query: Optional[str],
    url: Optional[str],
    tags: list[str],
    view_count: int,
    answer_count: int,
    is_answered: bool,
    vote_score: int,
    last_activity_at: int,
    signature: str,
) -> bool:
    payload = {
        "text": text,
        "source": source,
        "query": query,
        "url": url,
        "tags": tags,
        "view_count": view_count,
        "answer_count": answer_count,
        "is_answered": is_answered,
        "vote_score": vote_score,
        "last_activity_at": last_activity_at,
        "signature": signature,
    }
    r = requests.post(f"{API_BASE}/ingest", json=payload, timeout=30)
    if r.status_code == 400:
        return False
    r.raise_for_status()
    data = r.json()
    return not data.get("deduped", False)


def _safe_int(obj, name: str, default: int = 0) -> int:
    v = getattr(obj, name, default)
    try:
        return int(v or 0)
    except Exception:
        return default


def _safe_bool(obj, name: str, default: bool = False) -> bool:
    v = getattr(obj, name, default)
    return bool(v) if v is not None else default


def main() -> None:
    se_key = os.getenv("STACKEXCHANGE_KEY")

    targets = [
        ("superuser", "windows-11;networking"),
        ("superuser", "windows-11;wifi"),
        ("superuser", "windows-11;bluetooth"),
        ("superuser", "android;battery"),
        ("superuser", "android;notifications"),
        ("superuser", "iphone;ios"),
        ("stackoverflow", "python;fastapi"),
    ]

    total = 0
    passed = 0
    ingested = 0

    for site, tagged in targets:
        items = fetch_questions_with_body(site=site, tagged=tagged, pages=4, pagesize=50, api_key=se_key)

        for it in items:
            total += 1

            body = clean_text(getattr(it, "text", "") or "")
            title = clean_text(getattr(it, "title", "") or "")

            if not body and not title:
                continue

            ok = is_signal_strict(body) or is_signal_soft(title)
            if not ok:
                continue

            passed += 1

            tags = list(getattr(it, "tags", []) or [])
            sig = make_signature(title=title, body=body, tags=tags)

            # метрики (безопасно, даже если полей нет)
            view_count = _safe_int(it, "view_count", 0)
            answer_count = _safe_int(it, "answer_count", 0)
            is_answered = _safe_bool(it, "is_answered", False)

            # StackExchange может отдавать score как "score" (upvotes-downvotes)
            vote_score = _safe_int(it, "vote_score", None) if hasattr(it, "vote_score") else _safe_int(it, "score", 0)

            # время активности: часто "last_activity_at" или "last_activity_date"
            last_activity_at = _safe_int(it, "last_activity_at", None) if hasattr(it, "last_activity_at") else _safe_int(
                it, "last_activity_date", 0
            )

            if ingest(
                text=body or title,
                source=str(getattr(it, "source", "stackexchange")),
                query=getattr(it, "query", None),
                url=getattr(it, "url", None),
                tags=tags,
                view_count=view_count,
                answer_count=answer_count,
                is_answered=is_answered,
                vote_score=vote_score,
                last_activity_at=last_activity_at,
                signature=sig,
            ):
                ingested += 1

    print(f"Collected: {total} | Passed filter: {passed} | Ingested: {ingested}")
    print("Next: POST /extract then GET /radar and GET /ideas")


if __name__ == "__main__":
    main()
