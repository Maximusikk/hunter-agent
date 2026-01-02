from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Set

from fastapi import FastAPI
from pydantic import BaseModel, Field

from core.models import Task
from core.extractor import extract_task

app = FastAPI(title="Hunter Agent")


# ----------------------------
# API Schemas
# ----------------------------
class IngestRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: Optional[str] = "manual"
    query: Optional[str] = None
    url: Optional[str] = None


class ExtractRequest(BaseModel):
    limit: int = 50  # how many latest raw items to process
    only_new: bool = True  # skip already-extracted raw ids


class StoredRaw(BaseModel):
    id: int
    text: str
    source: Optional[str] = None
    query: Optional[str] = None
    url: Optional[str] = None
    created_at: str


class StoredTask(BaseModel):
    id: int
    raw_id: int
    task: Task
    created_at: str


# ----------------------------
# In-memory stores (MVP)
# ----------------------------
RAW_STORE: List[StoredRaw] = []
TASK_STORE: List[StoredTask] = []
EXTRACTED_RAW_IDS: Set[int] = set()


# ----------------------------
# Endpoints
# ----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(req: IngestRequest):
    item = StoredRaw(
        id=len(RAW_STORE) + 1,
        text=req.text.strip(),
        source=req.source,
        query=req.query,
        url=req.url,
        created_at=datetime.utcnow().isoformat() + "Z",
    )
    RAW_STORE.append(item)
    return {"ok": True, "item": item.model_dump()}


@app.get("/raw")
def raw(limit: int = 50):
    items = RAW_STORE[-limit:]
    return {"count": len(RAW_STORE), "items": [x.model_dump() for x in items]}


@app.post("/extract")
def extract(req: ExtractRequest):
    # Choose candidates
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


@app.get("/tasks")
def tasks(limit: int = 50):
    items = TASK_STORE[-limit:]
    return {"count": len(TASK_STORE), "items": [x.model_dump() for x in items]}


@app.post("/reset")
def reset():
    RAW_STORE.clear()
    TASK_STORE.clear()
    EXTRACTED_RAW_IDS.clear()
    return {"ok": True}
