from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Set

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.models import Task
from core.extractor import extract_task
from core.cluster import cluster_tasks
from core.cluster import _norm_text as norm_text
from core.idea_factory import ideas_from_clusters
app = FastAPI(title="Hunter Agent")


class IngestRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: Optional[str] = "manual"
    query: Optional[str] = None
    url: Optional[str] = None


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
    created_at: str


class StoredTask(BaseModel):
    id: int
    raw_id: int
    task: Task
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

@app.get("/ideas")
def ideas(limit: int = 10, min_count: int = 2):
    all_tasks = [st.task for st in TASK_STORE]
    clusters_list = cluster_tasks(all_tasks, sample_size=3)
    clusters_list = [c for c in clusters_list if c["count"] >= min_count]

    ideas_list = ideas_from_clusters(clusters_list, limit=limit)
    return {"count": len(ideas_list), "items": [i.model_dump() for i in ideas_list]}
@app.get("/tasks")
def tasks(limit: int = 50):
    items = TASK_STORE[-limit:]
    return {"count": len(TASK_STORE), "items": [x.model_dump() for x in items]}


@app.get("/clusters")
def clusters(limit: int = 20, min_count: int = 1, sample_size: int = 3):
    # Build clusters from extracted tasks
    all_tasks = [st.task for st in TASK_STORE]
    clusters_list = cluster_tasks(all_tasks, sample_size=sample_size)
    clusters_list = [c for c in clusters_list if c["count"] >= min_count]
    return {"count": len(clusters_list), "items": clusters_list[:limit]}


@app.post("/reset")
def reset():
    RAW_STORE.clear()
    TASK_STORE.clear()
    EXTRACTED_RAW_IDS.clear()
    RAW_DEDUP_SET.clear()
    return {"ok": True}
