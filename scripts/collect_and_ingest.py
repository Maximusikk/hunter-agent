from __future__ import annotations

import requests
from core.text_clean import clean_text

API = "http://127.0.0.1:8000"


def ingest(text: str):
    r = requests.post(f"{API}/ingest", json={
        "text": text,
        "source": "stackexchange",
        "query": "windows-11",
        "url": ""
    })
    return r.status_code == 200


def collect():
    url = (
        "https://api.stackexchange.com/2.3/questions"
        "?pagesize=50&order=desc&sort=activity"
        "&tagged=windows-11&site=superuser&filter=withbody"
    )

    data = requests.get(url).json()
    collected = 0
    ingested = 0

    for item in data.get("items", []):
        body = clean_text(item.get("body", ""))
        if len(body) < 120:
            continue

        collected += 1
        if ingest(body):
            ingested += 1

    print(f"Collected: {collected} | Ingested: {ingested}")


if __name__ == "__main__":
    collect()
