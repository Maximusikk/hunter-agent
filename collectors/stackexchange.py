from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import requests


@dataclass
class CollectedItem:
    source: str
    title: str
    text: str
    url: str
    query: Optional[str] = None


def fetch_stackexchange_questions(
    site: str = "stackoverflow",
    tagged: str = "python",
    pagesize: int = 20,
    sort: str = "activity",
) -> List[CollectedItem]:
    """
    StackExchange API (официальный): берём вопросы по тегам.
    site: stackoverflow | superuser | serverfault ...
    tagged: "python;fastapi" (через ;)
    """
    url = "https://api.stackexchange.com/2.3/questions"
    params = {
        "site": site,
        "pagesize": pagesize,
        "order": "desc",
        "sort": sort,
        "tagged": tagged,
        # body не берём (нужно отдельное поле filter),
        # но нам хватает title + link как "сырье"
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    items: List[CollectedItem] = []
    for q in data.get("items", []):
        title = q.get("title", "") or ""
        link = q.get("link", "") or ""
        # как сырье используем заголовок (уже боль)
        text = title
        items.append(CollectedItem(source=f"stackexchange:{site}", title=title, text=text, url=link, query=tagged))

    return items
