from __future__ import annotations

import time
from typing import Optional, List, Dict, Any

import requests

from core.text_clean import clean_text
from core.signal_filter import is_signal_strict, is_signal_soft

from collectors.reddit_public import fetch_posts  # уже есть у тебя
from collectors.hn_algolia import search_hn


API_BASE = "http://127.0.0.1:8000"


def ingest(
    text: str,
    source: str,
    query: Optional[str],
    url: Optional[str],
    tags: Optional[List[str]],
    view_count: int = 0,
    answer_count: int = 0,
    is_answered: bool = False,
    vote_score: int = 0,
    last_activity_at: int = 0,
    signature: Optional[str] = None,
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
    r = requests.post(f"{API_BASE}/ingest", json=payload, timeout=25)
    if r.status_code == 400:
        return False
    r.raise_for_status()
    data = r.json()
    return not data.get("deduped", False)


def _should_keep(body: str, title: str) -> bool:
    """
    Тут мы делаем важный смысловой сдвиг:
    - строгий фильтр на body
    - мягкий на title
    """
    b = clean_text(body)
    t = clean_text(title)
    if is_signal_strict(b):
        return True
    return is_signal_soft(t)


def collect_reddit() -> List[Dict[str, Any]]:
    """
    Возвращает унифицированные элементы:
    {text, title, url, tags, score, created_utc}
    """
    # Сабреддиты специально под “рутинные боли/автоматизация/AI”
    subreddits = [
        "productivity",
        "Notion",
        "ObsidianMD",
        "todoist",
        "excel",
        "GoogleSheets",
        "automation",
        "LifeProTips",
        "ios",
        "androidapps",
        "homeassistant",
        "MealPrepSunday",
        "nutrition",
        "personalfinance",
        "travel",
    ]

    out: List[Dict[str, Any]] = []
    for sr in subreddits:
        try:
            posts = fetch_posts(subreddit=sr, limit=80, sort="new")  # см. твой collectors/reddit_public.py
        except Exception as e:
            print(f"[reddit] error r/{sr}: {e}")
            continue

        for p in posts:
            title = (p.get("title") or "").strip()
            body = (p.get("selftext") or "").strip()
            url = p.get("url") or p.get("permalink")
            if url and url.startswith("/"):
                url = "https://www.reddit.com" + url

            if not title and not body:
                continue

            text = title if not body else f"{title}\n\n{body}"
            tags = ["reddit", f"r:{sr}"]
            score = int(p.get("score") or 0)
            created_utc = int(p.get("created_utc") or 0)

            if not _should_keep(body=text, title=title):
                continue

            out.append(
                {
                    "text": clean_text(text),
                    "title": title,
                    "url": url,
                    "tags": tags,
                    "score": score,
                    "created_utc": created_utc,
                }
            )
        time.sleep(0.4)

    return out


def collect_hn() -> List[Dict[str, Any]]:
    # Запросы именно под “AI как инструмент для рутины”
    queries = [
        "AI assistant workflow",
        "automate spreadsheet",
        "meeting notes action items",
        "photo calorie estimate app",
        "AI stylist app",
        "voice notes summarize",
        "email inbox summarize",
        "personal finance assistant",
        "home inventory app",
        "plan trip AI",
    ]

    out: List[Dict[str, Any]] = []
    for q in queries:
        try:
            items = search_hn(q, pages=2, hits_per_page=50)
        except Exception as e:
            print(f"[hn] error query={q}: {e}")
            continue

        for it in items:
            title = it.title or ""
            text = it.text or title
            if not _should_keep(body=text, title=title):
                continue

            out.append(
                {
                    "text": clean_text(text),
                    "title": title,
                    "url": it.url,
                    "tags": it.tags,
                    "score": it.points,
                    "created_utc": it.created_at_i,
                    "answer_count": it.num_comments,
                }
            )
        time.sleep(0.4)

    return out


def main() -> None:
    total = 0
    passed = 0
    ingested = 0

    # Reddit
    reddit_items = collect_reddit()
    for it in reddit_items:
        total += 1
        passed += 1
        if ingest(
            text=it["text"],
            source="reddit",
            query=None,
            url=it.get("url"),
            tags=it.get("tags"),
            vote_score=int(it.get("score") or 0),
            last_activity_at=int(it.get("created_utc") or 0),
        ):
            ingested += 1

    # HN
    hn_items = collect_hn()
    for it in hn_items:
        total += 1
        passed += 1
        if ingest(
            text=it["text"],
            source="hn",
            query=None,
            url=it.get("url"),
            tags=it.get("tags"),
            vote_score=int(it.get("score") or 0),
            answer_count=int(it.get("answer_count") or 0),
            last_activity_at=int(it.get("created_utc") or 0),
        ):
            ingested += 1

    print(f"Collected: {total} | Passed filter: {passed} | Ingested: {ingested}")
    print("Next: POST /extract then GET /radar then GET /ideas")


if __name__ == "__main__":
    main()
