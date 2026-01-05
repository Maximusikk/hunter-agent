from __future__ import annotations

import re

# Жёстко режем dev/support (оно забивает весь радар)
DEV_DENY = {
    "fastapi", "pydantic", "sqlalchemy", "uvicorn", "pytest", "pip", "venv",
    "docker", "kubernetes", "k8s", "jwt", "oauth", "traceback", "exception",
    "stack trace", "mypy", "types", "asyncio", "httpx", "requests", "flask",
    "django", "react", "vite", "node", "npm", "yarn", "git",
}

# Decision / “узнать быстрее”
DECISION_HINTS = {
    "what is this", "what is that", "identify", "recognize", "detect",
    "is this safe", "is this dangerous", "dangerous", "poisonous",
    "estimate", "calories", "macro", "nutrition", "ingredients",
    "which looks better", "which one", "choose", "recommend",
    "does this look", "how do i look", "outfit", "style", "haircut", "hairstyle",
    "plant", "insect", "bug", "mushroom",
    "is it legit", "scam", "fake", "authentic",
    "from a photo", "from this photo", "from this picture", "from this screenshot",
}

# Маркеры “внешний мир” (часто предполагается image/screenshot)
IMAGE_HINTS = {
    "photo", "picture", "image", "screenshot", "camera", "scan", "snap",
}

# Одноразовые “не работает” — обычно не твой кейс
ONE_OFF_FIX_HINTS = {
    "not working", "error", "fails", "failed", "doesn't work", "does not work",
    "crash", "bug", "issue", "problem", "can't", "cannot",
}

WS_RE = re.compile(r"\s+")

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = WS_RE.sub(" ", s)
    return s

def is_dev_support(text: str) -> bool:
    t = _norm(text)
    return any(k in t for k in DEV_DENY)

def has_decision_signal(text: str) -> bool:
    t = _norm(text)
    return any(k in t for k in DECISION_HINTS) or any(k in t for k in IMAGE_HINTS)

def is_one_off_fix(text: str) -> bool:
    t = _norm(text)
    # если нет decision-сигналов, а есть “не работает” → считаем одноразовым фикс-постом
    return any(k in t for k in ONE_OFF_FIX_HINTS) and not has_decision_signal(t)

def is_signal_strict(text: str) -> bool:
    """Строгий пропуск: decision-сценарий и не dev-support."""
    if not text or len(text.strip()) < 12:
        return False
    if is_dev_support(text):
        return False
    if is_one_off_fix(text):
        return False
    return has_decision_signal(text)

def is_signal_soft(text: str) -> bool:
    """Мягкий пропуск: чуть шире, но всё равно режем dev-support."""
    if not text or len(text.strip()) < 8:
        return False
    if is_dev_support(text):
        return False
    # допускаем, если есть хотя бы намёк на image/screenshot/выбор/оценку
    return has_decision_signal(text)
