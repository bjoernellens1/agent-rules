# Installation

The toolkit is intentionally independent of the coding harness. It needs Git and Python 3.10+; SQLite ships with ordinary Python builds. It installs no global packages or services.

## Human installation

1. Clone the toolkit into a separate checkout, inspect the source, run its tests and pin the revision you trust.

       git clone https://github.com/bjoernellens1/agent-rules.git ~/git/agent-rules
       cd ~/git/agent-rules
       git rev-parse HEAD
       python -m unittest discover -s tests -v

2. Inspect the target project and perform a dry run. Exit 1 from --check means changes would be made, 2 means a conflict/error. Use a clean target worktree when possible.

       git -C ~/git/sceneweave status --short
       python tools/agent.py install --target ~/git/sceneweave --profile research --check

3. Install and recheck. For ordinary software use --profile core instead.

       python tools/agent.py install --target ~/git/sceneweave --profile research
       python tools/agent.py install --target ~/git/sceneweave --profile research --check
       cd ~/git/sceneweave
       python .agent-rules/agent.py doctor
       git diff -- AGENTS.md
       git status --short

4. Review the new files, preserve local rules, and commit only the intended installation changes. Never stage unrelated work. The installer does not commit, modify global configuration or publish anything.

## Copy-paste instruction for a coding agent

> Install the toolkit from https://github.com/bjoernellens1/agent-rules in this repository using its INSTALL.md and AGENT_INSTALL.md. Inspect the current rules, Git state and harness first. Use the research profile for scientific/GPU projects and core for general software. Pin and verify the toolkit revision; preserve all local constraints and unrelated edits. Preview before applying. Verify the installed CLI and show the managed diff. Configure only the current project, not global settings or remote infrastructure. Report conflicts and do not claim success without running checks.

## Global knowledge setup

Default: a private SQLite database at ~/.local/share/agent-rules/knowledge.sqlite3 (or the platform-equivalent path under the current user's home). Set AGENT_RULES_HOME or AGENT_RULES_KB to change it. Use the same absolute path for all your agents/worktrees on a machine. On Unix keep the directory private and DB mode 600.

       python .agent-rules/agent.py knowledge audit
       python .agent-rules/agent.py knowledge search --project sceneweave --include-global --query "depth scale" --budget 6000

Use a stable project key independent of worktree name (sceneweave, vksplat, stereoforge, etc.). Only reviewed facts are returned by search. Never store secrets, unredacted logs, private data or raw transcripts. Review the knowledge privacy model in docs/learning.md before configuring a model or shared host. This database is not a Git file. No cloud service is enabled automatically.

## Harness selection

See docs/harnesses.md. Codex/OpenCode can use AGENTS.md when their configured discovery rules support it. Claude Code can reference it from CLAUDE.md; Antigravity can reference it from its project rules. Verify with a harmless session that the correct policy and skill can be loaded. Avoid duplicate competing instruction copies. Do not overwrite existing harness configuration; request approval for global changes.

## Upgrade

Fetch the new version in the toolkit checkout and review commits; pin the intended revision. Repeat --check, install and --check. Modified managed files cause a conflict rather than being silently overwritten. Move your custom policy outside the managed block; reconcile conflicting skills manually. The manifest tracks installed hashes. A migration may require maintainer review. Back up the knowledge database separately before schema-changing upgrades.

## Removal

No automatic destructive uninstall. Review .agent-rules/manifest.json and the managed AGENTS.md markers. Remove only tracked managed files and the marked block after checking their hashes and preserving custom content. Keep knowledge/backups unless explicitly deleting them. Do not remove an entire .agents folder because other skills may live there.

## Verification

Run the toolkit tests, target doctor, install --check, knowledge audit and a read-only recall query. For optional scheduler, container and model adapters use the dry-run/plan interface first. Run a real smoke job only with approved infrastructure, resource limits and credentials. Document which checks were actually executed.

## Optional adapters and lifelong learning

Read docs/adapters.md before configuring a GPU scheduler or evaluator container, docs/telemetry.md before measuring agents, and docs/learning.md for review, scheduled curation, multi-host exchange and repository writeback. Install no scheduler or model credentials by default. Agents must update the authoritative repo docs/tests/tools when a durable validated finding is learned and propose reusable toolkit improvements upstream. Use the explicit review and privacy boundaries.
