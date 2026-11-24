# Lifelong knowledge and repository learning

## Design decision

SQLite is the local canonical store; generated Markdown is a convenient inspectable view and Git writeback format. Technical search needs exact model names, file names, commit hashes, numerical values, scope, dates and citations. Full-text FTS5 (when available) plus lexical fallback avoids a mandatory vector service. Lexical similarity suggests duplicate candidates; model-driven distillation is optional. Neither lexical similarity nor an LLM can independently validate a scientific claim. See sources.md for the inspiration.

Separate five things: task state (handoff), raw evidence (experiment artifacts), observations (immutable claims plus cited sources), reviewed facts (compact current version plus retained history), and operational policy (Git-reviewed rules). The database is not an executable instruction channel.

## Layout and scope

One private SQLite database per trust boundary, default AGENT_RULES_KB or AGENT_RULES_HOME/knowledge.sqlite3 (~/.local/share/agent-rules by default). Use one stable project key per repository, independent of branch/worktree. The special project global contains explicitly promoted cross-project findings. Other projects are not searched implicitly. Do not store credentials, private messages, raw sessions or sensitive datasets. Use private evidence references, and use a different DB for a separate trust boundary.

Use a local filesystem with working SQLite locking. Do not put a live SQLite database on NFS or blindly sync it between hosts. For multiple machines choose one trusted knowledge host and call its CLI through your authorized SSH/remote execution setup. Offline workers can exchange scoped observations by JSONL and import idempotently; their reviewed status does not automatically transfer. Keep the canonical approvals on the knowledge host. These are cooperative controls: any process with DB write access can bypass them. For a multi-user adversarial deployment use separate OS identities or a restricted service with actual authorization.

## Required learning loop

At task start recall relevant reviewed facts with a bounded query. At completion, agents must identify non-obvious validated findings (including negative results). Update the authoritative repository location: contract, decision, troubleshooting note, regression test, tool or report. Store a concise observation in the shared KB with source evidence. Generalizable improvements to the toolkit belong in a focused upstream agent-rules issue/patch, with measured evidence and review. Do not fork managed copies or silently rewrite rules. If a finding is already recorded, link the existing entry rather than duplicate it. If none, record "no durable finding"; if blocked, document why and where it should go. Private discoveries remain private, with a sanitized repository-safe summary only when authorized.

## Commands

Examples assume an actual verified finding and real source references, not placeholders to ingest.

    python .agent-rules/agent.py knowledge add --project sceneweave --topic optimizer/active-set --kind lesson --body "VERIFIED CLAIM" --evidence "COMMIT OR RUN RECEIPT"
    python .agent-rules/agent.py knowledge maintain --project sceneweave
    python .agent-rules/agent.py knowledge similar --project sceneweave
    python .agent-rules/agent.py knowledge packet --project sceneweave --limit 20
    python .agent-rules/agent.py knowledge propose --project sceneweave --topic optimizer/active-set --body "DISTILLED CLAIM" --observations 1 2
    python .agent-rules/agent.py knowledge proposals --project sceneweave
    python .agent-rules/agent.py knowledge inspect-proposal 1
    python .agent-rules/agent.py knowledge decide 1 approve --reviewer designated-reviewer --reason "Verified against cited sources"
    python .agent-rules/agent.py knowledge search --project sceneweave --include-global --query "active set" --budget 6000
    python .agent-rules/agent.py knowledge history --project sceneweave --topic optimizer/active-set
    python .agent-rules/agent.py knowledge export --project sceneweave
    python .agent-rules/agent.py knowledge audit

Use actual IDs returned by your store. Kind is fact, decision, lesson, procedure or negative-result. Each project/topic/kind is a stable identity for one proposition; split distinct propositions into different topics. Observation text is normalized for exact deduplication, keeping independent evidence. Similarity is advisory (bounded recent observations); avoid merging negations, different numerical conditions or independent claims. Curate conflict groups into a short accurate synthesis. Superseded and retired facts are kept with their source/proposal history, not erased. Stale facts are excluded from normal recall; use --include-stale only when reviewing them. Approve a new version after revalidation or explicitly retire it. Proposal approval is a recorded decision, not authentication; enforce reviewer roles outside the CLI.

Promote a lesson across repositories only if scope justifies it: propose with --project global --cross-project and source observation IDs. It must still be reviewed and does not consume the original project's pending observation. New evidence invalidates a pending proposal snapshot and reopens a covered observation. Reviewed facts retain the exact approval-time evidence snapshot; use inspect-proposal to review paginated sources before approval. For migrated v1 databases, historical source sets cannot be reconstructed, so snapshots reflect available sources at migration time (recorded in the event log). New evidence must preserve important conflicting evidence; don't compress away conditions, failures or uncertainty.

