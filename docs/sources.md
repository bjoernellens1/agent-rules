# Inspiration and attribution

The rules and tools here are independently written syntheses, not copied agent prompts or third-party implementations. The following publicly documented practices informed the design:

- Ryan Vogel, [DashSplat](https://github.com/R44VC0RP/dashsplat): shared data contract, folder ownership, iterative reports, causal evidence, remote execution, handoffs.
- [Superlocal agent instructions](https://github.com/R44VC0RP/superlocal/blob/main/AGENTS.md): actual baseline/build, matched evidence, no weakened budgets, visual review and single commit owner.
- [OpenSend](https://github.com/R44VC0RP/opensend): one authoritative API, measured bottlenecks, safe operational boundaries.
- [OpenCode memory skill](https://github.com/R44VC0RP/skills/blob/main/skills/opencode-memory/SKILL.md): lean context, append-only learning, curated knowledge, approved rule proposals.
- [ferry](https://github.com/R44VC0RP/ferry): separate editing from remote heavy jobs. Do not copy its broad machine trust policy into shared clusters.
- [Karpathy autoresearch](https://github.com/karpathy/autoresearch): bounded experiments, protected evaluation, keep/discard.
- [Simon Willison Showboat](https://github.com/simonw/showboat): executable evidence.
- [Mitchell Hashimoto, My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey): invest in preventing recurring agent errors.
- [OpenAI, Harness engineering](https://openai.com/index/harness-engineering/): agent-readable source, structured docs and mechanical enforcement.
- [Anthropic, Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): selective context and tool design.

These references motivate practices, not proof of a specific productivity multiplier or the private DashSplat model lineup. Validate the toolkit's effects in our own work. Do not assume model or harness support based only on an example configuration.

## Knowledge architecture

- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): incremental compaction and reusable linked knowledge.
- [Letta archival memory](https://docs.letta.com/v1-sdk/memory/archival-memory): separate working context and long-term retrieval.
- [Mem0 paper](https://arxiv.org/abs/2504.19413): extraction, updating and selective retrieval of memories.
- [Graphiti](https://github.com/getzep/graphiti): temporal facts and provenance.
- [SQLite FTS5](https://www.sqlite.org/fts5.html): local full-text indexing. The toolkit uses SQLite transactions, optional FTS5 and explicit review rather than adopting a vector or graph service up front. Semantic dedup is advisory and cannot establish truth.
