from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import time
import requests

API = "https://api.stackexchange.com/2.3"


@dataclass
class SEQuestion:
    title: str
    text: str
    url: str
    tags: List[str]
    source: str
    query: Optional[str] = None
    view_count: int = 0
    answer_count: int = 0
    is_answered: bool = False
    score: int = 0
    last_activity_at: int = 0  # unix ts


def _request_json(endpoint: str, params: Dict, timeout: int = 25) -> Dict:
    r = requests.get(endpoint, params=params, timeout=timeout, headers={"User-Agent": "hunter-agent/0.1"})
    if r.status_code >= 400:
        try:
            data = r.json()
        except Exception:
            data = None

        if isinstance(data, dict) and data.get("error_name") == "throttle_violation":
            # поднимаем специальную ошибку
            raise RuntimeError(f"SE_THROTTLED:{data.get('error_message','')}|url={r.url}")

        raise RuntimeError(f"StackExchange HTTP {r.status_code}: {r.text} | url={r.url}")

    return r.json()

def _request_json(endpoint: str, params: Dict, timeout: int = 25) -> Dict:
    r = requests.get(endpoint, params=params, timeout=timeout, headers={"User-Agent": "hunter-agent/0.1"})

    # Cloudflare / HTML-ban page
    ct = (r.headers.get("content-type") or "").lower()
    if "text/html" in ct and ("too many requests" in (r.text or "").lower()):
        raise RuntimeError(f"SE_BLOCKED_HTML:{r.status_code}|url={r.url}")

    if r.status_code >= 400:
        ...

def fetch_questions_with_body(
    site: str,
    tagged: str,
    pages: int = 2,
    pagesize: int = 50,
    api_key: str | None = None,
    query: str | None = None,
) -> List[SEQuestion]:
    """
    2-step:
      1) /questions without body filter -> get ids
      2) /questions/{ids} with filter=withbody -> get bodies
    """
    all_ids: List[int] = []

    for page in range(1, pages + 1):
        params = {
            "site": site,
            "tagged": tagged,
            "pagesize": pagesize,
            "page": page,
            "order": "desc",
            "sort": "activity",
        }
        if api_key:
            params["key"] = api_key

        data = _request_json(f"{API}/questions", params=params)
        items = data.get("items") or []
        for it in items:
            qid = it.get("question_id")
            if qid:
                all_ids.append(int(qid))

        if not data.get("has_more"):
            break

        # лёгкий троттлинг, чтобы не рвать API
        time.sleep(0.2)

    if not all_ids:
        return []

    # step 2: bodies
    ids_str = ";".join(map(str, all_ids))
    params2 = {
        "site": site,
        "filter": "withbody",
        "pagesize": min(100, len(all_ids)),
    }
    if api_key:
        params2["key"] = api_key

    data2 = _request_json(f"{API}/questions/{ids_str}", params=params2)
    out: List[SEQuestion] = []
    for it in (data2.get("items") or []):
        out.append(
            SEQuestion(
                title=it.get("title") or "",
                text=it.get("body") or "",
                url=it.get("link") or "",
                tags=list(it.get("tags") or []),
                source="stackexchange",
                query=query,
                view_count=int(it.get("view_count") or 0),
                answer_count=int(it.get("answer_count") or 0),
                is_answered=bool(it.get("is_answered") or False),
                score=int(it.get("score") or 0),
                last_activity_at=int(it.get("last_activity_date") or 0),
            )
        )
    return out
