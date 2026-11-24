# Verified engineering findings

This file demonstrates the repository learning requirement: retain compact evidence-backed lessons rather than repeating failure investigations. Keep mutable claims revision-scoped.

## Detached receipts on Windows

The initial scheduler extension CI on revision e645e23 exposed a transient PermissionError reading receipt.json while another process replaced it on Windows Python 3.10; cleanup also encountered an open supervisor log. Evidence: [failing run](https://github.com/bjoernellens1/agent-rules/actions/runs/45470134680), Windows/Python 3.10 job. This was not a failed GPU job or model result. Treat file-sharing races as a portability concern. The subsequent implementation adds bounded retry for Windows atomic replacement/read and regression polling; the current CI must verify the fix before claiming portability.

## Installation and initial runner

The original 14-test expanded CI passed on Linux, macOS and Windows using Python 3.10 and 3.13 at d81b77c ([run](https://github.com/bjoernellens1/agent-rules/actions/runs/45468688828)). This proves the tested fixture behaviors for that revision, not the later extensions or a live GPU/cluster integration.

## Knowledge boundary

A repository-safe note and private shared memory are different artifacts. Keep raw private evidence in the private store; export only an explicitly reviewed claim and safe citation to a public repository. Policy changes and evaluator thresholds remain reviewer-controlled.
