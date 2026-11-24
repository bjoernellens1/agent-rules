# Research and GPU engineering

- Formulate falsifiable hypotheses and predeclare metrics, datasets, seeds, baselines, budgets and stop rules. Protect evaluator code, held-out data and thresholds from candidate agents; enforce with separate read-only inputs or reviewer-controlled checkout where possible.
- Escalate E0 feasibility -> E1 small real run -> E2 controlled ablation -> E3 multi-scene/seed confirmation -> E4 sealed publication evaluation. Stop or revise failed hypotheses; retain negative results.
- Always compare time-to-quality for performance research: matched wall clock, quality thresholds, latency distributions, memory, compute, and failures. Distinguish throughput from latency, amortized batch rates from individual latency, and online from offline.
- Use relevant strong external baselines; match hardware, settings, input availability, budget and evaluation. Document deviations. Do not tune on sealed data or use future observations in causal experiments.
- Verify actual GPU execution, numerical correctness, synchronization and gradients where relevant. Record hardware, driver, backend, source revision, dependencies/model revisions, config/dataset fingerprints, seeds, commands and artifacts.
- Prefer portable interfaces and vendor-independent implementations; optional vendor-specific accelerations must preserve correctness and have fallbacks. Do not infer performance parity across untested backends.
- In reconstruction, distinguish observed, inferred and generated content. Preserve verified accumulated geometry, observations and optimizer state where appropriate; correct invalid predictions without resetting valid evidence. Predictions are not independent physical measurements.
- For mapping, compare matched RGB, depth and TSDF renders as appropriate, metric geometry, coverage, false surfaces, causal timing and downstream utility. Include failure cases and inspect renders, not only metrics.
- Keep experiment tooling and regression suites representative and compact. Use local/remote scheduler resource leases to prevent benchmark contamination. Record cold/warm conditions, outliers, failures and interruptions.
- Passing unit tests is necessary where applicable but not sufficient for a scientific claim. Report evidence strength, uncertainty and generalization limits; distinguish prototype, confirmed result and publication-ready claim.
