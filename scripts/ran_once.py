"""
Demonstration script for the hunter-agent project.

This script performs a manual, one-off execution of the hunter-agent
pipeline to show how raw text inputs can be transformed into structured
Task objects and then aggregated into Idea objects. It uses the data
models defined in core.models and hard-coded examples to avoid any
external dependencies or machine learning.

Running this script will print the list of tasks followed by the list
of ideas to the console.
"""

from __future__ import annotations

from typing import List

from core.models import Task, Idea


def create_tasks(raw_inputs: List[str]) -> List[Task]:
    """Convert raw textual descriptions into Task objects.

    The mapping from text to structured fields is hard-coded and based
    on simple keyword checks. This is sufficient for a demonstration
    without involving any external services or complex logic.

    Args:
        raw_inputs: A list of human-provided problem statements.

    Returns:
        A list of Task instances corresponding to the inputs.
    """
    tasks: List[Task] = []
    for text in raw_inputs:
        lower = text.lower()
        if "calories" in lower:
            tasks.append(
                Task(
                    intent="evaluate",
                    input_type="image",
                    output_type="score",
                    domain="health",
                    problem_statement="Determine the calorie count from a food photo.",
                    evidence=[text],
                )
            )
        elif "plant" in lower:
            tasks.append(
                Task(
                    intent="identify",
                    input_type="image",
                    output_type="summary",
                    domain="nature",
                    problem_statement="Identify a plant and determine if it is dangerous.",
                    evidence=[text],
                )
            )
        elif "summarize" in lower:
            tasks.append(
                Task(
                    intent="summarize",
                    input_type="text",
                    output_type="summary",
                    domain="general",
                    problem_statement="Summarize a long article or document.",
                    evidence=[text],
                )
            )
        elif "outfit" in lower or "formal event" in lower:
            tasks.append(
                Task(
                    intent="compare",
                    input_type="image",
                    output_type="recommendation",
                    domain="fashion",
                    problem_statement="Compare outfit choices for a formal event.",
                    evidence=[text],
                )
            )
        elif "translate" in lower and "french" in lower:
            tasks.append(
                Task(
                    intent="translate",
                    input_type="text",
                    output_type="translation",
                    domain="language",
                    problem_statement="Translate a paragraph into French.",
                    evidence=[text],
                )
            )
        else:
            # Fallback for any unrecognized patterns
            tasks.append(
                Task(
                    intent="unknown",
                    input_type="text",
                    output_type="summary",
                    domain="misc",
                    problem_statement=text,
                    evidence=[text],
                )
            )
    return tasks


def create_ideas(tasks: List[Task]) -> List[Idea]:
    """Group tasks into one or two idea objects.

    This function aggregates related tasks and defines a high-level
    minimum viable product (MVP) plan for each idea. It uses simple
    heuristics to group tasks by input type and domain. Scores and
    priority types are arbitrary for demonstration purposes.

    Args:
        tasks: The list of Task instances created from user inputs.

    Returns:
        A list containing one or two Idea instances.
    """
    # Separate tasks by whether they involve images or text
    image_tasks = [t for t in tasks if t.input_type == "image"]
    text_tasks = [t for t in tasks if t.input_type == "text"]

    ideas: List[Idea] = []

    if image_tasks:
        ideas.append(
            Idea(
                title="Visual Helper AI",
                one_liner="An AI agent that processes images to estimate calories, identify plants, and offer fashion advice.",
                based_on_tasks=image_tasks,
                mvp_7_days_plan=[
                    "Day 1: Define data models and input/output formats.",
                    "Day 2: Collect a small sample dataset for food, plants, and outfits.",
                    "Day 3: Implement simple image upload and display in the web interface.",
                    "Day 4: Integrate basic image analysis stubs for calories, plant ID, and outfit comparison.",
                    "Day 5: Develop a scoring and recommendation mechanism.",
                    "Day 6: Build a simple UI to present results to users.",
                    "Day 7: Test end-to-end flow and gather feedback.",
                ],
                monetization=[
                    "Freemium model with paid access to detailed analyses.",
                    "Partner with nutrition and fashion brands for sponsorships.",
                ],
                    score=8,
                type="TYPE_1",
            )
        )

    if text_tasks:
        ideas.append(
            Idea(
                title="Text Assistant AI",
                one_liner="An AI assistant that summarizes articles and translates text.",
                based_on_tasks=text_tasks,
                mvp_7_days_plan=[
                    "Day 1: Finalize models and skeleton of the summarization/translation pipeline.",
                    "Day 2: Prepare sample text inputs for summarization and translation.",
                    "Day 3: Implement basic summarization and translation stubs.",
                    "Day 4: Create an API endpoint to process text requests.",
                    "Day 5: Build a front-end form to submit text and view results.",
                    "Day 6: Add logging and error handling.",
                    "Day 7: Test the pipeline and document next steps.",
                ],
                monetization=[
                    "Subscription for unlimited usage.",
                    "Per-use fee for premium translations.",
                ],
                score=6,
                type="TYPE_2",
            )
        )

    return ideas


def main() -> None:
    """Run the demonstration pipeline and print results."""
    raw_inputs = [
        "How many calories are in this food photo?",
        "What is this plant and is it dangerous?",
        "Summarize this long article for me",
        "Which outfit looks better for a formal event?",
        "Translate this paragraph into French",
    ]

    tasks = create_tasks(raw_inputs)
    ideas = create_ideas(tasks)

    print("Tasks:")
    for idx, task in enumerate(tasks, start=1):
        # Print a brief summary of each task
        summary = {
            "intent": task.intent,
            "input_type": task.input_type,
            "output_type": task.output_type,
            "domain": task.domain,
            "problem_statement": task.problem_statement,
        }
        print(f"  {idx}. {summary}")

    print("\nIdeas:")
    for idx, idea in enumerate(ideas, start=1):
        print(f"  Idea {idx}:")
        print(f"    Title: {idea.title}")
        print(f"    One-liner: {idea.one_liner}")
        print(f"    Based on {len(idea.based_on_tasks)} tasks")
        print("    MVP 7-day plan:")
        for step in idea.mvp_7_days_plan:
            print(f"      - {step}")
        print("    Monetization:")
        for model in idea.monetization:
            print(f"      - {model}")
        print(f"    Score: {idea.score}")
        print(f"    Priority Type: {idea.type}")


if __name__ == "__main__":
    main()
