# agent-rules

Reusable, evidence-driven engineering for coding agents and scientific software. Optimize **time to validated results**, not lines of code, test counts or agent activity.

Use with any harness that can read Markdown and run Python: OpenCode, Codex, Claude Code, Antigravity or a future agent. No provider credentials, LLM dependency, paid service or mandatory multi-agent framework.

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
    python .agent-rules/agent.py learn --inbox .agent-work/knowledge.jsonl --finding "..." --evidence "commit/run/path" --scope optimizer

The run CLI records real command execution, revision, exit status, elapsed time, context and artifact checksums. It is not a GPU scheduler or independent proof of scientific validity.

    python .agent-rules/agent.py run --out /tmp/screen-001 --context context.json --timeout 120 -- python benchmark.py
    python .agent-rules/agent.py status /tmp/screen-001
    python .agent-rules/agent.py verify /tmp/screen-001 --require-metrics
    python .agent-rules/agent.py compare /tmp/base-001 /tmp/screen-001 --gates gates.json

Context must be identical across matched runs. Commands can write numeric metrics to the metrics.json file in the AGENT_RUN_DIR environment variable. Output directories must be outside the checkout or Git-ignored. Never include credentials or private data in commands, contexts, logs or shared receipts. Use a fresh output directory per run. See docs/execution.md.

## What's here

| Location | Purpose |
|---|---|
| rules/core.md | Short universal instructions, embedded in managed AGENTS.md block |
| rules/research.md | Scientific and GPU engineering profile |
| skills/ | On-demand procedures, each with SKILL.md |
| templates/ | Task, run context, gates, handoff and report starting points |
| docs/ | Workflow, harness integration, execution, learning, sources |
| tools/agent.py | Installer, doctor, task, run, status, logs, verify, compare, learn |
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

Initial toolkit: local execution and safe installation, not an enterprise scheduler. Cluster integration, enforced evaluator isolation, provider telemetry and automatic memory curation are extension points; see [roadmap](docs/roadmap.md). Do not confuse textual instructions with OS or GitHub permissions.

## Development

    python -m unittest discover -s tests -v

Review the installed files and the source revision before applying updates to any project. This repository does not assign a software license yet; a license decision belongs to the maintainer.
