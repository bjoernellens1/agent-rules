---
name: experiment
description: Run bounded CPU/GPU experiments, collect evidence and compare matched baselines.
---

# experiment

Read research profile if relevant. Freeze protocol and protected gates; record source, dataset/evaluator hashes, hardware, seeds and budget in context. Start with a small real screening run, then ablate/confirm. Allocate resources externally, use fresh run directories, invoke runner, inspect logs/artifacts and verify receipt. Compare matched runs; retain negative results, outliers and contaminated samples. Do not declare a GPU run from CPU tests or infer validity from a receipt alone.

For time-to-quality, record curve.json with real elapsed timestamps and use the curve command; report thresholds not reached rather than inventing convergence.
