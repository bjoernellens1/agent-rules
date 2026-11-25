#!/usr/bin/env python3
"""Advisory resource/finish gate for a bounded autonomous research session."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

TERMINAL = {"done", "rejected", "blocked", "parked"}
STATUSES = TERMINAL | {"pending", "running"}


def now_utc():
    return datetime.now(timezone.utc)


def parse_time(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("start_utc must include a timezone")
    return dt


def check(ledger, now=None):
    now = now or now_utc()
    elapsed = max(0.0, (now - parse_time(ledger["start_utc"])).total_seconds() / 60)
    limit = float(ledger["wall_limit_min"])
    reserve = float(ledger["handover_reserve_min"])
    gpu_limit = float(ledger["gpu_limit_min"])
    gpu_used = float(ledger["gpu_allocated_min"])
    if not (limit > reserve >= 0 and gpu_limit >= 0 and gpu_used >= 0):
        raise ValueError("invalid resource limits or GPU accounting")
    tasks = ledger["tasks"]
    by_id = {t["id"]: t for t in tasks}
    if len(by_id) != len(tasks):
        raise ValueError("duplicate task IDs")
    if len(tasks) > int(ledger.get("task_cap", 36)):
        raise ValueError("task cap exceeded")
    if int(ledger.get("new_paired_screens_started", 0)) > int(ledger.get("paired_screen_cap", 24)):
        raise ValueError("paired screen cap exceeded")
    for t in tasks:
        if t["status"] not in STATUSES:
            raise ValueError(f"{t['id']}: invalid status")
        if t["status"] in TERMINAL and not str(t.get("outcome", "")).strip():
            raise ValueError(f"{t['id']}: terminal status requires outcome/blocker")
        if any(dep not in by_id or dep == t["id"] for dep in t.get("depends_on", [])):
            raise ValueError(f"{t['id']}: invalid dependency")
        if float(t["estimated_wall_min"]) <= 0 or float(t.get("estimated_gpu_min", 0)) < 0:
            raise ValueError(f"{t['id']}: invalid estimate")
    # Reject dependency cycles instead of quietly treating them as a blocked backlog.
    def visit(task_id, stack, seen):
        if task_id in stack:
            raise ValueError(f"dependency cycle at {task_id}")
        if task_id in seen:
            return
        stack.add(task_id)
        for dep in by_id[task_id].get("depends_on", []):
            visit(dep, stack, seen)
        stack.remove(task_id)
        seen.add(task_id)
    seen = set()
    for task_id in by_id:
        visit(task_id, set(), seen)
    productive_left = max(0.0, limit - reserve - elapsed)
    gpu_left = max(0.0, gpu_limit - gpu_used)
    running = [t["id"] for t in tasks if t["status"] == "running"]
    ready = []
    unavailable = {}
    for t in tasks:
        if t["status"] != "pending":
            continue
        if any(by_id[d]["status"] != "done" for d in t.get("depends_on", [])):
            unavailable[t["id"]] = "dependencies not done"
        elif float(t["estimated_wall_min"]) > productive_left:
            unavailable[t["id"]] = "insufficient productive time"
        elif float(t.get("estimated_gpu_min", 0)) > gpu_left:
            unavailable[t["id"]] = "insufficient GPU allocation"
        elif t.get("paired_screen", False) and int(ledger.get("new_paired_screens_started", 0)) >= int(ledger.get("paired_screen_cap", 24)):
            unavailable[t["id"]] = "paired screen cap reached"
        else:
            ready.append(t["id"])
    # A real emergency can stop productive work, but the ledger must account for owned writers.
    emergency = str(ledger.get("emergency_stop_reason", "")).strip()
    review = str(ledger.get("early_finish_backlog_review", "")).strip()
    if running:
        reason, allowed = "owned work still running", False
    elif emergency:
        reason, allowed = "documented emergency stop", True
    elif productive_left <= 0:
        reason, allowed = "handover reserve or deadline reached", True
    elif ready:
        reason, allowed = "runnable authorized backlog remains", False
    elif not review:
        reason, allowed = "early finish requires documented backlog review", False
    else:
        reason, allowed = "no remaining eligible work; early-stop review recorded", True
    return {
        "finish_allowed": allowed, "reason": reason,
        "elapsed_min": round(elapsed, 2), "productive_remaining_min": round(productive_left, 2),
        "gpu_remaining_min": round(gpu_left, 2), "gpu_budget_exceeded": gpu_used > gpu_limit,
        "deadline_exceeded": elapsed > limit, "running": running, "ready": ready,
        "unavailable": unavailable,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["init", "status", "finish"])
    p.add_argument("ledger", type=Path)
    p.add_argument("--minutes", type=float, default=360)
    p.add_argument("--reserve", type=float, default=45)
    p.add_argument("--gpu-minutes", type=float, default=180)
    args = p.parse_args()
    if args.action == "init":
        data = {"start_utc": now_utc().isoformat(), "wall_limit_min": args.minutes,
                "handover_reserve_min": args.reserve, "gpu_limit_min": args.gpu_minutes,
                "gpu_allocated_min": 0, "task_cap": 36, "paired_screen_cap": 24,
                "new_paired_screens_started": 0, "tasks": [],
                "early_finish_backlog_review": "", "emergency_stop_reason": ""}
        check(data)
        with args.ledger.open("x", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        return 0
    data = json.loads(args.ledger.read_text(encoding="utf-8"))
    report = check(data)
    print(json.dumps(report, indent=2))
    return 0 if args.action == "status" or report["finish_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
