from __future__ import annotations

from core.models import Task
from core.topic_rules import classify_topic


def extract_task(text: str) -> Task:
    t = (text or "").strip()
    low = t.lower()

    # intent / input / output / domain — оставь свою текущую логику.
    # Ниже пример, если вдруг у тебя максимально простой extractor.
    intent = "understand"
    input_type = "text"
    output_type = "summary"
    domain = "general"

    # ---- ТУТ ВАЖНОЕ ИЗМЕНЕНИЕ ----
    topic = classify_topic(t)

    return Task(
        intent=intent,
        input_type=input_type,
        output_type=output_type,
        domain=domain,
        problem_statement=t,
        evidence=[t],
        topic=topic,  # если у тебя поле topic есть в Task
    )
