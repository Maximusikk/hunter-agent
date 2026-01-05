from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.models import Idea, Task
from core.labels import classify_need
from core.subtopics import pick_subtopic
from core.market_scan import run_market_scan


def _priority_from_score(score: int) -> str:
    return "TYPE_1" if score >= 60 else "TYPE_2"


def _mvp_plan_for(label: str) -> List[str]:
    if label == "workflow_time_saver":
        return [
            "Day 1: Определить UX и форматы входа/выхода, сделать минимальный UI + FastAPI",
            "Day 2: Добавить ingestion (текст/файлы) + хранение истории (sqlite/файлы)",
            "Day 3: Реализовать 1–2 ключевых сценария (stubs/правила)",
            "Day 4: Экспорт (Markdown/копирование/шаблоны) + горячие кнопки",
            "Day 5: Улучшить UX: быстрые пресеты, авто-детект структуры",
            "Day 6: Мини-лендинг + демо примеры + логирование",
            "Day 7: Тестирование + сбор фидбэка",
        ]
    if label == "decision_preview":
        return [
            "Day 1: UX + формат задачи + сбор 30 примеров",
            "Day 2: Простейший пайплайн оценки (правила/метрики)",
            "Day 3: UI + API + хранение истории",
            "Day 4: Качество: подсказки, ограничения, объяснимость",
            "Day 5: Экспорт/шаринг",
            "Day 6: Лендос + демо",
            "Day 7: Тесты + фидбэк",
        ]
    return [
        "Day 1: Быстрый MVP: UI + API",
        "Day 2: 1 основной сценарий",
        "Day 3: Улучшение UX",
        "Day 4: Экспорт/шаринг",
        "Day 5: Лендос",
        "Day 6: Тесты",
        "Day 7: Фидбэк",
    ]


def _monetization_for(label: str) -> List[str]:
    if label in {"workflow_time_saver", "decision_preview"}:
        return ["Freemium + подписка", "Платные пакеты/лимиты"]
    return ["Freemium"]

def _topic_for_search(topic: str) -> str:
    t = (topic or "").lower()
    t = t.replace("tags:", "").replace("q:", "")
    t = t.replace("+", " ")
    return t.strip()

def ideas2_from_clusters(
    clusters: List[Dict],
    min_count: int = 3,
    per_cluster_limit: int = 3,
    market_results_per_query: int = 6,
) -> List[Idea]:
    """
    clusters: from /clusters (each has: topic, count, examples, domain, intent, output_type)
    We split each cluster into subtopics, scan market, score, return top ideas.
    """
    ideas: List[Idea] = []

    for c in clusters:
        if c.get("count", 0) < min_count:
            continue

        examples: List[str] = c.get("examples") or []
        topic = c.get("topic") or "misc"
        domain = c.get("domain") or "general"

        # subtopic buckets
        sub: Dict[str, List[str]] = {}
        for ex in examples:
            label = pick_subtopic(ex, tags=None, query=None)
            sub.setdefault(label, []).append(ex)

        # take top subtopics by frequency (within examples)
        sub_sorted = sorted(sub.items(), key=lambda kv: len(kv[1]), reverse=True)[:per_cluster_limit]

        for subtopic, ex_list in sub_sorted:
            # classify need label based on concatenated text
            joined = " ".join(ex_list[:3])
            need_label = classify_need(joined)

            # skip pure "support_fix" when you want monetizable pet projects
            # (you can relax this later)
            if need_label == "support_fix":
                continue

            # market scan query: coarse topic + subtopic + domain
            topic_clean = _topic_for_search(topic)
            query = f"{domain} {topic_clean} {subtopic} app tool"

            scan = run_market_scan(query=query, max_results=market_results_per_query)

            # score: mass (cluster count) + label boost - competition penalty
            mass = int(c.get("count", 0))
            label_boost = 25 if need_label == "workflow_time_saver" else 15
            competition_penalty = scan.competition_score * 5

            score = mass * 4 + label_boost - competition_penalty

            title = f"{subtopic.replace('_', ' ').title()} ({topic})"
            one_liner = f"Инструмент/агент решает: {subtopic.replace('_', ' ')}. Вердикт рынка: {scan.verdict}."

            # tasks from examples (simple: Task objects with statement + evidence)
            tasks: List[Task] = []
            for ex in ex_list[:5]:
                tasks.append(
                    Task(
                        intent="understand",
                        input_type="text",
                        output_type="summary",
                        domain=domain,
                        problem_statement=ex,
                        evidence=[ex],
                    )
                )

            ideas.append(
                Idea(
                    title=title,
                    one_liner=one_liner,
                    based_on_tasks=tasks,
                    mvp_7_days_plan=_mvp_plan_for(need_label),
                    monetization=_monetization_for(need_label),
                    score=int(score),
                    priority_type=_priority_from_score(int(score)),
                )
            )

    ideas.sort(key=lambda i: i.score, reverse=True)
    return ideas
