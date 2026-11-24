"""Private, explicit task telemetry and paired agent benchmark analysis."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import statistics

REQUIRED=("id","campaign","variant","task","trial","protocol_sha256","base_commit","harness","model","outcome","elapsed_s","evidence")
OPTIONAL=("harness_version","model_version","input_tokens","output_tokens","cached_tokens","cost_usd","gpu_seconds","human_interventions","rework_count","regressions")
METRICS=("elapsed_s","input_tokens","output_tokens","cached_tokens","cost_usd","gpu_seconds","human_interventions","rework_count","regressions")
def emit(x):print(json.dumps(x,indent=2,sort_keys=True,allow_nan=False))
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"),parse_constant=lambda x:(_ for _ in ()).throw(ValueError("Invalid JSON number")))
def validate(r):
    if not isinstance(r,dict) or set(REQUIRED)-set(r) or set(r)-set(REQUIRED)-set(OPTIONAL):
        raise ValueError("Telemetry has missing or unknown fields")
    for k in REQUIRED:
        if k in ("elapsed_s","trial"):continue
        if not isinstance(r[k],str) or not r[k].strip() or len(r[k])>1000:raise ValueError("Invalid "+k)
    for k in ("model_version","harness_version"):
        if k in r and r[k] is not None and (not isinstance(r[k],str) or len(r[k])>200):raise ValueError("Invalid "+k)
    if not re.fullmatch(r"[a-f0-9]{64}",r["protocol_sha256"]) or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}",r["base_commit"]):
        raise ValueError("Use immutable protocol SHA-256 and Git commit")
    if type(r["trial"])!=int or r["trial"]<0:raise ValueError("Invalid trial")
    if r["outcome"] not in ("accepted","rejected","blocked","timeout"):raise ValueError("Invalid outcome")
    for k in METRICS:
        v=r.get(k)
        if v is None and k!="elapsed_s":continue
        if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<0:
            raise ValueError("Invalid "+k)
        if k in ("input_tokens","output_tokens","cached_tokens","human_interventions","rework_count","regressions") and type(v)!=int:raise ValueError("Count must be integer: "+k)
    return r
def connect(a):
    home=Path(os.environ.get("AGENT_RULES_HOME",Path.home()/".local/share/agent-rules")).expanduser()
    path=Path(a.db or home/"telemetry.sqlite3").expanduser()
    if path.is_symlink():raise ValueError("Refusing symlink DB")
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if not path.exists():
        try:
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
        except FileExistsError:pass
    if os.name=="posix" and path.stat().st_mode&0o077:raise ValueError("Telemetry DB must be private (chmod 600)")
    c=sqlite3.connect(path,timeout=20)
    c.execute("CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,campaign TEXT,variant TEXT,task TEXT,trial INTEGER,payload TEXT,UNIQUE(campaign,variant,task,trial))")
    c.commit();return c
def record(c,a):
    r=validate(read(a.input));payload=json.dumps(r,sort_keys=True,allow_nan=False)
    c.execute("BEGIN IMMEDIATE")
    old=c.execute("SELECT payload FROM attempts WHERE id=?",(r["id"],)).fetchone()
    if old and old[0]!=payload:raise ValueError("Run ID already exists with different contents")
    if not old:c.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?)",(r["id"],r["campaign"],r["variant"],r["task"],r["trial"],payload))
    c.commit();emit({"status":"unchanged" if old else "recorded","id":r["id"]})
def records(c,campaign,variant=None):
    sql="SELECT payload FROM attempts WHERE campaign=?";params=[campaign]
    if variant is not None:sql+=" AND variant=?";params.append(variant)
    return [validate(json.loads(r[0])) for r in c.execute(sql+" ORDER BY task,trial",params)]
def export(c,a):
    for r in records(c,a.campaign):print(json.dumps(r,sort_keys=True,allow_nan=False))
def compare(c,a):
    if a.baseline==a.candidate:raise ValueError("Select distinct variants")
    aa=records(c,a.campaign,a.baseline);bb=records(c,a.campaign,a.candidate)
    def key(r):return (r["task"],r["trial"])
    left={key(r):r for r in aa};right={key(r):r for r in bb}
    if not left or left.keys()!=right.keys():raise ValueError("Unmatched task/trial sets; report incomplete campaign before comparing")
    pairs=[(left[k],right[k]) for k in sorted(left)]
    for x,y in pairs:
        if (x["protocol_sha256"],x["base_commit"])!=(y["protocol_sha256"],y["base_commit"]):
            raise ValueError("Mismatched protected protocol or baseline revision")
    both=[(x,y) for x,y in pairs if x["outcome"]==y["outcome"]=="accepted"]
    def summarize(data):
        return {"n":len(data),"accepted":sum(r["outcome"]=="accepted" for r in data),
                "outcomes":{k:sum(r["outcome"]==k for r in data) for k in ("accepted","rejected","blocked","timeout")},
                "harness_models":sorted({r["harness"]+"/"+r["model"] for r in data})}
    comparisons={}
    for k in METRICS:
        valid=[(x[k],y[k]) for x,y in both if x.get(k) is not None and y.get(k) is not None]
        comparisons[k]={"paired_count":len(valid),
            "baseline_median":statistics.median(x for x,y in valid) if valid else None,
            "candidate_median":statistics.median(y for x,y in valid) if valid else None,
            "median_paired_delta":statistics.median(y-x for x,y in valid) if valid else None}
    emit({"campaign":a.campaign,"pairs":len(pairs),"both_accepted":len(both),
          "baseline":summarize(aa),"candidate":summarize(bb),
          "accepted_pair_metrics":comparisons,
          "all_attempt_elapsed_s":{"baseline":sum(r["elapsed_s"] for r in aa),"candidate":sum(r["elapsed_s"] for r in bb)},
          "note":"Failures are retained in acceptance rates and all-attempt time. Conditional metrics use jointly accepted pairs only; missing is null. External evaluator must establish outcomes and protocol integrity."})
def dispatch(a):
    c=connect(a)
    try:a.handler(c,a)
    finally:c.close()
    return 0
def register(subs):
    s=subs.add_parser("telemetry",help="Record and export private agent task evidence")
    s.add_argument("--db");ss=s.add_subparsers(dest="operation",required=True)
    p=ss.add_parser("record");p.add_argument("--input",required=True);p.set_defaults(func=dispatch,handler=record)
    p=ss.add_parser("export");p.add_argument("--campaign",required=True);p.set_defaults(func=dispatch,handler=export)
    s=subs.add_parser("benchmark",help="Matched agent/harness/model benchmark analysis")
    s.add_argument("--db");ss=s.add_subparsers(dest="operation",required=True)
    p=ss.add_parser("compare");p.add_argument("--campaign",required=True);p.add_argument("--baseline",required=True);p.add_argument("--candidate",required=True);p.set_defaults(func=dispatch,handler=compare)
