---
name: plan
description: Plan substantial engineering tasks, parallel work and experiments; skip formal planning for trivial edits.
---

# plan

Inspect actual baseline and prior findings. Fill TASK.md with objective, allowed/protected paths, contracts, dependency graph, budget, acceptance and stop conditions. Assign one writable owner per component and isolate overlapping tasks in worktrees. Freeze evaluation before implementation. For high-risk decisions seek independent review. Choose smallest falsifiable vertical slice.

Use the task worktree and scope commands for isolated changes. Freeze scope.json outside the candidate's write boundary and run scope before integration.
