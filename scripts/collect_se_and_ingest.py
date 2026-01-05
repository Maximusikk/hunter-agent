from __future__ import annotations

import os
import requests

from collectors.stackexchange import fetch_questions_with_body

API_BASE = "http://127.0.0.1:8000"


def ingest(payload: dict) -> bool:
    r = requests.post(f"{API_BASE}/ingest", json=payload, timeout=25)
    if r.status_code == 400:
        return False
    r.raise_for_status()
    data = r.json()
    return not data.get("deduped", False)


def main() -> None:
    se_key = os.getenv("STACKEXCHANGE_KEY")

    targets = [
        ("superuser", "windows-11;wifi"),
        ("superuser", "windows-11;networking"),
        ("superuser", "windows-11;bluetooth"),
        ("superuser", "iphone;ios"),
        ("superuser", "android;battery"),
        ("superuser", "android;notifications"),
        ("stackoverflow", "python;fastapi"),
    ]

    total = 0
    ingested_count = 0

    for site, tagged in targets:
        items = fetch_questions_with_body(site=site, tagged=tagged, pages=3, pagesize=50, api_key=se_key)

        for it in items:
            total += 1

            payload = {
                "text": it.text,
                "source": it.source,
                "query": f"{it.site}:{it.query}",
                "url": it.url,
                "tags": it.tags,
                "created_at_source": it.created_at,
                "last_activity_at_source": it.last_activity_at,
                "view_count": it.view_count,
                "score": it.score,
                "answer_count": it.answer_count,
                "is_answered": it.is_answered,
            }

            if ingest(payload):
                ingested_count += 1

    print(f"Collected: {total} | Ingested: {ingested_count}")
    print("Next: POST /extract then GET /radar")


if __name__ == "__main__":
    main()
