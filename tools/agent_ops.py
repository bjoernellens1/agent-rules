"""Explicit scheduler, project and isolated evaluator adapters; standard library only."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().with_name("agent.py")
NAME=re.compile(r"^[a-z0-9]([-a-z0-9]{0,61}[a-z0-9])?$")
IMAGE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*@sha256:[a-f0-9]{64}$")

def emit(value):
    print(json.dumps(value,indent=2,sort_keys=True,allow_nan=False))

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))

def positive(v,label,maxval=1000000):
    if type(v)!=int or not 1<=v<=maxval:raise ValueError("Invalid "+label)
    return v

def name(v,label):
    if not isinstance(v,str) or not NAME.fullmatch(v):raise ValueError("Invalid "+label)
    return v

def vector(v):
    if not isinstance(v,list) or not v or any(not isinstance(s,str) or not s or "\x00" in s for s in v):
        raise ValueError("Command must be a nonempty argv array")
    return v

def image(v):
    if not isinstance(v,str) or not IMAGE.fullmatch(v):raise ValueError("Use a digest-pinned image")
    return v

def command(argv,timeout=60,stdin=None):
    r=subprocess.run(argv,input=stdin,text=True,capture_output=True,timeout=timeout)
    if r.returncode:raise ValueError("Command failed ("+str(r.returncode)+"): "+r.stderr[-2000:])
    return r.stdout

def confirm(a):
    if not a.confirm:raise ValueError("Explicit --confirm required")

def kube_base(s):
    context=s.get("context")
    if not isinstance(context,str) or not context or context.startswith("-"):raise ValueError("Explicit Kubernetes context required")
    return ["kubectl","--context",context,"--namespace",name(s["namespace"],"namespace")]

def roles_ok(roles,stage):
    if stage=="candidate":
        return {"source","output"}<=roles and roles<={"source","data","output"}
    if stage=="evaluator":
        return roles=={"evaluator","data","predictions","output"}
    return False

def kube_manifest(s):
    kube_base(s)
    job=name(s["name"],"job name")
    if len(job)>50:raise ValueError("Job name limited to 50 characters")
    backend=s.get("backend","job")
    if backend not in ("job","argo"):raise ValueError("Backend must be job or argo")
    limits=s["resources"]
    resources={"cpu":str(positive(limits["cpu"],"CPU",512)),
               "memory":str(positive(limits["memory_mib"],"memory MiB"))+"Mi"}
    gpu=limits.get("gpu",0)
    if type(gpu)!=int or not 0<=gpu<=64:raise ValueError("Invalid GPU count")
    if gpu:
        resource=limits.get("gpu_resource")
        if not isinstance(resource,str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]*/[A-Za-z0-9_.-]+",resource):
            raise ValueError("Specify the actual advertised GPU resource name")
        resources[resource]=str(gpu)
    stage=s.get("stage","candidate")
    if not roles_ok(set(s["volumes"]),stage):raise ValueError("Invalid volume roles for stage")
    claims=set();mounts=[];volumes=[]
    for role,claim in s["volumes"].items():
        name(claim,"PVC")
        if claim in claims:raise ValueError("PVC roles must use distinct claims")
        claims.add(claim);ro=role!="output"
        mounts.append({"name":role,"mountPath":"/"+role,"readOnly":ro})
        volumes.append({"name":role,"persistentVolumeClaim":{"claimName":claim,"readOnly":ro}})
    mounts.append({"name":"tmp","mountPath":"/tmp"})
    volumes.append({"name":"tmp","emptyDir":{"sizeLimit":"1024Mi"}})
    sec={"runAsNonRoot":True,"runAsUser":positive(s.get("uid",1000),"uid",2147483647),
         "runAsGroup":positive(s.get("gid",1000),"gid",2147483647),"allowPrivilegeEscalation":False,
         "readOnlyRootFilesystem":True,"capabilities":{"drop":["ALL"]},"seccompProfile":{"type":"RuntimeDefault"}}
    labels=s.get("labels",{})
    if not isinstance(labels,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in labels.items()):
        raise ValueError("Labels must be strings")
    labels={**labels,"agent-rules/stage":stage}
    deadline=positive(s["timeout_s"],"deadline",604800)
    container={"name":"runner","image":image(s["image"]),"command":vector(s["command"]),
               "resources":{"requests":resources,"limits":resources},"securityContext":sec,
               "volumeMounts":mounts,"workingDir":"/evaluator" if stage=="evaluator" else "/source"}
    pod={"restartPolicy":"Never","automountServiceAccountToken":False,"enableServiceLinks":False,
         "containers":[container],"volumes":volumes}
    if s.get("scheduler_name"):pod["schedulerName"]=name(s["scheduler_name"],"scheduler name")
    if s.get("node_selector"):
        if not isinstance(s["node_selector"],dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in s["node_selector"].items()):
            raise ValueError("Invalid node selector")
        pod["nodeSelector"]=s["node_selector"]
    metadata={"name":job,"namespace":s["namespace"],"labels":labels}
    if backend=="job":
        return {"apiVersion":"batch/v1","kind":"Job","metadata":metadata,
                "spec":{"backoffLimit":0,"activeDeadlineSeconds":deadline,
                        "template":{"metadata":{"labels":labels},"spec":pod}}}
    # Argo uses its own executor and service-account requirements. Site RBAC
    # and network policies remain necessary; this is not a security boundary.
    template={"name":"run","container":{k:v for k,v in container.items() if k!="name"},
              "activeDeadlineSeconds":deadline,"metadata":{"labels":labels}}
    for k in ("schedulerName","nodeSelector"):
        if k in pod:template[k]=pod[k]
    return {"apiVersion":"argoproj.io/v1alpha1","kind":"Workflow","metadata":metadata,
            "spec":{"entrypoint":"run","activeDeadlineSeconds":deadline,"volumes":volumes,
                    "serviceAccountName":name(s["service_account"],"Argo service account"),
                    "templates":[template]}}

def scheduler(a):
    if a.operation=="local-submit":
        confirm(a)
        argv=[sys.executable,str(HERE),"run","--detach","--out",a.out,"--context",a.run_context,
              "--timeout",str(a.timeout),"--lease",a.device,"--",*vector(a.command[1:] if a.command and a.command[0]=="--" else a.command)]
        return subprocess.call(argv)
    if a.operation=="fetch":
        source=Path(a.source).resolve();dest=Path(a.destination)
        if not source.is_dir() or dest.exists() or dest.resolve().is_relative_to(source):
            raise ValueError("Source must be directory, destination fresh and outside source")
        for path in source.rglob("*"):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):raise ValueError("Unsafe artifact entry")
        shutil.copytree(source,dest)
        emit({"destination":str(dest),"note":"Copied mounted artifacts; verify receipts independently"});return 0
    s=load(a.spec);manifest=kube_manifest(s)
    if a.operation=="plan":emit(manifest);return 0
    base=kube_base(s);kind="job" if s.get("backend","job")=="job" else "workflow"
    if a.operation=="submit":
        confirm(a);print(command(base+["create","-f","-","-o","json"],stdin=json.dumps(manifest)))
    elif a.operation=="status":
        print(command(base+["get",kind,s["name"],"-o","json"]))
    elif a.operation=="logs":
        n=positive(a.lines,"lines",1000)
        if kind=="job":print(command(base+["logs","job/"+s["name"],"--tail="+str(n)]))
        else:
            pod=name(a.pod,"workflow pod")
            obj=json.loads(command(base+["get","pod",pod,"-o","json"]))
            if obj["metadata"]["labels"].get("workflows.argoproj.io/workflow")!=s["name"]:
                raise ValueError("Pod is not labeled for the specified workflow")
            print(command(base+["logs",pod,"-c","main","--tail="+str(n)]))
    elif a.operation=="usage":
        selector=("job-name=" if kind=="job" else "workflows.argoproj.io/workflow=")+s["name"]
        pods=json.loads(command(base+["get","pods","-l",selector,"-o","json"]))
        records=[{"name":p["metadata"]["name"],"phase":p.get("status",{}).get("phase"),
                  "started":p.get("status",{}).get("startTime"),
                  "resources":[{"container":c["name"],"resources":c.get("resources",{})} for c in p["spec"]["containers"]]}
                 for p in pods.get("items",[])]
        top=subprocess.run(base+["top","pod","-l",selector,"--containers"],text=True,capture_output=True,timeout=60)
        emit({"pods":records,"cpu_memory_snapshot":top.stdout if top.returncode==0 else None,
              "gpu_utilization":None,"note":"Allocations and available metrics-server snapshots, not GPU-hours or measured device utilization"})
    elif a.operation=="cancel":
        confirm(a)
        obj=json.loads(command(base+["get",kind,s["name"],"-o","json"]))
        if obj["metadata"]["uid"]!=a.uid:raise ValueError("Resource UID differs; refusing cancellation")
        # kubectl delete by name is not an atomic UID-preconditioned deletion.
        # Use unique names, do not reuse names concurrently.
        print(command(base+["delete",kind,s["name"],"--wait=false"]))
    return 0

def sandbox_plan(s):
    engine=s.get("engine","docker")
    if engine not in ("docker","podman"):raise ValueError("Use docker or podman")
    stage=s["stage"];mounts=s["mounts"]
    if not roles_ok(set(mounts),stage):raise ValueError("Invalid mount roles for stage")
    paths={}
    for role,value in mounts.items():
        if not isinstance(value,str) or not Path(value).is_absolute():raise ValueError("Use absolute mount paths")
        original=Path(value)
        if original.is_symlink():raise ValueError("No symlink mounts")
        p=original.resolve()
        if not p.is_dir() or "," in str(p) or "\n" in str(p):raise ValueError("Unsafe or missing mount")
        paths[role]=p
    for a in paths:
        for b in paths:
            if a!=b and paths[a].is_relative_to(paths[b]):raise ValueError("Mount roots must be disjoint")
    if any(paths["output"].iterdir()):raise ValueError("Use a fresh empty output directory")
    uid=positive(s.get("uid",1000),"uid",2147483647);gid=positive(s.get("gid",1000),"gid",2147483647)
    cpu=positive(s["cpu"],"CPU",512);mem=positive(s["memory_mib"],"memory MiB")
    timeout=positive(s["timeout_s"],"timeout",604800)
    argv=[engine,"run","--rm","--pull=never","--network=none","--read-only",
          "--cap-drop=ALL","--security-opt=no-new-privileges","--pids-limit=512",
          "--user",f"{uid}:{gid}","--cpus",str(cpu),"--memory",str(mem)+"m",
          "--tmpfs","/tmp:rw,nosuid,nodev,size=512m","--workdir","/evaluator" if stage=="evaluator" else "/source"]
    for role,p in paths.items():
        argv+=["--mount",f"type=bind,source={p},target=/{role}"+(",readonly" if role!="output" else "")]
    argv += ["--entrypoint",vector(s["command"])[0],image(s["image"]),*s["command"][1:]]
    return {"argv":argv,"stage":stage,"timeout_s":timeout,
            "note":"CPU sandbox; trusted evaluator must not execute candidate code or deserialize unsafe predictions"}

def sandbox(a):
    plan=sandbox_plan(load(a.spec))
    if a.operation=="plan":emit(plan);return 0
    confirm(a);tag="agent-rules-"+uuid.uuid4().hex
    argv=plan["argv"];argv[2:2]=["--name",tag]
    try:return subprocess.call(argv,timeout=plan["timeout_s"])
    except (subprocess.TimeoutExpired,KeyboardInterrupt):
        subprocess.run([argv[0],"rm","-f",tag],capture_output=True,timeout=30)
        raise ValueError("Sandbox interrupted or timed out")

def project(a):
    commands=load(a.config)["commands"]
    if not isinstance(commands,dict):raise ValueError("commands must be an object")
    for k,v in commands.items():name(k,"command name");vector(v)
    if a.operation=="list":emit({"commands":commands});return 0
    if a.name not in commands:raise ValueError("Unknown project command")
    if a.operation=="plan":emit({"argv":commands[a.name]});return 0
    confirm(a)
    return subprocess.call([sys.executable,str(HERE),"run","--out",a.out,"--context",a.run_context,
                            "--timeout",str(a.timeout),"--",*commands[a.name]])

def register(subs):
    s=subs.add_parser("scheduler",help="Local and Kubernetes/Argo adapters")
    ss=s.add_subparsers(dest="operation",required=True)
    for op in ("plan","submit","status","logs","usage","cancel"):
        p=ss.add_parser(op);p.add_argument("--spec",required=True);p.set_defaults(func=scheduler)
        if op in ("submit","cancel"):p.add_argument("--confirm",action="store_true")
        if op=="cancel":p.add_argument("--uid",required=True)
        if op=="logs":p.add_argument("--lines",type=int,default=30);p.add_argument("--pod")
    p=ss.add_parser("local-submit");p.set_defaults(func=scheduler)
    p.add_argument("--device",required=True);p.add_argument("--out",required=True);p.add_argument("--context",dest="run_context",required=True)
    p.add_argument("--timeout",type=float,required=True);p.add_argument("--confirm",action="store_true");p.add_argument("command",nargs=argparse.REMAINDER)
    p=ss.add_parser("fetch");p.set_defaults(func=scheduler);p.add_argument("--source",required=True);p.add_argument("--destination",required=True)
    s=subs.add_parser("sandbox",help="Plan/run isolated candidate or evaluator container")
    ss=s.add_subparsers(dest="operation",required=True)
    for op in ("plan","run"):
        p=ss.add_parser(op);p.add_argument("--spec",required=True);p.set_defaults(func=sandbox)
        if op=="run":p.add_argument("--confirm",action="store_true")
    s=subs.add_parser("project",help="Run canonical project-specific argv")
    ss=s.add_subparsers(dest="operation",required=True)
    for op in ("list","plan","run"):
        p=ss.add_parser(op);p.add_argument("--config",required=True);p.set_defaults(func=project)
        if op!="list":p.add_argument("name")
        if op=="run":
            p.add_argument("--out",required=True);p.add_argument("--context",dest="run_context",required=True);p.add_argument("--timeout",type=float,required=True);p.add_argument("--confirm",action="store_true")
