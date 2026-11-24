"""Runtime security-chain regression tests."""

import pytest

from x4.agents import AgentRuntime, Task


def test_safe_task_succeeds() -> None:
    runtime = AgentRuntime()
    task = Task(description="List files")
    result = runtime.run(task, action="read", resource="./")
    assert result.success is True
    assert result.audit_id is not None


def test_high_risk_blocked_without_approval() -> None:
    runtime = AgentRuntime(require_approval_for_high_risk=True)
    task = Task(description="Delete something")
    result = runtime.run(task, action="delete", resource="/data")
    assert result.success is False
    assert "Approval required" in (result.error or "")


def test_high_risk_executes_after_exact_approval() -> None:
    runtime = AgentRuntime(require_approval_for_high_risk=True)
    task = Task(description="Delete something")
    runtime.approve(task.id, action="delete", resource="/data")
    result = runtime.run(task, action="delete", resource="/data")
    assert result.success is True
    assert result.audit_id is not None


def test_high_risk_approval_is_one_time() -> None:
    runtime = AgentRuntime(require_approval_for_high_risk=True)
    task = Task(description="Delete something")
    runtime.approve(task.id, action="delete", resource="/data")

    first = runtime.run(task, action="delete", resource="/data")
    second = runtime.run(task, action="delete", resource="/data")

    assert first.success is True
    assert second.success is False
    assert "Approval required" in (second.error or "")


def test_approval_cannot_be_reused_for_another_resource() -> None:
    runtime = AgentRuntime(require_approval_for_high_risk=True)
    task = Task(description="Delete something")
    runtime.approve(task.id, action="delete", resource="/data")

    mismatched = runtime.run(task, action="delete", resource="/secrets")
    attempted_reuse = runtime.run(task, action="delete", resource="/data")

    assert mismatched.success is False
    assert attempted_reuse.success is False
    assert "Approval required" in (mismatched.error or "")
