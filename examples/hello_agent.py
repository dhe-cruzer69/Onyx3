"""Minimal secure agent example."""

from x4.agents import AgentRuntime, Task


def main() -> None:
    runtime = AgentRuntime()

    # Safe action
    task1 = Task(description="Read configuration")
    result1 = runtime.run(task1, action="read", resource="./config.yaml")
    print(f"Safe task: success={result1.success} output={result1.output}")

    # High-risk action without approval
    task2 = Task(description="Delete production data")
    result2 = runtime.run(task2, action="delete", resource="/prod")
    print(f"High-risk blocked: success={result2.success} error={result2.error}")

    # Approve and retry
    runtime.approve(task2.id)
    result3 = runtime.run(task2, action="delete", resource="/prod")
    print(f"After approval: success={result3.success}")

    print(f"Audit events: {len(runtime.audit.list_events())}")

if __name__ == "__main__":
    main()
