# Shared engineering rules

Optimize time to validated results, correctness, maintainability and resource efficiency.

1. Establish the actual repository, intended revision, dirty state, environment and running build. Preserve concurrent and unrelated work.
2. Read the smallest relevant context: local rules, authoritative source, contracts and measured evidence. Reuse existing code, tools and findings. Before substantial work, query relevant reviewed project/global knowledge using the stable project key; do not load the whole knowledge base.
3. Implement small reversible changes directly; for substantial work define objective, scope, baseline, budget, acceptance and stop conditions before editing.
4. Assign one owner per writable component. Isolate concurrent writes in worktrees. Coordinate shared interfaces and integration; do not stage another worker's changes.
5. Build a minimal working vertical slice. Prefer simple existing mechanisms; avoid speculative abstractions, duplicate logic, dependencies, flags and unrelated refactors.
6. Protect evaluation, datasets, thresholds and permission boundaries. Never weaken a gate, hide failures/outliers or change a metric to obtain success. Escalate proposed contract changes separately.
7. Use canonical commands. Run the relevant tests and real end-to-end checks. For visual changes inspect matched before/after output; for performance claims compare measured equivalent conditions. A file or passing unit test alone is not proof.
8. Bound and schedule expensive jobs. Make them independently inspectable and resumable where supported. Reuse fingerprinted results; do not rerun unaffected expensive checks without a reason.
9. Keep secrets, private data, machine-specific state, model weights and large artifacts out of Git. Ask before irreversible, external or cost-incurring actions not already authorized.
10. Record revision, commands, results, limitations, artifacts and next action. Report measured, estimated, failed, blocked and unverified outcomes distinctly. Stop at validated completion, an exhausted budget or a documented blocker.
11. Learning is part of completion. For every non-obvious validated finding, update the relevant repository's canonical docs, contract, test or tool and record concise evidence in the shared knowledge store. For a proven reusable rule/skill/tool improvement, implement a focused upstream change in agent-rules, test it and commit it to an authorized branch; submit it for review or publish only when authorized. If access is blocked, record an actionable proposal with evidence and the exact intended change. Do not leave durable learning only in chat or private notes. If nothing durable was learned, say so; if writeback is blocked, record the destination and reason. Never autonomously weaken protected policies, gates or permissions; keep confidential findings private and obtain authorization before publishing.
12. Use focused commits and independent review for consequential changes. Do not self-approve protected changes or publish unrelated work.

Load relevant on-demand procedures in .agents/skills/ (research, plan, implement, experiment, review, visual-qa, handoff, learn). For tasks involving significant GPU or scientific work, also read the research profile when that profile is active.
