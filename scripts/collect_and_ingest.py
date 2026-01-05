from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

from collectors.reddit_public import fetch_posts
from core.signal_filter import is_signal_strict, is_signal_soft
from core.text_clean import clean_text

API_BASE = os.getenv("HUNTER_API_BASE", "http://127.0.0.1:8000")
DEBUG = os.getenv("HUNTER_DEBUG", "0") == "1"


def ingest(
    text: str,
    source: str,
    query: Optional[str] = None,
    url: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    payload = {
        "text": text,
        "source": source,
        "query": query,
        "url": url,
        "tags": tags or [],
        # метрики пока 0 для reddit-public
        "view_count": 0,
        "answer_count": 0,
        "is_answered": False,
        "vote_score": 0,
        "last_activity_at": 0,
        "signature": None,
    }
    r = requests.post(f"{API_BASE}/ingest", json=payload, timeout=25)

    if r.status_code == 400:
        return False

    r.raise_for_status()
    data = r.json()
    return not data.get("deduped", False)


def _should_keep(merged_text: str, title: str) -> bool:
    """
    strict на merged (title+body), soft на title.
    """
    if not merged_text and not title:
        return False
    return is_signal_strict(merged_text) or is_signal_soft(title)


def collect_reddit_routine() -> List[Dict[str, Any]]:
    """
    Рутинные/повседневные темы + AI помощники (но не "разовый баг либы").
    """
    subreddits = [
        # рутина / заметки / списки
        "productivity",
        "GetDisciplined",
        "LifeProTips",
        "Notion",
        "ObsidianMD",
        "todoist",
        "OneNote",
        "GoogleKeep",

        # таблицы
        "excel",
        "GoogleSheets",

        # автоматизация / быт / shortcuts
        "automation",
        "shortcuts",
        "homeassistant",

        # AI в жизни (генерация, ассистенты, инструменты)
        "ChatGPT",
        "OpenAI",
        "LocalLLaMA",
        "StableDiffusion",

        # еда/питание (под кейсы "калории по фото" и т.п.)
        "nutrition",
        "MealPrepSunday",
        "loseit",
    ]

    out: List[Dict[str, Any]] = []

    for sr in subreddits:
        try:
            posts = fetch_posts(subreddit=sr, limit=80, sort="new", sleep_s=0.0)
        except Exception as e:
            print(f"[reddit] error r/{sr}: {e}")
            continue

        raw_n = len(posts)
        kept = 0
        too_short = 0
        filtered = 0

        for p in posts:
            title = (p.title or "").strip()
            body = (p.text or "").strip()  # у тебя text = title + selftext, но title отдельно тоже есть
            url = p.url

            # ВАЖНО: формируем merged из title + selftext (а не только selftext)
            # На случай если p.text уже содержит title, всё равно ок — дедуп потом отработает.
            merged_raw = (title + "\n\n" + body).strip()

            if not merged_raw:
                continue

            if not _should_keep(merged_text=merged_raw, title=title):
                filtered += 1
                continue

            merged_clean = clean_text(merged_raw)

            # порог уменьшаем: иначе линк-посты/короткие вопросы умирают
            if len(merged_clean) < 40:
                too_short += 1
                continue

            kept += 1
            out.append(
                {
                    "text": merged_clean,
                    "source": p.source,
                    "query": p.query,
                    "url": url,
                    "tags": ["reddit", f"r:{sr}"],
                }
            )

        if DEBUG:
            print(f"[reddit] r/{sr}: got={raw_n} filtered={filtered} too_short={too_short} kept={kept}")

        time.sleep(0.5)

    return out


def main() -> None:
    items = collect_reddit_routine()

    total = len(items)
    ingested = 0

    if DEBUG:
        print(f"[debug] total candidates after filter: {total}")

    for it in items:
        ok = ingest(
            text=it["text"],
            source=it["source"],
            query=it.get("query"),
            url=it.get("url"),
            tags=it.get("tags"),
        )
        if ok:
            ingested += 1

    print(f"Collected: {total} | Ingested: {ingested}")
    print("Next: POST /extract then GET /radar then GET /ideas")


if __name__ == "__main__":
    main()
