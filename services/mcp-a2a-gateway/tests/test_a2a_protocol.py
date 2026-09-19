from __future__ import annotations

from app.a2a.protocol import A2ATaskRequest, TaskState, build_default_a2a_agent


def test_agent_card_lists_skills() -> None:
    agent = build_default_a2a_agent()
    assert len(agent.card.skills) == 2


def test_submit_task_for_known_skill_completes() -> None:
    agent = build_default_a2a_agent()
    task = agent.submit_task(A2ATaskRequest(skill_id="lookup_incident", message="INC0010042?"))
    assert task.state == TaskState.COMPLETED
    assert agent.get_task(task.task_id) is task


def test_submit_task_for_unknown_skill_fails() -> None:
    agent = build_default_a2a_agent()
    task = agent.submit_task(A2ATaskRequest(skill_id="delete_everything", message="do it"))
    assert task.state == TaskState.FAILED


def test_get_unknown_task_returns_none() -> None:
    agent = build_default_a2a_agent()
    assert agent.get_task("does-not-exist") is None
