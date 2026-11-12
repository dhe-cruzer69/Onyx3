"""Policy and risk classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PolicyDecision:
    allowed: bool
    risk: RiskLevel
    requires_approval: bool
    reason: str


class PolicyEngine:
    """Simple policy engine for agent actions."""

    HIGH_RISK_ACTIONS: ClassVar[set[str]] = {"delete", "rm", "drop", "shutdown", "exec_raw"}

    def evaluate(self, action: str, resource: str = "") -> PolicyDecision:
        action_lower = action.lower()
        if any(risky in action_lower for risky in self.HIGH_RISK_ACTIONS):
            return PolicyDecision(
                allowed=False,
                risk=RiskLevel.HIGH,
                requires_approval=True,
                reason=f"High-risk action requires approval: {action}",
            )
        if action_lower in {"write", "create", "update"}:
            return PolicyDecision(
                allowed=True,
                risk=RiskLevel.MEDIUM,
                requires_approval=False,
                reason="Write action permitted under policy",
            )
        return PolicyDecision(
            allowed=True,
            risk=RiskLevel.LOW,
            requires_approval=False,
            reason="Read/safe action permitted",
        )
