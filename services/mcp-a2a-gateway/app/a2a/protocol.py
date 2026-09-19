"""Minimal Agent2Agent (A2A) interop surface.

Implements the two building blocks needed to demonstrate governed
multi-agent interoperability: an Agent Card (capability discovery document,
analogous to `/.well-known/agent.json` in the A2A spec) and a Task
send/receive lifecycle for delegating work to a remote agent across an
organizational or vendor boundary -- the scenario the JD's "governed
multi-agent integration and interoperability" line points at.
"""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class AgentSkillCard(BaseModel):
    id: str
    name: str
    description: str


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "0.1.0"
    skills: list[AgentSkillCard] = Field(default_factory=list)


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskMessage(BaseModel):
    role: str
    content: str


class A2ATask(BaseModel):
    task_id: str
    state: TaskState
    messages: list[TaskMessage] = Field(default_factory=list)


class A2ATaskRequest(BaseModel):
    skill_id: str
    message: str


class A2AAgentServer:
    """A remote-callable agent endpoint speaking a minimal A2A subset."""

    def __init__(self, card: AgentCard) -> None:
        self.card = card
        self._tasks: dict[str, A2ATask] = {}

    def submit_task(self, request: A2ATaskRequest) -> A2ATask:
        skill_ids = {s.id for s in self.card.skills}
        task_id = str(uuid.uuid4())

        if request.skill_id not in skill_ids:
            task = A2ATask(
                task_id=task_id,
                state=TaskState.FAILED,
                messages=[
                    TaskMessage(role="user", content=request.message),
                    TaskMessage(
                        role="agent",
                        content=f"No such skill '{request.skill_id}' on this agent.",
                    ),
                ],
            )
        else:
            task = A2ATask(
                task_id=task_id,
                state=TaskState.COMPLETED,
                messages=[
                    TaskMessage(role="user", content=request.message),
                    TaskMessage(
                        role="agent",
                        content=f"Skill '{request.skill_id}' executed for: {request.message}",
                    ),
                ],
            )
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> A2ATask | None:
        return self._tasks.get(task_id)


def build_default_a2a_agent(base_url: str = "http://mcp-a2a-gateway:8002") -> A2AAgentServer:
    card = AgentCard(
        name="itsm-triage-agent-remote",
        description=(
            "Remote-callable A2A peer that mirrors the itsm-triage-agent's "
            "read/summarize skills for cross-platform delegation."
        ),
        url=f"{base_url}/a2a",
        skills=[
            AgentSkillCard(
                id="lookup_incident",
                name="Lookup Incident",
                description="Read-only incident lookup.",
            ),
            AgentSkillCard(
                id="summarize_change_risk",
                name="Summarize Change Risk",
                description="Risk-score a proposed change.",
            ),
        ],
    )
    return A2AAgentServer(card)
