from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus

import requests


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass
class MarketScan:
    query: str
    results: List[SearchResult]
    verdict: str  # "occupied" | "partially_occupied" | "open" | "unknown"
    competition_score: int  # 0..10
    notes: str


_TITLE_CLEAN_RX = re.compile(r"\s+")
_TAG_RX = re.compile(r"<[^>]+>")
_WS_RX = re.compile(r"\s+")

# DuckDuckGo Lite has predictable markup; we'll parse anchors.
# Example: <a rel="nofollow" class="result-link" href="...">Title</a>
_LINK_RX = re.compile(
    r'<a[^>]+class="result-link"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE,
)
_SNIP_RX = re.compile(
    r'<td[^>]+class="result-snippet"[^>]*>(.*?)</td>',
    re.IGNORECASE,
)


def _strip_html(s: str) -> str:
    s = _TAG_RX.sub(" ", s or "")
    s = _WS_RX.sub(" ", s).strip()
    return s


def duckduckgo_lite_search(query: str, max_results: int = 8, timeout: int = 25) -> List[SearchResult]:
    q = quote_plus(query)
    urls = [
        f"https://lite.duckduckgo.com/lite/?q={q}",
        f"https://duckduckgo.com/html/?q={q}",  # fallback на другой html
    ]

    last_debug = ""
    for url in urls:
        r = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
            allow_redirects=True,
        )

        # если блок/капча/редирект на защиту — покажем это наверх
        ct = (r.headers.get("content-type") or "").lower()
        if r.status_code != 200 or "text/html" not in ct:
            last_debug = f"{url} -> status={r.status_code}, content-type={ct}"
            continue

        html_txt = r.text
        # простая диагностика “бот-чек”
        low = html_txt.lower()
        if "captcha" in low or "verify" in low and "human" in low:
            last_debug = f"{url} -> bot-check page (captcha/verify)."
            continue

        links = _LINK_RX.findall(html_txt)
        snippets = _SNIP_RX.findall(html_txt)

        results: List[SearchResult] = []
        for i, (href, title_html) in enumerate(links[:max_results]):
            title = _strip_html(title_html)
            title = _TITLE_CLEAN_RX.sub(" ", title).strip()

            snippet = ""
            if i < len(snippets):
                snippet = _strip_html(snippets[i])

            if not href or not title:
                continue
            results.append(SearchResult(title=title, url=href, snippet=snippet))

        if results:
            return results

        last_debug = f"{url} -> parsed 0 results (html changed or blocked)."

    # если оба источника не дали результата — пробрасываем “почему”
    raise RuntimeError(f"Search returned 0 results. Debug: {last_debug}")


def _score_competition(results: List[SearchResult]) -> tuple[int, str, str]:
    """
    Quick heuristic:
    - if many results look like products/apps => higher competition
    - if mostly forums/docs => lower competition
    """
    if not results:
        return 0, "unknown", "No results returned."

    product_markers = (
        "app", "download", "pricing", "pricing", "subscription", "ios app", "android app",
        "chrome extension", "extension", "saas", "product", "get started", "sign up",
    )
    forum_markers = (
        "stack overflow", "super user", "reddit", "github", "docs", "documentation",
        "how to", "tutorial", "guide",
    )

    product_hits = 0
    forum_hits = 0
    for r in results:
        s = f"{r.title} {r.snippet}".lower()
        if any(m in s for m in product_markers):
            product_hits += 1
        if any(m in s for m in forum_markers):
            forum_hits += 1

    # competition score 0..10
    # more "product-like" results => higher competition
    score = min(10, max(0, product_hits * 2 + (1 if product_hits >= 3 else 0)))

    # verdict
    if product_hits >= 4:
        verdict = "occupied"
        notes = f"Many product-like results ({product_hits}). Likely crowded."
    elif product_hits >= 2:
        verdict = "partially_occupied"
        notes = f"Some product-like results ({product_hits}). Possible niche if you differentiate."
    else:
        verdict = "open"
        notes = f"Few/no product-like results ({product_hits}). Looks open or underserved."

    # if it's mostly forums/docs, highlight that
    if forum_hits >= 4 and product_hits <= 1:
        notes += " Mostly forums/docs => opportunity for a packaged tool."

    return score, verdict, notes


def run_market_scan(query: str, max_results: int = 8, sleep_s: float = 0.2) -> MarketScan:
    try:
        results = duckduckgo_lite_search(query=query, max_results=max_results)
        time.sleep(sleep_s)
        comp_score, verdict, notes = _score_competition(results)
        return MarketScan(query=query, results=results, verdict=verdict, competition_score=comp_score, notes=notes)
    except Exception as e:
        return MarketScan(
            query=query,
            results=[],
            verdict="unknown",
            competition_score=0,
            notes=f"Search failed: {type(e).__name__}: {e}",
        )

