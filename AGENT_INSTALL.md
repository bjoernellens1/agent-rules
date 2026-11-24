# Agent installation contract

Use this document when a human asks you to adopt agent-rules in an existing repository. It is not authorization to change unrelated repositories or global settings.

- Locate the actual repository root, HEAD, worktree, dirty files, existing AGENTS.md / CLAUDE.md / harness rules, tests and tools. Do not assume the current directory is the target.
- Inspect INSTALL.md and the toolkit source, record the exact toolkit commit. Run the toolkit regression suite if possible. Choose core unless scientific/GPU work justifies research.
- Use the source checkout's tools/agent.py install --target ABSOLUTE_TARGET --profile PROFILE --check. A drift exit code (1) is expected for a new installation; a conflict/error (2) is not. Do not delete existing rules to bypass conflicts.
- Apply the same command without --check. Review AGENTS.md, managed manifest and added skills. Re-run --check and the installed doctor. Verify the active harness loads AGENTS.md; use a small pointer from its native rule file if explicitly permitted.
- Settle a stable project key for knowledge (repo name, not branch/worktree). Use the private default KB or an explicitly configured AGENT_RULES_KB. Recall relevant reviewed project/global facts only when needed. Record findings with source references; never upload private contents or automatically approve rule changes.
- Do not install optional daemons, schedules, model APIs, GPU jobs or cloud credentials by default. For those, read the corresponding documentation, propose the configuration and get authorization.
- If the user wants a commit, stage only the installed policy files and authorized local integration. Preserve other agents' work.
- Report target path, toolkit revision, profile, changed files, conflicts, verification results, and remaining harness-specific configuration. Do not claim a check you did not run.

After installation use AGENTS.md as the root policy. Load only relevant skills. Keep personal and site-specific information in the private knowledge store or external configuration, not in distributable rules.

After adoption, enforce the learning writeback rule: verified discoveries must update the target project's authoritative docs/tests/tools, and reusable improvements should be proposed upstream in agent-rules. Preserve privacy and protected review boundaries; never silently edit vendored managed blocks.
