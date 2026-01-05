from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field, AliasChoices, ConfigDict


class Task(BaseModel):
    intent: str
    input_type: str
    output_type: str
    domain: str
    problem_statement: str
    evidence: List[str]


class Idea(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    one_liner: str
    based_on_tasks: List[Task]
    mvp_7_days_plan: List[str]
    monetization: List[str]
    score: int

    # принимает И 'priority_type', И старое 'type'
    priority_type: str = Field(
        validation_alias=AliasChoices("priority_type", "type"),
        serialization_alias="priority_type",
    )
