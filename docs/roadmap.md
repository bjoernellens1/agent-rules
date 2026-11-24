# Roadmap

Implemented in the initial version: distributable core/research policies, on-demand skills, templates, non-destructive installer, local doctor/task creation, bounded synchronous/detached local command execution, receipt verification, matched metrics comparison/gates, and append-only findings.

Next, after real use on a small project:

- Add a scheduler adapter for existing K3s/Kai/Hera infrastructure and site-specific local GPU runners; include leases, cancellation, artifact sync and actual resource accounting.
- Integrate immutable evaluator and data artifacts with independent write permissions; enforce gates in CI or a trusted evaluator.
- Add task-level telemetry (model/harness/version, token counts, costs, wall clock) and matched agent benchmarks; do not hardcode model rankings.
- Implement optional memory curation with explicit user approval, source citations, locking and reversible changes.
- Add repository-specific adapter manifests for commands, GPU probes and visual QA; avoid embedding project-specific logic in the universal toolkit.
- Trial on one research repo, evaluate time-to-validated-result and context cost, then expand. Use the smallest justified set of new features.

No estimate of productivity uplift is treated as measured until a controlled trial has run.
