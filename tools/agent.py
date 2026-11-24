#!/usr/bin/env python3
"""Portable agent workflow CLI. Python 3.10+, standard library and Git."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import stat
import sqlite3
import subprocess
import sys
import tempfile
import shutil
import time

HERE = Path(__file__).resolve()
START = "<!-- agent-rules:begin -->"
END = "<!-- agent-rules:end -->"
SCHEMA = 1


class RuleError(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    if not path.is_file() or path.is_symlink():
        raise RuleError(f"Not a regular artifact: {path}")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream, parse_constant=lambda value: (_ for _ in ()).throw(
            RuleError(f"Invalid JSON number: {value}")))


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, temp = tempfile.mkstemp(prefix=".agent-tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def write_json(path, value):
    atomic_write(path, json_bytes(value))


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def git(cwd, *args, check=True):
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True,
                            text=True, check=False)
    if check and result.returncode:
        raise RuleError("Git command failed: " + " ".join(args) + "\n" + result.stderr.strip())
    return result


def identity(cwd):
    root = Path(git(cwd, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    return {"root": str(root), "commit": git(root, "rev-parse", "HEAD").stdout.strip(),
            "dirty": bool(git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout)}


def safe_path(root, name):
    rel = Path(name)
    if rel.is_absolute() or ".." in rel.parts:
        raise RuleError(f"Unsafe relative path: {name}")
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise RuleError(f"Refusing symlink: {path}")
    return path


def existing(path):
    if not path.exists():
        return None
    if not path.is_file():
        raise RuleError(f"Expected regular file: {path}")
    return path.read_bytes()


def split_block(raw):
    start, end = START.encode(), END.encode()
    if not raw.count(start) and not raw.count(end):
        return None, None, None
    if raw.count(start) != 1 or raw.count(end) != 1:
        raise RuleError("Ambiguous managed AGENTS.md markers")
    i, j = raw.index(start), raw.index(end) + len(end)
    if i >= j - len(end) or (i and raw[i-1:i] != b"\n"):
        raise RuleError("Invalid managed AGENTS.md block")
    if j < len(raw) and raw[j:j+1] not in (b"\n", b"\r"):
        raise RuleError("Invalid managed AGENTS.md end marker")
    return raw[:i], raw[i:j], raw[j:]


def install(args):
    source = HERE.parents[1]
    if not (source / "rules/core.md").is_file():
        raise RuleError("Install from a toolkit checkout, not a vendored CLI")
    target = Path(args.target).resolve()
    if not target.is_dir():
        raise RuleError("Target must be an existing directory")
    try:
        source_id = identity(source)
        revision = source_id["commit"]
        source_dirty = source_id["dirty"]
    except RuleError:
        revision, source_dirty = None, None
    manifest_path = safe_path(target, ".agent-rules/manifest.json")
    old = read_json(manifest_path) if manifest_path.exists() else None
    if old is not None and (not isinstance(old, dict) or old.get("schema") != SCHEMA
                            or not isinstance(old.get("files"), dict)):
        raise RuleError("Unknown or invalid install manifest")
    core = (source / "rules/core.md").read_text(encoding="utf-8").rstrip()
    profile = ("Research profile active: before significant scientific or GPU work, "
               "read .agent-rules/research.md." if args.profile == "research" else
               "Core profile active. The optional research profile is available at .agent-rules/research.md.")
    block = (START + "\n" + core + "\n\n" + profile + "\n" + END).encode()
    root_path = safe_path(target, "AGENTS.md")
    raw = existing(root_path) or b""
    prefix, current, suffix = split_block(raw)
    if current is not None:
        if old is None or digest(current) != old.get("root_block"):
            raise RuleError("Managed AGENTS.md block was edited or is unowned; review manually")
        root_data = prefix + block + suffix
    else:
        if old is not None:
            raise RuleError("Managed AGENTS.md block is missing; review manually")
        sep = b"" if not raw else b"\n" if raw.endswith(b"\n") else b"\n\n"
        root_data = raw + sep + block + b"\n"
    files = {
        ".agent-rules/agent.py": HERE.read_bytes(),
        ".agent-rules/research.md": (source / "rules/research.md").read_bytes(),
        ".agent-work/.gitignore": b"*\n!.gitignore\n",
    }
    for module in sorted((source / "tools").glob("agent_*.py")):
        files[".agent-rules/" + module.name] = module.read_bytes()
    for folder, dest in (("skills", ".agents/skills"), ("templates", ".agent-rules/templates")):
        for path in sorted((source / folder).rglob("*")):
            if path.is_file():
                files[dest + "/" + path.relative_to(source / folder).as_posix()] = path.read_bytes()
    hashes = {name: digest(data) for name, data in files.items()}
    old_files = old["files"] if old else {}
    obsolete = set(old_files) - set(files)
    if obsolete:
        raise RuleError("Obsolete managed files require explicit migration: " + ", ".join(sorted(obsolete)))
    planned = {}
    for name, data in files.items():
        path = safe_path(target, name)
        before = existing(path)
        if name in old_files:
            if before is None or digest(before) != old_files[name]:
                raise RuleError(f"Managed file changed or missing: {name}")
        elif before is not None and before != data:
            raise RuleError(f"Unmanaged file collision: {name}")
        if before != data:
            planned[name] = data
    if root_data != raw:
        planned["AGENTS.md"] = root_data
    manifest = {"schema": SCHEMA, "profile": args.profile, "source_revision": revision,
                "source_dirty": source_dirty, "root_block": digest(block), "files": hashes}
    manifest_data = json_bytes(manifest)
    if existing(manifest_path) != manifest_data:
        planned[".agent-rules/manifest.json"] = manifest_data
    if not args.check:
        for name, data in planned.items():
            atomic_write(safe_path(target, name), data)
    emit({"target": str(target), "profile": args.profile, "source_revision": revision,
          "source_dirty": source_dirty, "mode": "check" if args.check else "install",
          "changed": list(planned), "status": "drift" if args.check and planned else "ok"})
    return int(bool(args.check and planned))


def doctor(args):
    state = identity(Path(args.target))
    emit({"repository": state, "python": platform.python_version(), "system": platform.system(),
          "machine": platform.machine(), "managed_rules": (Path(state["root"]) /
          ".agent-rules/manifest.json").is_file(), "gpu": "not probed; verify with site runtime"})
    return 0


def task_new(args):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", args.id):
        raise RuleError("Task ID must be 1–80 letters, digits, underscores or hyphens")
    state = identity(Path.cwd())
    root = Path(state["root"])
    folder = safe_path(root, ".agent-work/tasks/" + args.id)
    template = HERE.parent / "templates/TASK.md"
    if not template.is_file():
        template = HERE.parents[1] / "templates/TASK.md"
    text = template.read_text(encoding="utf-8").replace(
        "Objective:", "Objective: " + args.objective, 1).replace(
        "Baseline (revision/build and measurements):",
        "Baseline (revision/build and measurements): " + state["commit"] +
        (" (dirty checkout; investigate)" if state["dirty"] else " (measure behavior)"), 1)
    folder.mkdir(parents=True, exist_ok=False)
    atomic_write(folder / "TASK.md", text.encode())
    emit({"task": str(folder / "TASK.md"), "revision": state["commit"],
          "note": "Fill remaining contract; create a separate worktree if needed."})
    return 0


def task_worktree(args):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", args.id):
        raise RuleError("Invalid task ID")
    root = Path(identity(Path.cwd())["root"])
    path = Path(args.path).resolve()
    if path.exists() or path.is_relative_to(root) or not path.parent.is_dir():
        raise RuleError("Worktree path must be fresh, outside this checkout, with an existing parent")
    commit = git(root, "rev-parse", "--verify", "--end-of-options", args.base + "^{commit}").stdout.strip()
    branch = "agent/" + args.id
    git(root, "worktree", "add", "-b", branch, str(path), commit)
    emit({"branch": branch, "worktree": identity(path),
          "note": "Only committed base content is included; existing local edits were preserved."})
    return 0


def scope(args):
    """Inspect committed, staged, unstaged and untracked paths against a contract."""
    root = Path(identity(Path.cwd())["root"])
    contract_path = Path(args.contract)
    contract = read_json(contract_path)
    if not isinstance(contract, dict):
        raise RuleError("Scope contract must be an object")
    if not isinstance(contract.get("base"), str) or not contract["base"]:
        raise RuleError("Scope contract must specify a base revision")
    allowed, protected = contract.get("allow"), contract.get("protect", [])
    def valid_paths(paths):
        return isinstance(paths, list) and all(
            isinstance(p, str) and p and "\\" not in p and
            all(part not in ("", ".", "..") for part in p.split("/"))
            for p in paths)
    if not valid_paths(allowed) or not allowed or not valid_paths(protected):
        raise RuleError("Specify nonempty allow paths and optional protect paths as relative POSIX prefixes")
    base = git(root, "rev-parse", "--verify", "--end-of-options",
               contract["base"] + "^{commit}").stdout.strip()
    if git(root, "merge-base", "--is-ancestor", base, "HEAD", check=False).returncode:
        raise RuleError("Scope baseline must be an ancestor of HEAD")
    changed = set()
    for command in (("diff", "--name-only", "-z", "--no-renames", base, "HEAD", "--"),
                    ("diff", "--cached", "--name-only", "-z", "--no-renames", base, "--"),
                    ("diff", "--name-only", "-z", "--no-renames", "--"),
                    ("ls-files", "--others", "--exclude-standard", "-z")):
        changed.update(p for p in git(root, *command).stdout.split("\0") if p)
    def matches(path, prefixes):
        return any(path == p or path.startswith(p + "/") for p in prefixes)
    denied = sorted(p for p in changed if matches(p, protected) or not matches(p, allowed))
    emit({"status": "fail" if denied else "pass", "base": base,
          "contract_sha256": file_hash(contract_path), "changed": sorted(changed),
          "violations": denied, "note": "Diff check, not filesystem access control"})
    return int(bool(denied))


def metrics(path):
    if not path.is_file() or path.is_symlink():
        raise RuleError("Missing or unsafe metrics.json")
    data = read_json(path)
    if not isinstance(data, dict) or not data:
        raise RuleError("Metrics must be a nonempty object")
    for key, value in data.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise RuleError(f"Metric must be finite numeric: {key}")
    return data


def lease_path(name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", name):
        raise RuleError("Lease name must be a stable machine/device key")
    root = Path(os.environ.get("AGENT_RULES_HOME", Path.home() / ".local/share/agent-rules")).expanduser() / "leases"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root / name

def cancel(args):
    folder = Path(args.run).resolve()
    receipt = read_json(folder / "receipt.json")
    if receipt["status"] not in ("pending", "running"):
        raise RuleError("Run is already terminal")
    marker = folder / "cancel.request"
    try:
        with marker.open("x", encoding="utf-8") as stream:
            stream.write(now() + "\n")
    except FileExistsError:
        pass
    emit({"status": "cancellation_requested", "run": str(folder),
          "note": "Supervisor must observe request; inspect status for actual outcome"})
    return 0

def execute(folder):
    """Supervisor: execute only the explicit spec, never a shell implicitly."""
    spec = read_json(folder / "spec.json")
    with (folder / "execution.lock").open("x") as lock:
        lock.write(str(os.getpid()) + "\n")
    receipt = dict(spec)
    receipt.update(status="running", started_at=now(), supervisor_pid=os.getpid())
    write_json(folder / "receipt.json", receipt)
    start = time.monotonic()
    proc = None
    code = None
    result = "error"
    error = None
    lease = None
    lease_owned = False
    try:
        if spec.get("lease"):
            lease = lease_path(spec["lease"])
            try:
                lease.mkdir(mode=0o700)
                lease_owned = True
            except FileExistsError:
                raise RuleError("Device lease occupied; inspect existing owner: " + str(lease))
            write_json(lease / "owner.json", {"run": str(folder), "supervisor_pid": os.getpid(), "acquired": now()})
        if (folder / "cancel.request").exists():
            result = "cancelled"
            return 1
        if file_hash(folder / "context.json") != spec["context_sha256"]:
            raise RuleError("Context changed after submission")
        if file_hash(HERE) != spec["runner_sha256"]:
            raise RuleError("Runner changed after submission")
        before = identity(Path(spec["cwd"]))
        if before != spec["source_before"]:
            raise RuleError("Checkout changed after submission")
        env = dict(os.environ, AGENT_RUN_DIR=str(folder))
        with (folder / "run.log").open("xb") as log:
            proc = subprocess.Popen(spec["command"], cwd=spec["cwd"], env=env,
                                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=(os.name == "posix"))
            deadline = time.monotonic() + spec["timeout_s"]
            while True:
                code = proc.poll()
                if code is not None:
                    result = "success" if code == 0 else "failed"
                    break
                if (folder / "cancel.request").exists() or time.monotonic() >= deadline:
                    result = "cancelled" if (folder / "cancel.request").exists() else "timeout"
                    if os.name == "posix":
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        proc.kill()
                    code = proc.wait()
                    break
                time.sleep(0.05)
    except (OSError, RuleError, KeyboardInterrupt) as exc:
        error = str(exc)
        if proc is not None and proc.poll() is None:
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            code = proc.wait()
    finally:
        try:
            after = identity(Path(spec["cwd"]))
        except (OSError, RuleError):
            after = None
        receipt.update(status=result, finished_at=now(), exit_code=code,
                       elapsed_s=round(time.monotonic()-start, 6), source_after=after,
                       source_unchanged=(not spec["source_before"]["dirty"] and after == spec["source_before"]),
                       error=error, artifacts={})
        for name in ("spec.json", "context.json", "run.log", "metrics.json", "curve.json"):
            path = folder / name
            if path.exists() or path.is_symlink():
                try:
                    receipt["artifacts"][name] = file_hash(path)
                except RuleError as exc:
                    receipt.update(status="error", error=str(exc))
        write_json(folder / "receipt.json", receipt)
        # Fail closed if the supervisor dies before cleanup; never remove another lease.
        if lease_owned and (proc is None or proc.poll() is not None):
            (lease / "owner.json").unlink(missing_ok=True)
            lease.rmdir()
    return 0 if receipt["status"] == "success" else 1


def run(args):
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise RuleError("Specify a command after --")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise RuleError("Timeout must be positive and finite")
    cwd = Path.cwd().resolve()
    source = identity(cwd)
    if source["dirty"] and not args.allow_dirty:
        raise RuleError("Dirty checkout; commit intended inputs or use --allow-dirty for exploration")
    if args.lease:
        lease_path(args.lease)
    context = read_json(Path(args.context))
    if not isinstance(context, dict) or not context:
        raise RuleError("Context must be a nonempty JSON object")
    folder = Path(args.out).resolve()
    root = Path(source["root"])
    if folder.is_relative_to(root):
        relative = str(folder.relative_to(root))
        if not relative or git(root, "check-ignore", "-q", "--", relative, check=False).returncode != 0:
            raise RuleError("Run output must be outside the checkout or Git-ignored")
    folder.mkdir(parents=True, exist_ok=False)
    # Private by default on POSIX; the operator controls parent permissions.
    if os.name == "posix":
        folder.chmod(0o700)
    spec = {"schema": SCHEMA, "command": command, "cwd": str(cwd), "source_before": source,
            "timeout_s": args.timeout, "submitted_at": now(),
            "context_sha256": digest(json_bytes(context)), "runner_sha256": file_hash(HERE), "lease": args.lease}
    write_json(folder / "context.json", context)
    write_json(folder / "spec.json", spec)
    write_json(folder / "receipt.json", dict(spec, status="pending"))
    if args.detach:
        try:
            with (folder / "supervisor.log").open("xb") as log:
                proc = subprocess.Popen([sys.executable, str(HERE), "_execute", str(folder)],
                                        cwd=str(cwd), stdin=subprocess.DEVNULL, stdout=log,
                                        stderr=subprocess.STDOUT,
                                        start_new_session=(os.name == "posix"))
        except OSError as exc:
            write_json(folder / "receipt.json", dict(spec, status="error", error=str(exc)))
            raise
        emit({"status": "submitted", "supervisor_pid": proc.pid, "run": str(folder)})
        return 0
    rc = execute(folder)
    emit(read_json(folder / "receipt.json"))
    return rc


def verified(folder, require_metrics=False, matched=False):
    receipt = read_json(folder / "receipt.json")
    if receipt.get("schema") != SCHEMA or receipt.get("status") != "success" or receipt.get("exit_code") != 0:
        raise RuleError(f"Run not successfully completed: {folder}")
    artifacts = receipt.get("artifacts", {})
    required = {"spec.json", "context.json", "run.log"}
    if require_metrics:
        required.add("metrics.json")
    if not isinstance(artifacts, dict) or not required <= artifacts.keys():
        raise RuleError("Missing required receipt artifacts")
    for name, sha in artifacts.items():
        if name not in {"spec.json", "context.json", "run.log", "metrics.json", "curve.json"}:
            raise RuleError("Unknown receipt artifact")
        if file_hash(folder / name) != sha:
            raise RuleError(f"Artifact checksum mismatch: {name}")
    spec = read_json(folder / "spec.json")
    for key, value in spec.items():
        if receipt.get(key) != value:
            raise RuleError(f"Receipt/spec mismatch: {key}")
    if file_hash(folder / "context.json") != receipt.get("context_sha256"):
        raise RuleError("Context checksum mismatch")
    if matched and (receipt["source_before"]["dirty"] or not receipt["source_unchanged"]
                    or receipt["source_before"] != receipt["source_after"]):
        raise RuleError("Dirty or changed source is not eligible for matched comparison")
    if "metrics.json" in artifacts:
        metrics(folder / "metrics.json")
    return receipt


def status(args):
    emit(read_json(Path(args.run) / "receipt.json"))
    return 0


def logs(args):
    path = Path(args.run) / "run.log"
    if not 1 <= args.lines <= 1000:
        raise RuleError("Line count must be between 1 and 1000")
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        stream.seek(max(0, stream.tell() - 65536))
        data = stream.read(65536).decode("utf-8", errors="replace")
    print("\n".join(data.splitlines()[-args.lines:]))
    return 0


def verify(args):
    receipt = verified(Path(args.run), args.require_metrics)
    emit({"status": "verified", "revision": receipt["source_before"]["commit"],
          "source_unchanged": receipt["source_unchanged"],
          "dirty": receipt["source_before"]["dirty"], "artifacts": receipt["artifacts"],
          "note": "Integrity and execution checks, not independent scientific validation"})
    return 0


def compare(args):
    a, b = Path(args.baseline), Path(args.candidate)
    if a.resolve() == b.resolve():
        raise RuleError("Baseline and candidate must be different runs")
    ra, rb = verified(a, True, True), verified(b, True, True)
    if read_json(a / "context.json") != read_json(b / "context.json"):
        raise RuleError("Unmatched run contexts")
    if not ra.get("runner_sha256") or ra["runner_sha256"] != rb.get("runner_sha256"):
        raise RuleError("Unmatched runner revisions")
    ma, mb = metrics(a / "metrics.json"), metrics(b / "metrics.json")
    if ma.keys() != mb.keys():
        raise RuleError("Metric sets differ")
    rows = {k: {"baseline": ma[k], "candidate": mb[k], "delta": mb[k]-ma[k]} for k in ma}
    outcomes = []
    if args.gates:
        gates = read_json(Path(args.gates))
        if not isinstance(gates, dict) or not gates:
            raise RuleError("Gates must be a nonempty object")
        for metric, constraints in gates.items():
            if metric not in rows or not isinstance(constraints, dict) or not constraints:
                raise RuleError(f"Invalid or missing gate metric: {metric}")
            for kind, limit in constraints.items():
                if (kind not in {"min", "max", "min_delta", "max_delta"} or
                    not isinstance(limit, (int, float)) or isinstance(limit, bool) or not math.isfinite(limit)):
                    raise RuleError(f"Invalid gate: {metric}.{kind}")
                actual = rows[metric]["delta" if kind.endswith("_delta") else "candidate"]
                passed = actual >= limit if kind.startswith("min") else actual <= limit
                outcomes.append({"metric": metric, "gate": kind, "limit": limit,
                                 "actual": actual, "pass": passed})
    passed = all(g["pass"] for g in outcomes)
    emit({"baseline_revision": ra["source_before"]["commit"],
          "candidate_revision": rb["source_before"]["commit"],
          "metrics": rows, "elapsed_s": {"baseline": ra["elapsed_s"], "candidate": rb["elapsed_s"]},
          "gates": outcomes, "gate_sha256": file_hash(Path(args.gates)) if args.gates else None,
          "status": ("pass" if passed else "fail") if outcomes else "compared_no_gates",
          "note": "Matching recorded contexts and numerical gates are not independent validation"})
    return 0 if passed else 1


def curve(args):
    """Compare first observed threshold crossings without interpolation."""
    a, b = Path(args.baseline), Path(args.candidate)
    if a.resolve() == b.resolve():
        raise RuleError("Baseline and candidate must be different runs")
    ra, rb = verified(a, False, True), verified(b, False, True)
    if (read_json(a / "context.json") != read_json(b / "context.json") or
        not ra.get("runner_sha256") or ra["runner_sha256"] != rb.get("runner_sha256")):
        raise RuleError("Unmatched run contexts or runner revisions")
    if not math.isfinite(args.threshold):
        raise RuleError("Threshold must be finite")
    def first(folder, receipt):
        if "curve.json" not in receipt["artifacts"]:
            raise RuleError("Missing recorded curve.json")
        data = read_json(folder / "curve.json")
        if not isinstance(data, dict) or not isinstance(data.get(args.metric), list) or not data[args.metric]:
            raise RuleError(f"Missing curve metric: {args.metric}")
        previous = -1.0
        crossing = None
        for point in data[args.metric]:
            if not isinstance(point, dict) or set(point) != {"t_s", "value"}:
                raise RuleError("Curve points require t_s and value")
            t, value = point["t_s"], point["value"]
            if any(not isinstance(x, (int, float)) or isinstance(x, bool) or
                   not math.isfinite(x) for x in (t, value)) or t < 0 or t <= previous:
                raise RuleError("Curve times must increase strictly; times and values must be finite")
            previous = t
            passes = value >= args.threshold if args.direction == "ge" else value <= args.threshold
            if crossing is None and passes:
                crossing = t
        return {"first_observed_crossing_s": crossing, "last_sample_s": previous,
                "reached": crossing is not None}
    ba, ca = first(a, ra), first(b, rb)
    bt, ct = ba["first_observed_crossing_s"], ca["first_observed_crossing_s"]
    emit({"metric": args.metric, "threshold": args.threshold, "direction": args.direction,
          "baseline": ba, "candidate": ca,
          "speedup": bt / ct if bt is not None and ct is not None and ct > 0 else None,
          "note": "Discrete first observed crossings; null means not reached or ratio undefined. Inspect curve stability."})
    return 0


def learn(args):
    if not all(v.strip() for v in (args.scope, args.finding, args.evidence)):
        raise RuleError("Scope, finding and evidence are required")
    entry = {"schema": SCHEMA, "recorded_at": now(), "scope": args.scope,
             "finding": args.finding, "evidence": args.evidence}
    data = (json.dumps(entry, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(data) > 4096:
        raise RuleError("Finding too long; link a durable report instead")
    path = Path(args.inbox)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.write(fd, data) != len(data):
            raise RuleError("Incomplete append")
    finally:
        os.close(fd)
    emit({"status": "appended", "inbox": str(path), "scope": args.scope})
    return 0


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="action", required=True)
    s = subs.add_parser("install", help="Install/update managed rules and skills")
    s.add_argument("--target", required=True)
    s.add_argument("--profile", choices=["core", "research"], default="core")
    s.add_argument("--check", action="store_true")
    s.set_defaults(func=install)
    s = subs.add_parser("doctor")
    s.add_argument("--target", default=".")
    s.set_defaults(func=doctor)
    s = subs.add_parser("task")
    tasks = s.add_subparsers(dest="task_action", required=True)
    t = tasks.add_parser("new")
    t.add_argument("id")
    t.add_argument("--objective", required=True)
    t.set_defaults(func=task_new)
    t = tasks.add_parser("worktree")
    t.add_argument("id")
    t.add_argument("--path", required=True)
    t.add_argument("--base", required=True)
    t.set_defaults(func=task_worktree)
    s = subs.add_parser("scope")
    s.add_argument("--contract", required=True)
    s.set_defaults(func=scope)
    s = subs.add_parser("run")
    s.add_argument("--out", required=True)
    s.add_argument("--context", required=True)
    s.add_argument("--timeout", type=float, required=True)
    s.add_argument("--allow-dirty", action="store_true")
    s.add_argument("--detach", action="store_true")
    s.add_argument("--lease", help="Exclusive cooperative machine/device lease")
    s.add_argument("command", nargs=argparse.REMAINDER)
    s.set_defaults(func=run)
    s = subs.add_parser("cancel")
    s.add_argument("run")
    s.set_defaults(func=cancel)
    for name, func in (("status", status), ("logs", logs), ("verify", verify)):
        s = subs.add_parser(name)
        s.add_argument("run")
        if name == "logs":
            s.add_argument("--lines", type=int, default=30)
        if name == "verify":
            s.add_argument("--require-metrics", action="store_true")
        s.set_defaults(func=func)
    s = subs.add_parser("compare")
    s.add_argument("baseline")
    s.add_argument("candidate")
    s.add_argument("--gates")
    s.set_defaults(func=compare)
    s = subs.add_parser("curve")
    s.add_argument("baseline")
    s.add_argument("candidate")
    s.add_argument("--metric", required=True)
    s.add_argument("--threshold", required=True, type=float)
    s.add_argument("--direction", choices=["ge", "le"], default="ge")
    s.set_defaults(func=curve)
    s = subs.add_parser("learn")
    for key in ("inbox", "scope", "finding", "evidence"):
        s.add_argument("--" + key, required=True)
    s.set_defaults(func=learn)
    import agent_kb
    agent_kb.register(subs)
    import agent_ops
    agent_ops.register(subs)
    s = subs.add_parser("_execute", help=argparse.SUPPRESS)
    s.add_argument("folder")
    s.set_defaults(func=lambda args: execute(Path(args.folder)))
    return p


def main():
    try:
        args = parser().parse_args()
        return args.func(args)
    except (RuleError, OSError, ValueError, KeyError, TypeError, OverflowError, sqlite3.Error, subprocess.TimeoutExpired) as exc:
        print(f"agent-rules: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
