# Recurring workflow → reusable skill

A lifelong-learning system should turn repeated work into a capability, not just a larger memory prompt. At substantial task completion, agents identify nontrivial repeatable procedures, record successful uses with actual evidence, and automatically implement or extend a skill once it has been used in three distinct validated tasks. Three is the initial engineering threshold, not an empirically optimized value. A repeated command in one task counts once.

## Skill lifecycle

1. **Observe:** stable workflow key, project identity, task ID, compact procedure summary, validation reference. Counts are distinct project/task pairs, agent-reported and not independent proof.
2. **Detect:** examine the candidates queue. If the workflow has already been promoted, improve/reuse it rather than create a duplicate.
3. **Deduplicate:** inventory project and upstream skills, read the relevant documents/tools, and check semantic overlap. The generator rejects duplicate names and exact workflow markers; semantic overlap requires agent judgment.
4. **Author:** implement a tested tool/check for deterministic operations and a concise SKILL.md for orchestration. Project-specific skills live in .agents/skills; generalizable skills live in the canonical agent-rules/skills directory. Use only repository-safe evidence and parameterized prerequisites.
5. **Validate:** perform the procedure on a fixture or real authorized task; run relevant tests. Inspect actual behavior, including failure paths. A generated file is not a verified capability.
6. **Commit:** create a focused change in the appropriate authorized repository/branch. Submit a PR or publish only under existing authorization. Record the committed skill path and exact SHA. If access is blocked, retain a patch or actionable issue; do not silently skip learning.
7. **Improve:** on later use, update the existing skill/tool when measured evidence warrants it. Retire or consolidate obsolete skills through reviewed changes, not deletion of unrelated local files.

No new skill may bypass permissions or protected evaluation. Repeated unsafe practices are not positive evidence. Do not save secrets, transcripts, private logs or sensitive evidence in a public skill. The agent may create normal non-policy skills without a separate task from the user when its repository write scope already permits the change; publishing and protected changes still follow authorization.

## Commands

Run from the target project with the installed CLI (or from the toolkit with tools/agent.py). Replace placeholders with actual data, not fictional memory.

    python .agent-rules/agent.py skill record --workflow gpu/paired-render-check --project sceneweave --task ACTUAL_TASK_ID --summary "VERIFIED PROCEDURE" --evidence "ACTUAL COMMIT OR RUN RECEIPT"
    python .agent-rules/agent.py skill candidates
    python .agent-rules/agent.py skill candidates --project sceneweave
    python .agent-rules/agent.py skill inventory --target /absolute/project
    python .agent-rules/agent.py skill inventory --target /absolute/agent-rules

Workflow uses share the private knowledge database, with the same backup and trust boundary. Use the same stable workflow key across projects if it truly represents the same procedure; prefix project-specific keys when their behavior differs. Candidate output includes private evidence references. Do not copy that output blindly into Git. Same task/evidence is idempotent; conflicting records are rejected. Scope-specific creation needs three uses in that project; shared creation needs three across the combined projects. Cross-project applicability still requires actual evidence or justified generalization.

Copy templates/skill.json to a private working file and replace its placeholders. Shared specs use scope shared and omit project; local specs use scope project and the stable project key.

    python tools/agent.py skill create --target /absolute/agent-rules --spec /private/skill.json
    python tools/agent.py skill create --target /absolute/agent-rules --spec /private/skill.json --apply --confirm-repo-safe

The first command previews. The second creates a new document exclusively, never overwrites an existing one. If an equivalent skill already exists, edit/reuse it using ordinary scoped Git work. The generator does not execute skill content, commit or push. For a project-specific skill, use the project root as target. The shared target must look like the canonical toolkit checkout.

After verification and a focused Git commit:

    python tools/agent.py skill complete --workflow gpu/paired-render-check --scope shared --repository agent-rules --target /absolute/agent-rules --skill-path skills/paired-render-check/SKILL.md --commit ACTUAL_FULL_SHA --disposition created

Use --disposition extended or reused for existing skills; project scope additionally requires --project. Completion checks the actual Git commit and path; for created/extended it requires the commit changed that file, and newly created files must include the workflow marker. It records the promotion in SQLite so subsequent tasks reuse it. It does not prove the commit was pushed or the procedure works; the agent must retain test evidence and the PR/push receipt separately.

## Boundaries

This is automatic as part of the agent's required learning workflow, not a daemon that watches every keystroke or infers reliable skills from raw transcripts. It relies on task-completion hooks/instructions in the selected harness and accurate reporting. It does not grant new permissions or silently alter shared policies. For multi-host work use the canonical KB host; observation exchange does not currently replicate workflow-use records, so submit skill records there directly. Keep the active skill library compact; load only skills relevant to the current task.
