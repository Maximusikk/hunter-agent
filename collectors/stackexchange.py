from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import time
import requests

from core.text_clean import clean_text


@dataclass
class SEQuestion:
    source: str          # "stackexchange"
    site: str            # "superuser", "stackoverflow", ...
    query: str           # tagged string you used
    url: str
    title: str
    text: str            # cleaned body (or title if no body)
    tags: List[str]

    # metrics
    created_at: int
    last_activity_at: int
    view_count: int
    score: int
    answer_count: int
    is_answered: bool


def fetch_questions_with_body(
    site: str,
    tagged: str,
    pages: int = 2,
    pagesize: int = 50,
    api_key: Optional[str] = None,
    sleep_s: float = 0.1,
) -> List[SEQuestion]:
    """
    Fetch questions from StackExchange API with body + useful metrics.
    No auth required (key optional).
    """
    out: List[SEQuestion] = []

    base = "https://api.stackexchange.com/2.3/questions"
    # filter=withbody returns body + usual fields
    params_base = {
        "site": site,
        "tagged": tagged,
        "pagesize": pagesize,
        "order": "desc",
        "sort": "activity",
        "filter": "withbody",
    }
    if api_key:
        params_base["key"] = api_key

    for page in range(1, pages + 1):
        params = dict(params_base)
        params["page"] = page

        r = requests.get(base, params=params, timeout=25, headers={"User-Agent": "hunter-agent"})
        r.raise_for_status()
        data = r.json()

        for it in data.get("items", []):
            title = (it.get("title") or "").strip()
            body_html = it.get("body") or ""
            body = clean_text(body_html)

            # иногда body пустой/короткий -> используем title как текст
            if len(body) < 80:
                text = title
            else:
                text = body

            link = it.get("link") or ""

            out.append(
                SEQuestion(
                    source="stackexchange",
                    site=site,
                    query=tagged,
                    url=link,
                    title=title,
                    text=text,
                    tags=list(it.get("tags") or []),
                    created_at=int(it.get("creation_date") or 0),
                    last_activity_at=int(it.get("last_activity_date") or it.get("creation_date") or 0),
                    view_count=int(it.get("view_count") or 0),
                    score=int(it.get("score") or 0),
                    answer_count=int(it.get("answer_count") or 0),
                    is_answered=bool(it.get("is_answered") or False),
                )
            )

        time.sleep(sleep_s)

    return out
