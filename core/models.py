from __future__ import annotations

from typing import List
from pydantic import BaseModel


class Task(BaseModel):
    intent: str
    input_type: str
    output_type: str
    domain: str
    problem_statement: str
    evidence: List[str]


class Idea(BaseModel):
    title: str
    one_liner: str
    based_on_tasks: List[Task]
    mvp_7_days_plan: List[str]
    monetization: List[str]
    score: int
    priority_type: str  # TYPE_1 / TYPE_2
