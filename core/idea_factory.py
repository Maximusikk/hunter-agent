from __future__ import annotations

from typing import List, Dict

from core.models import Task, Idea


def _score_cluster(cluster: Dict) -> int:
    """
    Простой скоринг (потом улучшишь):
    - база = count * 10
    - бонус, если topic явно про работу/процесс (meeting/workflow)
    """
    count = int(cluster.get("count", 0))
    topic = (cluster.get("topic") or "").lower()

    score = count * 10
    if "meeting" in topic or "workflow" in topic or "notes" in topic:
        score += 15
    return score


def _priority_type(score: int) -> str:
    return "TYPE_1" if score >= 35 else "TYPE_2"


def idea_from_cluster(cluster: Dict) -> Idea:
    """
    Делает Idea из одного cluster dict (как у /clusters).
    """
    topic = cluster["topic"]
    domain = cluster["domain"]
    intent = cluster["intent"]
    output_type = cluster["output_type"]
    examples: List[str] = cluster.get("examples", [])

    # Tasks из примеров (демо: считаем input_type=text)
    tasks: List[Task] = [
        Task(
            intent=intent,
            input_type="text",
            output_type=output_type,
            domain=domain,
            problem_statement=ex,
            evidence=[ex],
        )
        for ex in examples
    ]

    # Шаблоны под конкретные топики (быстро расширяется)
    if topic == "meeting_notes_summary":
        title = "Meeting Notes → Action Items"
        one_liner = "AI-агент превращает сырой текст встреч (заметки/транскрипт) в краткое резюме и список action items."
        plan = [
            "Day 1: FastAPI endpoints: /ingest_text, /summarize_stub, /actions_stub + простая UI-страница",
            "Day 2: Парсер структуры: темы/решения/вопросы/следующие шаги (правилами)",
            "Day 3: Экспорт: Markdown + Google Docs / Notion-friendly формат",
            "Day 4: Шаблоны meeting minutes (standup, 1:1, planning) + тональность",
            "Day 5: История/проекты: папки и теги (локально, без базы или sqlite)",
            "Day 6: UX: drag&drop текста, быстрые кнопки 'summary / actions / risks'",
            "Day 7: Мини-лендинг + демо-примеры + сбор фидбэка",
        ]
        monetization = [
            "Freemium: бесплатно 5 обработок/день, подписка для безлимита",
            "B2B: команда/рабочее пространство + платные места",
        ]
    else:
        # общий fallback
        title = f"AI helper for {topic}"
        one_liner = f"AI-агент помогает с задачами типа '{topic}' и выдаёт {output_type}."
        plan = [
            "Day 1: API + простая UI-форма",
            "Day 2: Правила/шаблоны извлечения ключевых пунктов",
            "Day 3: Экспорт результата в удобный формат",
            "Day 4: Улучшение UX и обработка ошибок",
            "Day 5: Тест на 20 примерах",
            "Day 6: Мини-лендинг + демо",
            "Day 7: Сбор фидбэка",
        ]
        monetization = [
            "Freemium + подписка",
        ]

    score = _score_cluster(cluster)
    ptype = _priority_type(score)

    return Idea(
        title=title,
        one_liner=one_liner,
        based_on_tasks=tasks,
        mvp_7_days_plan=plan,
        monetization=monetization,
        score=score,
        priority_type=ptype,  # у тебя сейчас поле type
    )


def ideas_from_clusters(clusters: List[Dict], limit: int = 10) -> List[Idea]:
    # сортируем по score (сначала считаем score для каждого)
    scored = [(c, _score_cluster(c)) for c in clusters]
    scored.sort(key=lambda x: x[1], reverse=True)

    ideas: List[Idea] = []
    for c, _ in scored[:limit]:
        ideas.append(idea_from_cluster(c))
    return ideas
