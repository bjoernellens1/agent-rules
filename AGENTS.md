# agent-rules development

Maintain a small harness-independent toolkit. The canonical distributable instructions are rules/core.md and rules/research.md. Do not duplicate their full text here. Read them before changes.

- Preserve user files and fail closed on ambiguous installation conflicts.
- Keep Python tools dependency-free (3.10+). No automatic network access, cloud spend, global config changes or hidden background processes.
- Run python -m unittest discover -s tests -v after relevant changes; add focused tests for changed behavior.
- Keep claims in README consistent with actual implementation. Clearly label unimplemented adapters and limitations.
- Do not add credentials or private machine details. Prefer explicit permission, immutable evidence and bounded outputs.
