---
name: skill-forge
description: Detect recurring validated workflows and automatically create or extend a tested reusable skill in the appropriate repository.
---

# skill-forge

Use when completing substantial tasks, when skill candidates reach the threshold, or when the same multi-step workflow or recurring problem is encountered again.

1. Identify a repeatable, nontrivial procedure and a stable workflow key. Record each independent successful task once, with its actual test/run/commit evidence. Never count repeated commands, unverified successes or invented tasks.
2. Run skill candidates. Three distinct validated tasks trigger implementation, not just a suggestion. Search installed project skills, the canonical agent-rules library and existing tools/docs for semantic overlap. Reuse or improve an existing skill rather than duplicating it.
3. Decide scope: project-specific procedures belong in the owning project's .agents/skills; portable procedures belong in agent-rules/skills. Keep sensitive details private; parameterize machine paths, devices, credentials and harness/model choices. Do not modify vendored managed files.
4. Prefer an executable tool or deterministic check for repeatable actions. Write a short skill with a specific trigger description, prerequisites, ordered steps, actual verification, failure handling, when not to use it and repository-safe evidence. Link tools and canonical docs instead of copying long instructions.
5. Fill templates/skill.json (installed at .agent-rules/templates/skill.json), run skill create for a preview, and apply after checking scope, duplicates and content safety. For existing skills use a focused authorized edit. Validate the actual procedure, inspect the diff and run relevant tests. Do not claim the generated scaffold proves correctness.
6. Commit the skill/tool/test to the authorized branch. Submit a PR or use explicitly authorized publication; never publish private evidence or weaken protected evaluation, safety or permission rules. Run skill complete with the exact verified commit and path; link that commit and PR in the handoff. If only existing skill reuse was needed, record its committed path instead.
7. If access, evidence or verification is blocked, preserve an actionable patch/proposal and reason. Check whether the new skill reduces repetition on later tasks; merge or retire obsolete skills through reviewed repository changes.

Commands and examples: docs/skills.md in the toolkit. Keep the library small and on-demand. No automatic shell execution, network transmission or unsupervised policy modification.
