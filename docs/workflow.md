# Workflow

## Complexity-based orchestration

Small changes: one agent, focused edit, relevant verification, brief handoff. Medium changes: one owner, task contract, baseline, scoped test and review if risk warrants it. Large changes: coordinator establishes a dependency graph and shared contracts; delegate only independent work. Start with one or two workers, increase if measured throughput improves. A read-only independent reviewer challenges assumptions and evidence; its findings do not silently mutate the candidate.

Roles are temporary: coordinator/integrator, implementer, researcher, experiment operator, evaluator, curator. A different model family may help independent review but does not guarantee independence. Use a strong model for high-risk reasoning, a coding model for implementation, and inexpensive tools/models for routine summaries. Do not pin global rules to model names.

## Task lifecycle

1. Inspect actual checkout, current running build and prior results. Decide whether planning is needed.
2. For substantial work, fill templates/TASK.md and freeze the evaluation contract. Declare file ownership, protected paths, budget and stop condition.
3. Research compatibility and alternatives only as needed; cite primary sources. Choose a small vertical slice and establish a measured baseline.
4. Run focused implementation/testing in the assigned worktree. For experimental work, follow the escalation funnel in the research profile.
5. Independently inspect diffs and results. Evaluate against the frozen gates, check causality/leakage, provenance, numerical validity and visual output. Choose accept, reject, revise or blocked.
6. Integrate only authorized changes; record evidence and handoff. Capture reusable lessons separately.

## Metrics for the workflow itself

Record elapsed time to validated outcome, LLM input/output/cache tokens when the provider exposes them, agent cost, GPU hours, failures, human interventions, rework and regressions. Treat missing telemetry as unknown, never zero. Compare harnesses on matched tasks, model, time budget and acceptance. Do not reward commit counts, test counts, or token volume.

## Isolation and acceptance

A Markdown rule is guidance, not access control. For consequential runs use distinct candidate and evaluator checkouts, read-only evaluator/data mounts, least-privilege credentials, and a separately controlled acceptance configuration. Freeze evaluator and dataset hashes in run context. Candidate agents may propose revisions, not apply them. The coordinator can accept a negative result as a completed research task without accepting its implementation as an improvement.

## Executable ownership checks

Use task worktree with an explicit base and fresh path outside the current checkout. Use the scope command with a reviewer-controlled copy of templates/scope.json, replacing the base with an immutable commit SHA and allowed/protected paths with actual repository-relative prefixes. The scope tool inspects committed, staged, unstaged and nonignored untracked paths, including both sides of renames. Protected paths override allowed paths. This detects out-of-scope changes at review time, not transient writes or ignored files; enforce real evaluator isolation separately.

## Completion includes repository learning

Before final handoff, run the learn skill: recall relevant prior knowledge, record any durable verified finding in the target repository's authoritative file and the shared knowledge store, and prepare an evidence-backed upstream improvement for general rules, skills, checks or tools. Mark no durable finding or a precise blocker explicitly. A local chat summary alone is not completion. Do not expose private data or weaken protected policies. Prefer a test/tool improvement to repeatedly adding prose.

Recurring validated work must become a reusable skill at three distinct task uses when appropriate. Record uses in the private KB; inventory existing skills; load skill-forge, test the procedure and commit the appropriate canonical skill. If it is deterministic, implement a tool or test and let the skill call it. See docs/skills.md.
