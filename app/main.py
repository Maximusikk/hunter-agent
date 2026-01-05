# app/main.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.models import Task
from core.extractor import extract_task
from core.cluster import norm_text
from core.radar import build_radar
from core.idea_builder import ideas_from_radar

app = FastAPI(title="Hunter Agent")


class IngestRequest(BaseModel):
    text: str = Field(..., min_length=1)

    # source info
    source: Optional[str] = "manual"
    query: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None

    # metrics (optional, from collectors)
    view_count: Optional[int] = 0
    answer_count: Optional[int] = 0
    is_answered: Optional[bool] = False
    vote_score: Optional[int] = 0
    last_activity_at: Optional[int] = 0  # unix ts
    signature: Optional[str] = None       # domain|intent|output|subtopic|keyword


class ExtractRequest(BaseModel):
    limit: int = 200
    only_new: bool = True


class StoredRaw(BaseModel):
    id: int
    text: str
    normalized: str

    source: Optional[str] = None
    query: Optional[str] = None
    url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # metrics
    view_count: int = 0
    answer_count: int = 0
    is_answered: bool = False
    vote_score: int = 0
    last_activity_at: int = 0
    signature: Optional[str] = None

    created_at: str


class StoredTask(BaseModel):
    id: int
    raw_id: int
    task: Task
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


RAW_STORE: List[StoredRaw] = []
TASK_STORE: List[StoredTask] = []
EXTRACTED_RAW_IDS: Set[int] = set()
RAW_DEDUP_SET: Set[str] = set()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(req: IngestRequest):
    text = req.text.strip()
    if text.lower() in {"string", "test", "asdf"}:
        raise HTTPException(status_code=400, detail="Placeholder text. Put a real problem/query.")

    normalized = norm_text(text)
    if normalized in RAW_DEDUP_SET:
        return {"ok": True, "deduped": True, "message": "Already ingested", "text": text}

    item = StoredRaw(
        id=len(RAW_STORE) + 1,
        text=text,
        normalized=normalized,
        source=req.source,
        query=req.query,
        url=req.url,
        tags=req.tags or [],
        view_count=int(req.view_count or 0),
        answer_count=int(req.answer_count or 0),
        is_answered=bool(req.is_answered or False),
        vote_score=int(req.vote_score or 0),
        last_activity_at=int(req.last_activity_at or 0),
        signature=req.signature,
        created_at=datetime.utcnow().isoformat() + "Z",
    )
    RAW_STORE.append(item)
    RAW_DEDUP_SET.add(normalized)
    return {"ok": True, "item": item.model_dump()}


@app.get("/raw")
def raw(limit: int = 50):
    items = RAW_STORE[-limit:]
    return {"count": len(RAW_STORE), "items": [x.model_dump() for x in items]}


@app.post("/extract")
def extract(req: ExtractRequest):
    candidates = RAW_STORE[-req.limit:] if req.limit > 0 else list(RAW_STORE)

    created: List[dict] = []
    skipped = 0

    for raw_item in candidates:
        if req.only_new and raw_item.id in EXTRACTED_RAW_IDS:
            skipped += 1
            continue

        task_obj = extract_task(raw_item.text)

        stored = StoredTask(
            id=len(TASK_STORE) + 1,
            raw_id=raw_item.id,
            task=task_obj,
            meta={
                "source": raw_item.source,
                "query": raw_item.query,
                "url": raw_item.url,
                "tags": raw_item.tags,
                "view_count": raw_item.view_count,
                "answer_count": raw_item.answer_count,
                "is_answered": raw_item.is_answered,
                "vote_score": raw_item.vote_score,
                "last_activity_at": raw_item.last_activity_at,
                "signature": raw_item.signature,
            },
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        TASK_STORE.append(stored)
        EXTRACTED_RAW_IDS.add(raw_item.id)
        created.append(stored.model_dump())

    return {
        "ok": True,
        "processed": len(candidates),
        "created": len(created),
        "skipped": skipped,
        "items": created,
    }


@app.get("/tasks")
def tasks(limit: int = 50):
    items = TASK_STORE[-limit:]
    return {"count": len(TASK_STORE), "items": [x.model_dump() for x in items]}


@app.get("/radar")
def radar(min_count: int = 2, limit: int = 30):
    rows: List[Dict[str, Any]] = []
    for st in TASK_STORE:
        m = st.meta or {}
        sig = m.get("signature")
        if not sig:
            # fallback: хотя бы domain|intent|output|tags|tags
            t = st.task
            tag_hint = "+".join(sorted(set((m.get("tags") or [])[:3]))) or "misc"
            sig = f"{t.domain}|{t.intent}|{t.output_type}|tags:{tag_hint}|tags:{tag_hint}"

        rows.append(
            {
                "signature": sig,
                "text": st.task.problem_statement,
                "tags": m.get("tags") or [],
                "source": m.get("source") or "unknown",
                "url": m.get("url") or None,
                "created_at": 0,
                "last_activity_at": int(m.get("last_activity_at") or 0),
                "view_count": int(m.get("view_count") or 0),
                "score": int(m.get("vote_score") or 0),
                "answer_count": int(m.get("answer_count") or 0),
                "is_answered": bool(m.get("is_answered") or False),
                "label": m.get("label") or "unknown",
            }
        )

    items = build_radar(items=rows, min_count=min_count, limit=limit)

    return {
        "count": len(items),
        "items": [
            {
                "signature": x.signature,
                "count": x.count,
                "score": round(x.score, 2),
                "total_views": x.total_views,
                "total_answers": x.total_answers,
                "answered_ratio": round(x.answered_ratio, 3),
                "avg_votes": round(x.avg_votes, 2),
                "days_since_activity": round(x.age_days, 1),
                "label": x.label,
                "tags_top": x.tags_top,
                "sources": x.sources,
                "examples": x.examples,
            }
            for x in items
        ],
    }


@app.get("/ideas")
def ideas(min_count: int = 2, limit: int = 10):
    r = radar(min_count=min_count, limit=max(limit, 50))
    radar_items = r.get("items") or []
    ideas_list = ideas_from_radar(radar_items, limit=limit)
    return {"count": len(ideas_list), "items": [x.model_dump() for x in ideas_list]}


@app.post("/reset")
def reset():
    RAW_STORE.clear()
    TASK_STORE.clear()
    EXTRACTED_RAW_IDS.clear()
    RAW_DEDUP_SET.clear()
    return {"ok": True}
