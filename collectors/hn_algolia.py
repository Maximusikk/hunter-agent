from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import time
import requests


@dataclass
class HNItem:
    title: str
    text: str
    url: Optional[str]
    tags: List[str]
    points: int
    num_comments: int
    created_at_i: int
    source: str = "hn"


ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"


def search_hn(
    query: str,
    pages: int = 2,
    hits_per_page: int = 50,
    sleep_s: float = 0.5,
) -> List[HNItem]:
    out: List[HNItem] = []
    for page in range(pages):
        params = {
            "query": query,
            "tags": "story",
            "page": page,
            "hitsPerPage": hits_per_page,
        }
        r = requests.get(
            ALGOLIA,
            params=params,
            timeout=25,
            headers={"User-Agent": "hunter-agent/0.1"},
        )
        r.raise_for_status()
        data = r.json()
        hits = data.get("hits") or []
        for h in hits:
            title = (h.get("title") or "").strip()
            story_text = (h.get("story_text") or "").strip()
            url = h.get("url") or h.get("story_url")
            created_at_i = int(h.get("created_at_i") or 0)
            points = int(h.get("points") or 0)
            num_comments = int(h.get("num_comments") or 0)

            # HN часто без body — сделаем “псевдо-текст” чтобы extractor работал
            combined = title
            if story_text:
                combined = f"{title}\n\n{story_text}"

            if not combined.strip():
                continue

            tags = ["hn", "story", "query:" + query]
            out.append(
                HNItem(
                    title=title,
                    text=combined,
                    url=url,
                    tags=tags,
                    points=points,
                    num_comments=num_comments,
                    created_at_i=created_at_i,
                )
            )
        time.sleep(sleep_s)
    return out