## Optional scheduled curation ("dreaming")

Run maintain periodically via your existing scheduler to propose isolated observations and flag conflicts/stale facts. A curator can read packet output, distill candidate claims and use propose. For automated model calls:

    python .agent-rules/agent.py knowledge curate --project sceneweave --limit 20 --timeout 120 -- /path/to/approved-curator-adapter

For an approved local OpenAI-compatible chat endpoint, an optional standard-library adapter is included:

    python .agent-rules/agent.py knowledge curate --project sceneweave --limit 20 --timeout 120 -- python .agent-rules/agent_curator.py --endpoint http://127.0.0.1:1234/v1/chat/completions --model YOUR_LOADED_MODEL

Use the actual local model and port. The adapter rejects redirects and non-loopback HTTP; remote HTTPS requires --allow-remote and separate authorization to transmit the packet. If required, pass --api-key-env NAME (credential value read from environment, never printed). Optional --json-mode asks compatible servers for structured JSON; otherwise strict output is still required. No real endpoint is contacted during installation.

The adapter reads one JSON packet from stdin and writes only {"proposals":[{"topic":"stable-key","kind":"lesson","body":"distilled claim","observations":[1,2],"review_days":90}]} to stdout. It receives bounded observations and current/rejected claim context. No model, credentials or automatic cloud transmission are installed. The chosen command is trusted local code; authorize its data access, network and spend separately. The CLI validates output shape, observation IDs and stale target versions; it does not verify the truth of an LLM summary. All proposals need designated review; never auto-approve policy, permission or gate changes.

An opt-in cron example (replace both absolute paths with your actual installation):

    15 3 * * * /usr/bin/python3 /absolute/path/agent-rules/tools/agent.py knowledge maintain --project sceneweave >> /private/path/knowledge-maintenance.log 2>&1

Use one job per project and avoid concurrent scheduled curators for the same project; transactions and proposal fingerprints reduce duplicates, but an external model may still incur duplicate cost. Never schedule jobs from an agent without authorization. The curator should periodically review rejected proposals, stale facts, recurring mistakes and context size. The database retains evidence history while compacting the *active view*, not deleting raw evidence. Back up before schema upgrades.

## Repository writeback

Prefer editing the existing canonical source; do not create duplicate Markdown for facts already captured by code/docs. When a reviewed fact needs a standalone repo note:

    python .agent-rules/agent.py knowledge writeback FACT_ID --target /absolute/project/root --public-evidence docs/experiment.md
    python .agent-rules/agent.py knowledge writeback FACT_ID --target /absolute/project/root --public-evidence docs/experiment.md --apply --confirm-repo-safe

Preview first. The command writes a stable topic-keyed note under docs/knowledge/ and excludes raw private evidence. For a changed existing entry pass its exact preview existing_sha256 via --expected-sha; do not overwrite local edits blindly. Inspect the diff and stage only the authorized changes. The CLI does not commit or publish. The supplied citation and approved claim itself must be appropriate for repository visibility. For a retired or superseded fact, update/remove any stale repo note through a reviewed change; the CLI does not automatically delete notes.

## Backup and exchange

    python .agent-rules/agent.py knowledge backup --output /private/backup-001.sqlite3
    python .agent-rules/agent.py knowledge export-observations --project sceneweave > /private/observations.jsonl
    python .agent-rules/agent.py knowledge import-observations --project sceneweave --input /private/observations.jsonl
    python .agent-rules/agent.py knowledge import-inbox --project sceneweave --inbox .agent-work/knowledge.jsonl

Review private exchange files before moving them; they contain full observation/source text. Backup uses SQLite's snapshot API; restore offline only after integrity check. Markdown export is generated, not canonical. Observation IDs are local; exchanges use content/source identity. Keep raw evidence in the appropriate private artifact store. No cloud service or vector model is required.

## Automatic skill discovery and creation

The same private SQLite store records successful workflow uses by stable workflow, project and task identity. The default promotion threshold is three distinct validated tasks; duplicate uses in one task do not inflate it. Check candidates before completing substantial work. Agents must create or improve and commit a suitable skill at the threshold, not leave a recommendation. Search existing skills and the canonical upstream library first. The skill command supports evidence counting, inventory, preview/creation and commit verification. Generalizable workflows belong in agent-rules; project-specific procedures remain in their project. See [skill lifecycle](skills.md). Knowledge observations and workflow counts are evidence, not executable instructions, and never grant publication or policy-change authority.
