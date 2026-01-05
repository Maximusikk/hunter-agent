from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

from collectors.reddit_public import fetch_posts
from core.signal_filter import is_signal_strict, is_signal_soft
from core.text_clean import clean_text

API_BASE = os.getenv("HUNTER_API_BASE", "http://127.0.0.1:8000")


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
        # ниже метрики — пока 0 (reddit public json не даёт нормально/стабильно)
        "view_count": 0,
        "answer_count": 0,
        "is_answered": False,
        "vote_score": 0,
        "last_activity_at": 0,
        "signature": None,
    }
    r = requests.post(f"{API_BASE}/ingest", json=payload, timeout=25)

    if r.status_code == 400:
        # placeholder / пустота / мусор
        return False

    r.raise_for_status()
    data = r.json()
    return not data.get("deduped", False)


def _should_keep(full_text: str, title: str) -> bool:
    """
    Твоя логика MVP: strict на body (или сумме), soft на title.
    """
    if not full_text and not title:
        return False

    # reddit часто короткий — используем смесь
    merged = (title + "\n\n" + full_text).strip()

    # strict — на контент, soft — на заголовок
    return is_signal_strict(merged) or is_signal_soft(title)


def collect_reddit_routine() -> List[Dict[str, Any]]:
    """
    Собираем то, что ближе к рутине/повседневке/продуктивности/AI-ассистам,
    а не “разовый баг в fastapi”.
    """
    subreddits = [
        # рутина / продуктивность / списки / заметки
        "productivity",
        "GetDisciplined",
        "LifeProTips",
        "Notion",
        "ObsidianMD",
        "todoist",
        "Evernote",
        "OneNote",
        "GoogleKeep",

        # таблицы
        "excel",
        "GoogleSheets",

        # автоматизация / домашние дела / цифровой быт
        "automation",
        "shortcuts",      # iOS Shortcuts
        "homeassistant",

        # “AI помогает в жизни”
        "ArtificialInteligence",
        "ChatGPT",
        "OpenAI",
        "LocalLLaMA",
        "StableDiffusion",

        # здоровье/еда (под твой пример “калории по фото”)
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

        for p in posts:
            title = (p.title or "").strip()
            raw_text = (p.text or "").strip()
            url = p.url

            if not title and not raw_text:
                continue

            if not _should_keep(full_text=raw_text, title=title):
                continue

            cleaned = clean_text(raw_text)
            if len(cleaned) < 80:
                # слишком короткие — часто шум (мемы/одно предложение)
                continue

            out.append(
                {
                    "text": cleaned,
                    "source": p.source,
                    "query": p.query,
                    "url": url,
                    "tags": ["reddit", f"r:{sr}"],
                }
            )

        # чтобы reddit не злился
        time.sleep(0.5)

    return out


def main() -> None:
    items = collect_reddit_routine()

    total = len(items)
    ingested = 0

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
