# core/idea_builder.py
from __future__ import annotations

from typing import Any, Dict, List

from core.models import Idea, Task


def _bucket_title(subtopic: str) -> str:
    mapping = {
        "meeting_notes_summary": "Meeting Notes → Action Items",
        "oauth_jwt_auth": "JWT/OAuth Auth Troubleshooter",
        "http_redirect_status": "HTTP Redirect Debug Helper",
        "file_upload_s3": "File Upload → S3 Pipeline Helper",
        "streaming_zip": "Streaming ZIP Builder",
        "tar_gzip_stream": "Streaming TAR.GZ Builder",
        "websocket_audio_whisper": "Audio/WebSocket → Transcription Debugger",
        "async_mock_pytest": "Async Tests Mocking Helper",
        "typing_pydantic_fastapi": "FastAPI Typing/OpenAPI Fixer",
        "logging_uvicorn": "Uvicorn Logging Helper",
    }
    return mapping.get(subtopic, f"{subtopic.replace('_', ' ').title()} Helper")


def _bucket_one_liner(subtopic: str) -> str:
    mapping = {
        "meeting_notes_summary": "AI-агент превращает сырой текст встреч (заметки/транскрипт) в краткое резюме и список action items.",
        "oauth_jwt_auth": "AI-агент диагностирует проблемы JWT/OAuth (cookies/bearer/401) и даёт пошаговые фиксы по симптомам.",
        "http_redirect_status": "AI-агент объясняет причины 307/redirect/trailing slash и предлагает точные правки роутов/клиента.",
        "file_upload_s3": "AI-агент собирает правильную схему upload→S3 (multipart/presigned) и ловит типовые ошибки.",
        "streaming_zip": "AI-агент помогает собрать StreamingResponse для ZIP без битых архивов и с отменой запросов.",
        "tar_gzip_stream": "AI-агент подсказывает, как стримить tar/gzip корректно без async-ловушек.",
        "websocket_audio_whisper": "AI-агент диагностирует пайплайн audio-bytes→PCM→Whisper и чинит проблемы 'white noise/quiet music'.",
        "async_mock_pytest": "AI-агент подсказывает, как мокать async context manager/aiter правильно в pytest.",
        "typing_pydantic_fastapi": "AI-агент чинит типизацию, response_model, openapi enums и предупреждения линтеров.",
        "logging_uvicorn": "AI-агент добавляет timestamp/формат логов uvicorn и объясняет конфиги.",
    }
    return mapping.get(subtopic, "AI-агент помогает быстро разобраться с частой болью и даёт конкретные шаги решения.")


def _mvp_plan(subtopic: str) -> List[str]:
    common = [
        "Day 1: FastAPI эндпоинты + простая web-страница демо",
        "Day 2: Парсер входа → структурирование симптомов/контекста",
        "Day 3: Библиотека типовых причин/проверок (rules)",
        "Day 4: Генерация пошагового плана фикса + чек-лист",
        "Day 5: Экспорт результата (Markdown) + копи-кнопки",
        "Day 6: Логи/метрики + хранение истории (sqlite)",
        "Day 7: Мини-лендинг + демо-кейсы + сбор фидбэка",
    ]
    if subtopic in {"meeting_notes_summary"}:
        return [
            "Day 1: /ingest_text + /build_summary_stub + /build_actions_stub",
            "Day 2: Правила: темы/решения/вопросы/след. шаги",
            "Day 3: Экспорт: Markdown + Notion-friendly",
            "Day 4: Шаблоны meeting minutes (standup/1:1/planning)",
            "Day 5: История/папки/теги (sqlite)",
            "Day 6: UI: drag&drop + кнопки summary/actions/risks",
            "Day 7: Лендос + 5 демо-примеров",
        ]
    return common


def _monetization(subtopic: str) -> List[str]:
    if subtopic in {"meeting_notes_summary"}:
        return [
            "Freemium: бесплатно N обработок/день, подписка за безлимит",
            "B2B: рабочие пространства/команды + платные места",
        ]
    return [
        "Freemium: бесплатный базовый анализ + подписка на продвинутые шаблоны",
        "B2B/Teams: платные места + shared workspace",
    ]


def _priority_and_score(count: int, score: float, days_since_activity: float, answered_ratio: float) -> tuple[str, int]:
    """
    Простая эвристика:
    - TYPE_1: свежо (<=45 дней), много сигналов (count>=4) и/или высокая radar score
    - TYPE_2: всё остальное
    """
    base = int(round(score))
    bonus = 0
    if days_since_activity <= 30:
        bonus += 10
    if count >= 5:
        bonus += 10
    if answered_ratio < 0.5:
        bonus += 8

    total = base + bonus
    ptype = "TYPE_1" if (days_since_activity <= 45 and (count >= 4 or total >= 220)) else "TYPE_2"
    return ptype, total


def idea_from_radar_item(item: Dict[str, Any]) -> Idea:
    """
    item — элемент из /radar.
    Превращаем его в Idea без LLM: шаблоны + примеры как Tasks.
    """
    sig = str(item.get("signature", "general|understand|summary|misc|misc"))
    parts = sig.split("|")
    domain = parts[0] if len(parts) > 0 else "general"
    intent = parts[1] if len(parts) > 1 else "understand"
    output_type = parts[2] if len(parts) > 2 else "summary"
    subtopic = parts[3] if len(parts) > 3 else "misc"

    examples = item.get("examples") or []
    tasks: List[Task] = []
    for ex in examples[:5]:
        tasks.append(
            Task(
                intent=intent,
                input_type="text",
                output_type=output_type,
                domain=domain,
                problem_statement=str(ex),
                evidence=[str(ex)],
            )
        )

    title = _bucket_title(subtopic)
    one_liner = _bucket_one_liner(subtopic)

    ptype, final_score = _priority_and_score(
        count=int(item.get("count") or 0),
        score=float(item.get("score") or 0.0),
        days_since_activity=float(item.get("days_since_activity") or 9999.0),
        answered_ratio=float(item.get("answered_ratio") or 1.0),
    )

    return Idea(
        title=title,
        one_liner=one_liner,
        based_on_tasks=tasks,
        mvp_7_days_plan=_mvp_plan(subtopic),
        monetization=_monetization(subtopic),
        score=final_score,
        priority_type=ptype,
    )


def ideas_from_radar(radar_items: List[Dict[str, Any]], limit: int = 10) -> List[Idea]:
    ideas: List[Idea] = []
    for it in radar_items[: max(0, limit)]:
        ideas.append(idea_from_radar_item(it))
    return ideas
