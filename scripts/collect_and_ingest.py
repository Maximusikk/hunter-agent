from __future__ import annotations

import requests

from core.signal_filter import is_signal
from collectors.stackexchange import fetch_stackexchange_questions
from collectors.reddit_public import fetch_reddit_subreddit_new

API_BASE = "http://127.0.0.1:8000"


def ingest(text: str, source: str, query: str | None = None, url: str | None = None) -> None:
    payload = {"text": text, "source": source, "query": query, "url": url}
    r = requests.post(f"{API_BASE}/ingest", json=payload, timeout=10)
    r.raise_for_status()


def main() -> None:
    total = 0
    passed = 0

    # 1) StackExchange: супер-полезно для "объемной работы" (можно superuser вместо stackoverflow)
    se_items = fetch_stackexchange_questions(site="superuser", tagged="windows-11;networking", pagesize=30)
    for it in se_items:
        total += 1
        if is_signal(it.text, min_len=30):  # для заголовков уменьшаем минимальную длину
            ingest(it.text, it.source, it.query, it.url)
            passed += 1

    # 2) Reddit: сабы под "workflow / productivity / tech help", но фильтр должен жёстко резать шум
    reddit_items = fetch_reddit_subreddit_new("productivity", limit=50)
    for it in reddit_items:
        total += 1
        if is_signal(it.text, min_len=80):
            ingest(it.text, it.source, it.query, it.url)
            passed += 1

    print(f"Collected: {total}, passed filter: {passed}")
    print("Now run: POST /extract -> GET /clusters")


if __name__ == "__main__":
    main()
