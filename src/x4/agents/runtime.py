"""Agent runtime with policy → risk → approval → audit chain."""

from __future__ import annotations

from x4.agents.audit import AuditLog
from x4.agents.models import Task, TaskResult
from x4.agents.policy import PolicyEngine


class AgentRuntime:
    """Minimal secure agent runtime."""

    def __init__(self, require_approval_for_high_risk: bool = True) -> None:
        self.policy = PolicyEngine()
        self.audit = AuditLog()
        self.require_approval_for_high_risk = require_approval_for_high_risk
        self._approvals: dict[str, bool] = {}

    def approve(self, action_id: str) -> None:
        self._approvals[action_id] = True

    def run(self, task: Task, action: str = "read", resource: str = ".") -> TaskResult:
        decision = self.policy.evaluate(action, resource)

        if (
            decision.requires_approval
            and self.require_approval_for_high_risk
            and not self._approvals.get(task.id, False)
        ):
            audit_id = self.audit.record(
                action=action,
                actor="agent",
                resource=resource,
                allowed=False,
                risk=decision.risk.value,
                details={"reason": decision.reason, "task": task.description},
            )
            return TaskResult(
                task_id=task.id,
                success=False,
                error=f"Approval required: {decision.reason}",
                audit_id=audit_id,
            )

        if not decision.allowed:
            audit_id = self.audit.record(
                action=action,
                actor="agent",
                resource=resource,
                allowed=False,
                risk=decision.risk.value,
                details={"reason": decision.reason},
            )
            return TaskResult(
                task_id=task.id,
                success=False,
                error=decision.reason,
                audit_id=audit_id,
            )

        # Simulated successful execution
        audit_id = self.audit.record(
            action=action,
            actor="agent",
            resource=resource,
            allowed=True,
            risk=decision.risk.value,
            details={"task": task.description},
        )
        return TaskResult(
            task_id=task.id,
            success=True,
            output=f"Executed: {task.description}",
            audit_id=audit_id,
        )
