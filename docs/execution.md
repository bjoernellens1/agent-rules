# Execution and evidence

Run commands as argument vectors, not implicit shell scripts. A shell may be explicitly selected by the operator. Worktree identity is recorded before and after execution; clean source is required by default. Use --allow-dirty for exploratory runs only. A dirty or changed source is not eligible for matched comparison.

Run from the candidate checkout. Choose a fresh absolute output path outside the checkout or explicitly Git-ignore it. The runner sets AGENT_RUN_DIR for the child; the benchmark writes metrics.json there as a flat JSON object of finite numeric values. Other artifacts are application-owned. The receipt verifies the log, context, metrics and optional curve checksums, not every possible external artifact. Independent evaluators should validate metric provenance and all relevant external evidence.

Context JSON is explicit and identical for matched comparisons (copy templates/context.json and fill it with real values). Include dataset/split identity and hashes, evaluator hash, hardware/driver, software/backend, seeds, compute budget, protocol and warmup. The comparator requires exact context and runner-version equality, a successful clean unchanged source run and finite metrics. It reports candidate-minus-baseline deltas. Optional gate JSON supports min/max and min_delta/max_delta per metric. Missing values or failed gates are not a pass. The gate file itself is not access-controlled by the CLI; keep it in an evaluator-controlled checkout.

## Local commands

    python tools/agent.py run --out /tmp/run-01 --context context.json --timeout 120 -- python benchmark.py
    python tools/agent.py run --detach --out /tmp/run-02 --context context.json --timeout 120 -- python benchmark.py
    python tools/agent.py status /tmp/run-02
    python tools/agent.py logs /tmp/run-02 --lines 30
    python tools/agent.py verify /tmp/run-02 --require-metrics
    python tools/agent.py compare /tmp/run-01 /tmp/run-02 --gates gates.json

Detached jobs use a local independent Python process. They are not automatically scheduled, restarted, resumed, or GPU-isolated. Timeout terminates the process group on POSIX; on Windows it terminates the direct child only. A crashed supervisor can leave a running/pending receipt; investigate externally rather than treating it as successful. The CLI does not cancel or recover arbitrary processes. Explicitly allocate resources and prevent concurrent jobs on the same device when comparing latency. No automatic cloud provisioning or spending.

## Remote/cluster adapter contract (not implemented)

Use existing SSH, Kubernetes/Kai/Hera, Slurm or an equivalent scheduler. A site adapter should expose submit, status, logs, fetch, cancel and resource accounting. Submit an immutable commit/image, explicit GPU/device/CPU/memory/time budget and read-only evaluator/data mounts. Execute the same run command on the allocated worker, persist results to a durable volume, then retrieve the receipt and logs. Make retries idempotent and never silently reuse stale runs. Resume belongs to the underlying benchmark/checkpoint protocol, not this CLI.

For production jobs use least-privilege identities, resource quotas and no blanket remote shell trust. GPU allocation and actual device use must be verified from scheduler/runtime evidence.

## Time-to-quality

A benchmark can additionally write curve.json in AGENT_RUN_DIR, e.g. {"psnr":[{"t_s":0,"value":10},{"t_s":12,"value":25}]}. Record real elapsed wall-clock timestamps from a consistent start boundary, without future-data leakage. The curve command compares first observed threshold crossings (ge by default; use --direction le for decreasing error). Missing crossings are null; no extrapolation or artificial terminal points. Inspect stability, sampling frequency and censored runs before claiming a speedup. The command checks artifact integrity, not the physical accuracy of the timestamps.
