# Harness integration

The source of truth is rules/core.md plus an optional profile. Installation embeds the core rules in a marked region of AGENTS.md and copies skills into .agents/skills/. Existing user instructions outside that region are preserved. The research profile is an on-demand file at .agent-rules/research.md, referenced by the generated root instructions.

- Codex / OpenCode: open the target repository and check the active instructions include AGENTS.md. Explicitly load relevant skills if they are not discovered by your version.
- Claude Code: configure its project instructions to load AGENTS.md (for example an import if supported by your installed version). Do not maintain a second divergent policy.
- Antigravity and other harnesses: explicitly load AGENTS.md and the relevant skill before work, or use the harness's supported project-rule configuration to reference it.

This toolkit does not install harness plugins or change global settings. Verify actual context loading and permissions with a harmless task. Configure review workers read-only, and assign experiment workers narrowly scoped execution permissions. Never assume a prompt creates a sandbox.

For cross-project configuration, maintain a versioned private config without credentials, pin toolkit revisions, and keep site-specific hardware and scheduler settings outside the public repository. Review updates before installing. Do not automatically enable network/SSH, cloud billing, or privilege escalation.

Installation: read INSTALL.md and AGENT_INSTALL.md. Set a stable project key and common private AGENT_RULES_KB for every local harness/worktree. Use the same CLI for knowledge recall and writeback. Harness-specific telemetry imports and model-driven curation are opt-in; no hidden session capture is configured. Run the learn skill before task completion.
