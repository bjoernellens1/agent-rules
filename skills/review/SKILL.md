---
name: review
description: Independently challenge code, architecture, numerical results or scientific claims.
---

# review

Read task contract and actual base/head, inspect implementation and evidence independently. Do not modify candidate, thresholds or protected evaluator. Check scope, invariants, tests, concurrency, causality, leakage, numerical accuracy, matched budgets, unsupported claims and failure cases. Rank findings by impact, provide file/line or run evidence and actionable resolution. Return accept/reject/revise/blocked with unverified checks explicitly listed.

Run the scope check against the frozen reviewer-controlled scope.json if available. Verify that candidate changes do not touch protected files. A passing diff check does not replace access control.
