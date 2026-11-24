---
name: experiment
description: Run bounded CPU/GPU experiments, collect evidence and compare matched baselines.
---

# experiment

Read research profile if relevant. Freeze protocol and protected gates; record source, dataset/evaluator hashes, hardware, seeds and budget in context. Start with a small real screening run, then ablate/confirm. Allocate resources externally, use fresh run directories, invoke runner, inspect logs/artifacts and verify receipt. Compare matched runs; retain negative results, outliers and contaminated samples. Do not declare a GPU run from CPU tests or infer validity from a receipt alone.

For time-to-quality, record curve.json with real elapsed timestamps and use the curve command; report thresholds not reached rather than inventing convergence.

For local parallel jobs use a consistent cooperative device lease; use the scheduler plan before authorized cluster submission. Verify actual allocation and GPU use independently. Keep candidate and sealed evaluator separate using the sandbox/cluster adapter and real permissions. Record measured task and GPU telemetry without guessing missing values.
