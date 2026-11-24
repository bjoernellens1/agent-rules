# Knowledge and learning

Keep temporary task state in task handoffs, permanent decisions in architecture/contract documents, and non-obvious verified findings in a searchable project knowledge store. Do not keep appending to global AGENTS.md.

Use the learn command to append a compact JSONL record (scope, finding, evidence and timestamp). Use an ignored/private path for discoveries that include unpublished details. No secrets or personal data. Append-only writes avoid read-modify-write conflicts; coordinate rotation and curation with active writers.

At a milestone or on a scheduled site-specific job, a curator reads new records and relevant session/run evidence, deduplicates, checks sources, and classifies each finding as: discard, durable fact, test/tool improvement, skill update or rule proposal. Facts must retain evidence and scope. Proposed policy changes need maintainer approval; changes to test/evaluation/permissions are never automatic. Commit approved updates, retain rejected proposals, and keep a rollback path.

Suggested curated structure: docs/knowledge/index.md, topic files, decisions, and an append-only inbox outside tracked source. A memory system should reduce repeated context, not grow indiscriminately. Track repeated mistakes, tokens spent rediscovering facts and stale advice. A dated fact is not a timeless rule.

This version supplies append-only capture and a curation procedure, not a scheduled LLM memory agent.
