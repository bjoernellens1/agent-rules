# agent-rules development

Maintain a small harness-independent toolkit. The canonical distributable instructions are rules/core.md and rules/research.md. Do not duplicate their full text here. Read them before changes.

- Preserve user files and fail closed on ambiguous installation conflicts.
- Keep Python tools dependency-free (3.10+). No automatic network access, cloud spend, global config changes or hidden background processes.
- Run python -m unittest discover -s tests -v after relevant changes; add focused tests for changed behavior.
- Keep claims in README consistent with actual implementation. Clearly label unimplemented adapters and limitations.
- Do not add credentials or private machine details. Prefer explicit permission, immutable evidence and bounded outputs.

- This toolkit must improve itself: validated reusable findings from adopter repos belong in the canonical rules, skills, tools or regression tests here, not only in a conversation. Include evidence and a focused diff; do not loosen policy without designated approval.

- When evidence shows a repeatedly used workflow, use skill-forge to create or extend a reusable skill, test the actual procedure, and commit it in the canonical skills directory when generalizable. Check existing skills first; preserve review and permissions boundaries.
