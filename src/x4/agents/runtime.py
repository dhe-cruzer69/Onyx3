"""Agent runtime with policy → risk → approval → audit chain."""

from __future__ import annotations

from x4.agents.audit import AuditLog
from x4.agents.models import Task, TaskResult
from x4.agents.policy import PolicyEngine


class AgentRuntime:
    """Minimal secure agent runtime with scoped one-use approvals."""

    def __init__(self, require_approval_for_high_risk: bool = True) -> None:
        self.policy = PolicyEngine()
        self.audit = AuditLog()
        self.require_approval_for_high_risk = require_approval_for_high_risk
        self._approvals: dict[str, tuple[str, str]] = {}

    def approve(self, task_id: str, *, action: str, resource: str) -> None:
        """Approve one exact high-risk task action/resource pair."""
        if not task_id.strip() or not action.strip() or not resource.strip():
            raise ValueError("task_id, action and resource are required for approval")
        self._approvals[task_id] = (action.casefold(), resource)

    def run(self, task: Task, action: str = "read", resource: str = ".") -> TaskResult:
        decision = self.policy.evaluate(action, resource)
        approval = self._approvals.pop(task.id, None) if decision.requires_approval else None
        approved = approval == (action.casefold(), resource)

        if decision.requires_approval and self.require_approval_for_high_risk and not approved:
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

        if not decision.allowed and not (decision.requires_approval and approved):
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

        # Simulated successful execution. Replace with a governed executor before
        # claiming this runtime performs real filesystem or process operations.
        audit_id = self.audit.record(
            action=action,
            actor="agent",
            resource=resource,
            allowed=True,
            risk=decision.risk.value,
            details={"task": task.description, "approval_used": approved},
        )
        return TaskResult(
            task_id=task.id,
            success=True,
            output=f"Executed: {task.description}",
            audit_id=audit_id,
        )
