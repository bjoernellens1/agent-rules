# Execution adapters and evaluator isolation

Core local runs, knowledge, telemetry and planning need only Python/Git. Cluster execution needs an authorized configured kubectl context; containers need an approved local Docker or Podman engine and digest-pinned image. All external mutations are explicitly confirmed. No deployment, cluster account, cloud billing or secrets are created by the toolkit.

## Local device scheduling

    python tools/agent.py scheduler local-submit --device strix-halo-gpu0 --out /tmp/run-01 --context context.json --timeout 120 --confirm -- python benchmark.py
    python tools/agent.py status /tmp/run-01
    python tools/agent.py logs /tmp/run-01 --lines 30
    python tools/agent.py cancel /tmp/run-01

Use a consistent machine/device name for all local jobs. A cooperative filesystem lease excludes other toolkit jobs using the same key; it does not prevent arbitrary non-toolkit GPU processes or set device visibility. Configure the runtime's device selection separately, and verify actual GPU use in measurements. Cancellation is requested via a marker, not by guessing a PID; check terminal receipt. On supervisor crash the lease fails closed and remains until a human verifies the process is gone. Never remove an active lease. On POSIX a timeout/cancel kills the child's process group, Windows kills the direct child only; use an external job manager for arbitrary Windows descendants.

## Kubernetes / K3s / Kai / Argo

Copy templates/scheduler.json. Fill context, namespace, a unique job name, immutable image digest, exact resources, deadline, command, read-only inputs and a dedicated output PVC. Use the actual scheduler name and advertised GPU resource, not a guessed cluster setting. Kai-specific fractional GPU policy and queues must be configured by the cluster operator; the toolkit uses ordinary schedulerName and extended-resource requests. Set backend to argo and service_account to an approved workflow account for native Argo Workflow CRD (also compatible with a Hera-managed Argo cluster). It does not install Hera or Kai.

    python tools/agent.py scheduler plan --spec scheduler.json
    python tools/agent.py scheduler submit --spec scheduler.json --confirm
    python tools/agent.py scheduler status --spec scheduler.json
    python tools/agent.py scheduler logs --spec scheduler.json --lines 30
    python tools/agent.py scheduler usage --spec scheduler.json
    python tools/agent.py scheduler cancel --spec scheduler.json --uid ACTUAL_RESOURCE_UID --confirm
    python tools/agent.py scheduler fetch --source /mounted/run-artifacts --destination /local/new-run-artifacts

Argo logs require --pod and check workflow ownership label. Submission uses create rather than replacing an existing job. Cancel verifies observed UID before deletion; this is not an atomic UID precondition, so unique names and controlled ownership are required. Usage reports resource requests/limits and available metrics-server CPU/memory snapshots, not real GPU utilization or billing. Fetch copies a mounted durable directory, not arbitrary SSH/cluster files. Verify receipts and artifact identities after copying. Use your authorized PVC/object-storage transport. Resuming a computation still requires checkpoint support in the underlying benchmark.

Plan is a local manifest generator, not proof that the cluster accepts it. Validate against the target cluster and run a minimal authorized smoke job before adopting it. Kubernetes RBAC, pod security, resource quotas, network policy, immutable input staging, device plugin and GPU verification belong to the site operator. Argo executor needs its own RBAC and may mount a service account token; configure isolation independently. Candidate and evaluator jobs should be created with separate service accounts/namespaces and immutable artifacts.

## Isolated candidate/evaluator

Copy templates/sandbox.json. Stage candidate code, permitted training data and a fresh writable predictions/output directory. Never mount the sealed dataset/evaluator into candidate. For the evaluator use only immutable trusted evaluator, sealed data, candidate predictions (read-only) and a *different*, empty output directory; never run candidate code in evaluator. Do not deserialize untrusted pickle or arbitrary executable formats. The evaluator verifies dataset, code, config and output identities against a frozen contract before computing gates.

    python tools/agent.py sandbox plan --spec sandbox.json
    python tools/agent.py sandbox run --spec sandbox.json --confirm

Local container command uses digest-pinned image, no network, no extra privileges, nonroot user, read-only root, disjoint mounts, CPU/memory/deadline limits. It is a CPU adapter; GPU isolated evaluation needs a cluster/device-specific policy. Stage safe paths outside candidate control. Docker/Podman access is privileged in many deployments; give candidate no engine socket or host credentials. Containers are defense-in-depth, not a proof against a malicious candidate or kernel vulnerability. Mount paths, permissions and actual engine behavior must be verified on the target host.

## Project adapter

Use templates/project.json to provide canonical argument vectors for build, checks, small benchmarks, GPU probes and visual QA. Keep actual site-specific paths private or parameterize in the calling environment. No implicit shell evaluation. Running a command wraps the receipt runner:

    python tools/agent.py project list --config project.json
    python tools/agent.py project plan --config project.json test
    python tools/agent.py project run --config project.json test --out /tmp/check-1 --context context.json --timeout 120 --confirm

Always inspect loaded config. The command is trusted project code, not an untrusted sandbox. This avoids agents inventing different build and benchmark commands every session.
