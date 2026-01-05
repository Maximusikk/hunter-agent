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


def fetch_reddit_subreddit_new(subreddit: str, limit: int = 25) -> List[CollectedItem]:
    """
    Публичный JSON (без OAuth) для быстрого MVP.
    В будущем лучше перейти на официальный Reddit API.
    """
    url = f"https://www.reddit.com/r/{subreddit}/new.json"
    headers = {"User-Agent": "hunter-agent/0.1 (by u/placeholder)"}
    params = {"limit": limit}

    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()

    items: List[CollectedItem] = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        title = d.get("title", "") or ""
        selftext = d.get("selftext", "") or ""
        permalink = d.get("permalink", "") or ""
        link = "https://www.reddit.com" + permalink if permalink else ""
        # сырье: заголовок + кусок тела (если есть)
        text = (title + "\n\n" + selftext).strip()
        items.append(CollectedItem(source=f"reddit:r/{subreddit}", title=title, text=text, url=link, query=subreddit))

    return items
