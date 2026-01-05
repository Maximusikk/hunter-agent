# core/subtopics.py
from __future__ import annotations

import re
from typing import List, Optional

_WORD_RX = re.compile(r"[a-z0-9]+|[а-я0-9]+", re.IGNORECASE)

# якорные "технические" подтемы, которые часто реально разделяют проблемы
# порядок важен: более специфичные сверху
_ANCHORS: list[tuple[str, list[str]]] = [
    ("oauth_jwt_auth", ["oauth", "jwt", "bearer", "token", "authorization", "auth", "login"]),
    ("http_redirect_status", ["307", "redirect", "status", "temporary", "permanent", "location", "trailing", "slash"]),
    ("file_upload_s3", ["s3", "amazon", "aws", "upload", "multipart", "presigned", "bucket"]),
    ("streaming_zip", ["zip", "archive", "compress", "streamingresponse", "stream", "iter_bytes"]),
    ("tar_gzip_stream", ["tar", "gzip", "tarfile", "addfile", "w|gz", "fileobj"]),
    ("websocket_audio_whisper", ["websocket", "whisper", "transcribe", "audio", "pcm", "wav", "bytes", "noise"]),
    ("async_mock_pytest", ["asyncmock", "pytest", "pytest-asyncio", "mock", "unittest", "patch", "__aenter__", "__aiter__"]),
    ("typing_pydantic_fastapi", ["pydantic", "basemodel", "literal", "enum", "openapi", "mypy", "pylance", "typing"]),
    ("db_sqlalchemy_sqlmodel", ["sqlalchemy", "sqlmodel", "session", "orm", "sqlite", "aiosqlite"]),
    ("logging_uvicorn", ["uvicorn", "logging", "timestamp", "log-level"]),
]

# общий мусор
_STOP = {
    "how", "what", "why", "does", "do", "is", "are", "to", "in", "on", "for", "with",
    "and", "or", "a", "the", "of", "my", "i", "can", "it", "this", "when", "then",
    "error", "issue", "problem", "help",
    "using", "use", "used", "trying", "try", "want", "need", "getting", "get",
    "python", "fastapi", "stackoverflow", "stackexchange",
}


def _tokens(text: str) -> list[str]:
    t = (text or "").lower()
    toks = [w.lower() for w in _WORD_RX.findall(t)]
    return toks


def pick_subtopic(text: str, tags: Optional[List[str]] = None, query: Optional[str] = None) -> str:
    """
    Возвращает устойчивый subtopic.
    Принцип:
      1) сначала пытаемся матчить "якоря" по тексту (они отделяют реально разные боли)
      2) если не нашли — пытаемся по тегам
      3) если не нашли — fallback: 2 содержательных токена (склеить)
    """
    toks = _tokens(text)
    text_lc = " ".join(toks)

    # 1) anchors by text
    for name, keys in _ANCHORS:
        for k in keys:
            if k in text_lc:
                return name

    # 2) anchors by tags
    tags_lc = [t.lower() for t in (tags or [])]
    tags_blob = " ".join(tags_lc)
    for name, keys in _ANCHORS:
        for k in keys:
            if k in tags_blob:
                return name

    # 3) query hint
    if query:
        q = query.lower()
        for name, keys in _ANCHORS:
            for k in keys:
                if k in q:
                    return name

    # 4) fallback: 2 содержательных слова
    content = [w for w in toks if len(w) >= 5 and w not in _STOP]
    if not content:
        return "misc"

    head = content[:30]
    # берём 2 наиболее частых
    freq: dict[str, int] = {}
    for w in head:
        freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:2]
    if not top:
        return "misc"
    if len(top) == 1:
        return top[0][0]
    return f"{top[0][0]}_{top[1][0]}"
