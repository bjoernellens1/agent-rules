# agent-rules

Reusable, evidence-driven engineering for coding agents and scientific software. Optimize **time to validated results**, not lines of code, test counts or agent activity.

Use with any harness that can read Markdown and run Python: OpenCode, Codex, Claude Code, Antigravity or a future agent. No provider credentials, LLM dependency, paid service or mandatory multi-agent framework.

## Install

**[Human installation guide](INSTALL.md) · [Coding-agent installation contract](AGENT_INSTALL.md)**

To adopt the toolkit, give your coding agent this instruction:

> Install https://github.com/bjoernellens1/agent-rules in this repository, following INSTALL.md and AGENT_INSTALL.md. Use the appropriate profile, preserve existing rules, preview and verify the installation, and report the pinned revision.

## Quick start

Requires Python 3.10+ and Git.

    git clone https://github.com/bjoernellens1/agent-rules.git
    cd agent-rules
    python tools/agent.py install --target /path/to/project --profile research
    python tools/agent.py install --target /path/to/project --profile research --check

Review and commit the generated files in the target project. Use a known toolkit commit for repeatable installs. The installer preserves non-managed AGENTS.md text, checks for local changes to managed files, and refuses conflicts. It does not change your global configuration, existing Git history, or cloud infrastructure. Choose profile core for general software; research adds scientific/GPU requirements. For harnesses that do not automatically read AGENTS.md, explicitly instruct them to load it at session start; see docs/harnesses.md.

From the target project:

    python .agent-rules/agent.py doctor
    python .agent-rules/agent.py task new optimizer-screen --objective "Reduce time to quality"
    python .agent-rules/agent.py task worktree optimizer-screen --path /path/to/isolated-checkout --base HEAD
    python .agent-rules/agent.py scope --contract /path/to/frozen-scope.json
    python .agent-rules/agent.py learn --inbox .agent-work/knowledge.jsonl --finding "..." --evidence "commit/run/path" --scope optimizer

The run CLI records real command execution, revision, exit status, elapsed time, context and artifact checksums. The runner itself is not an independent proof of scientific validity. Optional scheduler adapters provide bounded local and Kubernetes/Argo execution.

    python .agent-rules/agent.py run --out /tmp/screen-001 --context context.json --timeout 120 -- python benchmark.py
    python .agent-rules/agent.py status /tmp/screen-001
    python .agent-rules/agent.py verify /tmp/screen-001 --require-metrics
    python .agent-rules/agent.py compare /tmp/base-001 /tmp/screen-001 --gates gates.json
    python .agent-rules/agent.py curve /tmp/base-001 /tmp/screen-001 --metric psnr --threshold 25

Context must be identical across matched runs. Commands can write numeric metrics to the metrics.json file in the AGENT_RUN_DIR environment variable. Output directories must be outside the checkout or Git-ignored. Never include credentials or private data in commands, contexts, logs or shared receipts. Use a fresh output directory per run. See docs/execution.md.

## Lifelong learning

Every non-obvious validated finding must update the relevant repository and be recorded with evidence. Generalizable improvements must be proposed upstream in this toolkit. Permanent rules stay small; scoped facts, decisions, lessons, procedures and negative results go into a private shared SQLite knowledge store.

    python .agent-rules/agent.py knowledge add --project sceneweave --topic depth/scale --body "REPLACE with verified finding" --evidence "REPLACE with actual evidence"
    python .agent-rules/agent.py knowledge maintain --project sceneweave
    python .agent-rules/agent.py knowledge proposals --project sceneweave
    python .agent-rules/agent.py knowledge search --project sceneweave --include-global --query "depth scale" --budget 6000

Observations are deduplicated, curated into proposals, reviewed, versioned and recalled selectively. Approved knowledge can be written back into Git-safe Markdown using a preview and explicit confirmation. See [knowledge and learning](docs/learning.md). Do not seed real memory with placeholder example claims.

## Optional execution and agent evaluation

    python .agent-rules/agent.py scheduler plan --spec scheduler.json
    python .agent-rules/agent.py sandbox plan --spec sandbox.json
    python .agent-rules/agent.py project list --config project.json
    python .agent-rules/agent.py telemetry record --input attempt.json
    python .agent-rules/agent.py benchmark compare --campaign trial --baseline baseline --candidate candidate

Use the supplied templates and read [scheduler and isolation](docs/adapters.md), [agent benchmarks](docs/telemetry.md). Commands with external effects require explicit confirmation. No credentials, cluster or model providers are configured by installation.

## What's here

| Location | Purpose |
|---|---|
| rules/core.md | Short universal instructions, embedded in managed AGENTS.md block |
| rules/research.md | Scientific and GPU engineering profile |
| skills/ | On-demand procedures, each with SKILL.md |
| templates/ | Task, run context, gates, handoff and report starting points |
| docs/ | Workflow, harness integration, execution, learning, sources |
| tools/agent*.py | Core CLI, lifelong knowledge, scheduler/evaluator/project adapters, telemetry and paired agent benchmarks |
| tests/ | Dependency-free regression tests |
| examples/ | Small executable end-to-end example |

## Design

- One coordinator, one owner per writable component. Scale workers only when tasks are independent.
- Protect evaluators, datasets and acceptance criteria outside the candidate's write scope.
- Test the cheapest falsifiable experiment first; retain negative results and expand only when warranted.
- Every accepted result includes reproducible evidence. Every failed experiment yields reusable knowledge.
- Keep skills on demand, permanent rules small, and agent memory subordinate to validated source and evidence.

See [workflow](docs/workflow.md), [learning](docs/learning.md), [execution](docs/execution.md), [harnesses](docs/harnesses.md) and [inspiration](docs/sources.md).

## Scope

V2 includes local cooperative leases/cancellation, Kubernetes Job and Argo Workflow adapters, container isolation plans, knowledge curation and exchange, repository writeback, project manifests, and explicit telemetry/benchmark analysis. Real cluster, GPU, container-runtime and LLM-provider integration require site credentials, trusted immutable inputs and authorized smoke runs. Adapter planning/tests are not evidence of production deployment. See [roadmap](docs/roadmap.md).

## Development

    python -m unittest discover -s tests -v

Review the installed files and the source revision before applying updates to any project. This repository does not assign a software license yet; a license decision belongs to the maintainer.
