# Agent telemetry and matched benchmarks

The toolkit does not silently monitor coding sessions. Providers expose usage differently; record explicit, authorized task summaries using templates/attempt.json. No raw prompts, credentials or private transcripts. Missing telemetry remains null. Record all attempts, including failures and timeouts.

Freeze a task protocol (objective, allowed paths, acceptance, budgets, datasets, evaluator hash and human intervention policy) before comparison. Hash that document and record the same protocol_sha256 and base_commit for both variants. Use a fresh isolated checkout for each variant/task/trial, equivalent hardware and budget, and a trusted independent evaluator to determine outcome. Record actual model/harness versions where available. To compare harnesses, match model and settings; to compare models, match harness and settings where possible. Otherwise label the comparison as a combined configuration.

    python tools/agent.py telemetry record --input attempt.json
    python tools/agent.py telemetry export --campaign research-pilot
    python tools/agent.py benchmark compare --campaign research-pilot --baseline codex-high --candidate opencode-high

Telemetry uses a private SQLite DB in AGENT_RULES_HOME/telemetry.sqlite3 (override with --db before subcommand). Each id and campaign/variant/task/trial is unique; exact duplicate records are idempotent. Corrections require a new documented campaign, not silently replacing prior results. Elapsed time includes all work through validated outcome or stop. Track input/output/cache tokens, cost, GPU seconds, interventions, rework and regressions when measured. No automatic provider adapters are assumed; use official usage exports or a trusted site adapter to fill the JSON.

The comparator requires complete matching task/trial pairs and the same baseline/protocol hashes for each pair. It reports acceptance counts and all-attempt elapsed time, plus median paired differences among jointly accepted pairs for metrics observed on both sides. This avoids declaring failed tasks faster or missing tokens free. These are descriptive results, not significance tests; report uncertainty and selection limits. Retain a complete frozen task manifest outside candidate scope to detect tasks omitted from both variants.

Suggested first campaign: 10–20 representative tasks spanning Python research, C++/Rust/Slang/Vulkan kernels, benchmark analysis, bug fixes and documentation. Randomize variant order, repeat for stochastic variance, keep adjudicators blind to variant when feasible, and compare time-to-validated-result, cost and acceptance. Start smaller to establish the procedure. No productivity gains are claimed until measured.
