"""Reproducible microbenchmark for the x4 agent policy engine.

Measures policy evaluation, the check that runs before every agent action, and
compares it against a naive linear scan of the same rule list.

    python bench/bench_policy.py
    python bench/bench_policy.py --json
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x4.agents.policy import PolicyEngine

ITERATIONS = 20_000
SAMPLES = 7
GATES = {
    "policy_evaluate_safe": {"kind": "budget", "budget_ns": 4000},
    "policy_evaluate_high_risk": {"kind": "budget", "budget_ns": 5000},
}


def time_call(fn, iterations: int, samples: int) -> float:
    times = []
    for _ in range(samples):
        start = time.perf_counter()
        for _ in range(iterations):
            fn()
        times.append((time.perf_counter() - start) / iterations)
    return statistics.median(times)


engine = PolicyEngine()
_naive_rules = ["delete", "rm", "drop", "shutdown", "exec_raw"]


def safe_decision():
    return engine.evaluate("read", "repo:x4")


def naive_safe_decision():
    action = "read"
    action_lower = action.lower()
    for risky in _naive_rules:
        if risky in action_lower:
            return False
    return True


def risky_decision():
    return engine.evaluate("delete", "repo:x4")


def naive_risky_decision():
    action = "delete"
    action_lower = action.lower()
    for risky in _naive_rules:
        if risky in action_lower:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    args = parser.parse_args()

    cases = [
        ("policy_evaluate_safe", safe_decision, naive_safe_decision),
        ("policy_evaluate_high_risk", risky_decision, naive_risky_decision),
    ]

    results, failures = [], []
    for name, subject, naive in cases:
        fast = time_call(subject, args.iterations, SAMPLES)
        slow = time_call(naive, args.iterations, SAMPLES)
        speedup = slow / fast if fast else 0.0
        gate = GATES[name]
        ns = fast * 1e9
        ok = ns <= gate["budget_ns"]
        if not ok:
            failures.append(f"{name}: {ns:.0f} ns/op exceeds {gate['budget_ns']} ns/op")
        results.append(
            {
                "case": name,
                "iterations": args.iterations,
                "subject_seconds_per_op": round(fast, 9),
                "naive_seconds_per_op": round(slow, 9),
                "subject_ops_per_second": round(1 / fast) if fast else None,
                "measured_speedup_vs_naive": round(speedup, 2),
                "gate": f"<= {gate['budget_ns']} ns/op",
                "pass": ok,
            }
        )

    report = {
        "repo": "x4-agents",
        "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "results": results,
        "passed": not failures,
        "failures": failures,
        "note": "Speedup column is informational; the gate is an absolute latency budget.",
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"x4-agents benchmark · Python {report['python']} · {report['platform']}")
        for row in results:
            print(
                f"{row['case']:<28}{row['subject_ops_per_second']:>12,} ops/s"
                f"{row['subject_seconds_per_op'] * 1e9:>9.0f} ns"
                f"  {'PASS' if row['pass'] else 'FAIL'}"
            )
        print("\nAll gates met." if not failures else "\n" + "\n".join(failures))

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
