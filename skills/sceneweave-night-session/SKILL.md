---
name: sceneweave-night-session
description: Run bounded, multi-wave autonomous SceneWeave research in isolated parallel worktrees; use the full productive time window through pre-approved evidence-driven follow-ups, without padding, scope creep, unsafe merges, or benchmark contamination.
---

# SceneWeave autonomous research night

## Standing project preferences

A six-hour session is a productive research window, not a single small batch with a six-hour timeout. The 24–25 Nov 2026 session completed in under one hour (reported ~8.5 GPU minutes), leaving most of the intended window unused. For subsequent sessions, prepare roughly six waves of work, with 25–36 bounded experiment/implementation cards available, and replan after every completed wave. Do not force exactly six times the compute or code: progress, not busyness, is the objective.

AGO is a full Gaussian lifecycle, spatial-capacity, optimization, and residency controller, not merely an active-index selector. MST requires physically plausible, causal, geometrically verified object hypotheses. See `references/AGO_ROADMAP.md` and `references/MST_DIAGNOSTICS.md`.

## Start

1. Read the target repository AGENTS.md, optimization contract, experiment policy, testing rules, and current plans. Honor their pre-registration, visual review, cleanup, and pre-push requirements. Inspect all local worktrees, running jobs, current SHAs, and the latest remote state before assigning work. Reuse completed artifacts. Do not interrupt existing workers.
2. Create a session manifest with an actual UTC start, hard deadline, reserved handover interval, resource budget, worker ownership, frozen baseline SHAs, protected datasets, and experiment cards. The coordinator owns this ledger. Use `scripts/night_guard.py` if desired; it is a local advisory finish gate, not an agent orchestrator.
3. Defaults: 360 minutes elapsed, 45 minutes reserved for verification/handover, 180 additional GPU-minutes shared across the session, up to five isolated coding lanes (Core, AGO, MST, Teach, Sense), aggregate CPU threads <=32 on the known workstation. One performance job at a time on a shared GPU; suspend/throttle CPU activity that measurably perturbs timing. Independent devices may be used concurrently only if hardware isolation, memory, power and benchmark comparability are verified. No unattended shared-branch merges. User instructions may override budgets explicitly.
4. Seed a sufficiently deep backlog from `references/BACKLOG.md`: first-wave tasks, dependent follow-ups, independent fallbacks, and final verification. Default cap: 36 substantive cards, at most 24 new paired development screens, one retry per failed mechanism; repository-specific experiment limits still apply. Do not count unit tests or plotting as scientific experiments. Every scored experiment has a pre-registered hypothesis, one changed mechanism, immediate incumbent, fixed inputs, meaningful margin, metrics, runtime budget and kill condition.

## Work in waves, not a single batch

- Launch up to five parallel coding/CPU workers, one branch and worktree per lane; use separate native-engine worktrees/builds where needed. Each worker has an exclusive output directory and exact baseline/config fingerprints. Do not overwrite others' worktrees, shared installs, or artifacts.
- The coordinator checks progress at least every 10 minutes while active; completed cards immediately release dependent cards. A worker whose card finishes early takes the highest-value ready card within its existing lane, or assists verification if its lane is blocked.
- Prioritize P0 scientific integrity, then expected decision value per remaining resource. Prefer cheap L0 checks, then L1 paired screens, then L2 confirmation of meaningful finalists. Use existing `scripts/job.py` preflight, `--prereg`, `--after`, and resumable chunks where supported. Do not launch another run if valid existing artifacts already answer the question.
- Keep the GPU queue busy with useful isolated benchmarks, not just any benchmark. Before scheduling, check predicted completion within the productive window and aggregate GPU budget, memory and live deadlines. Resource estimates are not permission to exceed caps; use job timeouts/limits and account actual GPU allocation time including retries and tests. If timing cannot be isolated, defer the measurement.
- On negative results, park that mechanism, retain the artifact, and advance to the next authorized hypothesis. Do not invent extra architectures or endlessly tune the same candidate. On positive results, use remaining capacity for independent confirmation, ablation, failure-case analysis, stronger baselines, or bounded adjacent work from the pre-approved backlog.
- If all initial tasks finish in an hour, do not issue the final handover solely because the initial list is complete. Reconcile the ledger, activate the next wave, and repeat. Target roughly 80–90% of the productive window when defensible work exists. Idle time and resource exhaustion are tracked, not optimized as scientific metrics.

## Non-negotiable scientific constraints

- Always compare time-to-quality and evidence-to-quality, actual measured geometry, calibration, correction burden, downstream task utility, and resource usage. Optimization steps/s, raw coverage, Gaussian count, model calls, and PSNR alone are not success metrics.
- Use uninterrupted mapping timing with immutable snapshots and offline scoring; account for capture and background work. Do not report an average as p95. Missing or proxy evidence cannot pass a gate. Report per-scene/seed attainment and censored failures.
- No future evidence, unsupported provenance promotion, predicted-as-verified-free certification, or contamination of physical TSDF/occupancy. Keep uncertain predictions retractable. Do not use sealed results to choose parameters, fix algorithms or choose candidates; if a protocol bug is found, invalidate affected claim, document it, and use a fresh pre-registered holdout if needed.
- Keep fixed baseline parity (including shared engine and sensor improvements), matched budgets, documented data/model hashes, and independent physical references. Keep production defaults unchanged until reviewed evidence supports promotion.
- Do not start new unrelated repositories, large downloads, broad training campaigns, or destructive cleanup. Follow repository-specific hooks; never bypass them.

## Finish gate

Enter final verification at the reserved boundary, or earlier only if all in-scope, high-value cards are exhausted, blocked, or cannot fit the remaining budgets. Before early handover, run a backlog review and record concrete reasons, including elapsed time, GPU allocation, remaining cards, and blockers. A first-wave completion is not a finish condition. Never consume extra time merely to reach a utilization target.

No active owned jobs/writers at handover. Do not terminate someone else's work. Complete focused and applicable full tests, cleanup, required visual inspection, plots, animations, and reproducibility checks. Do not mark incomplete testing as a pass. Stop at the hard deadline; preserve unfinished artifacts with clear status. A safety or hardware emergency can end the session at once with a documented reason.

## Morning handover

Produce NIGHT_REPORT.md, NIGHT_MANIFEST.json, exact commands and revisions, per-lane decision cards (GO / NO-GO / INCONCLUSIVE / BLOCKED; screened/confirmed/validated), visual reviews, resource and wave ledger, and at most three next priorities. Record why the session ended, utilization, which planned follow-ups were consumed, and which could not be executed. Push only permitted clean feature branches; draft PRs are acceptable. Do not auto-merge shared integration branches.
