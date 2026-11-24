"""Evidence-triggered skill discovery, creation and tracked repository promotion."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

import agent_kb as kb

MIN_TASKS = 3
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SCHEMA = """
CREATE TABLE IF NOT EXISTS skill_uses(
 workflow TEXT NOT NULL, project TEXT NOT NULL, task TEXT NOT NULL,
 summary TEXT NOT NULL, evidence TEXT NOT NULL, recorded TEXT NOT NULL,
 PRIMARY KEY(workflow,project,task));
CREATE TABLE IF NOT EXISTS skill_promotions(
 workflow TEXT NOT NULL, scope TEXT NOT NULL, repository TEXT NOT NULL,
 skill_path TEXT NOT NULL, commit_sha TEXT NOT NULL, disposition TEXT NOT NULL,
 recorded TEXT NOT NULL, PRIMARY KEY(workflow,scope));
CREATE INDEX IF NOT EXISTS skill_uses_project ON skill_uses(project,workflow);
"""


def git(root,*args):
    p=subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,encoding="utf-8",errors="replace")
    if p.returncode:raise ValueError("Git check failed: "+p.stderr[-1000:])
    return p.stdout.strip()


def root_path(target):
    root=Path(target).expanduser().resolve()
    if not root.is_dir() or Path(git(root,"rev-parse","--show-toplevel")).resolve()!=root:
        raise ValueError("Target must be the actual Git root")
    return root


def scope_key(scope,project):
    if scope=="shared":
        if project is not None:raise ValueError("Do not supply a project for shared skills")
        return "global"
    if not project or project=="global":raise ValueError("Project skills require a stable project key")
    return kb.validate_key(project)


def skill_root(root,scope):
    if scope=="shared":
        if not all((root/p).is_file() for p in ("rules/core.md","tools/agent.py","AGENT_INSTALL.md")):
            raise ValueError("Shared skills must be created in the canonical agent-rules checkout")
        return "skills"
    return ".agents/skills"


def safe_path(root,relative):
    path=root
    for part in Path(relative).parts:
        if part in ("..",".") or Path(part).is_absolute():raise ValueError("Unsafe skill path")
        path=path/part
        if path.is_symlink():raise ValueError("Refusing symlink: "+str(path))
    return path


def inventory(root):
    records=[]
    for folder in ("skills",".agents/skills"):
        path=safe_path(root,folder)
        if not path.exists():continue
        if not path.is_dir():raise ValueError("Skill root is not a directory")
        for child in sorted(path.iterdir()):
            if child.is_symlink():raise ValueError("Refusing symlink skill: "+str(child))
            if not child.is_dir():continue
            skill=child/"SKILL.md"
            if skill.is_symlink():raise ValueError("Refusing symlink skill document")
            if not skill.is_file():continue
            if skill.stat().st_size>256000:raise ValueError("Oversized skill document")
            content=skill.read_text(encoding="utf-8")
            marker=re.search(r"(?m)^<!-- agent-rules-workflow: ([A-Za-z0-9_.:/-]+) -->$",content)
            description=re.search(r"(?m)^description: (.+)$",content)
            records.append({"path":skill.relative_to(root).as_posix(),"name":child.name,
                "workflow":marker.group(1) if marker else None,
                "description":description.group(1) if description else None})
    return records


def count_uses(c,workflow,scope):
    sql="SELECT count(*) AS tasks,count(DISTINCT project) AS projects FROM skill_uses WHERE workflow=?"
    params=[workflow]
    if scope!="global":sql+=" AND project=?";params.append(scope)
    return dict(c.execute(sql,params).fetchone())


def promotion(c,workflow,scope):
    row=c.execute("SELECT * FROM skill_promotions WHERE workflow=? AND scope IN (?, 'global') ORDER BY scope='global' DESC LIMIT 1",(workflow,scope)).fetchone()
    return dict(row) if row else None


def record(c,a):
    workflow=kb.validate_key(a.workflow);project=kb.validate_key(a.project);task=kb.validate_key(a.task)
    if project=="global":raise ValueError("Use an actual project identity, not global")
    summary=kb.text(a.summary,600,"validated workflow summary")
    evidence=kb.text(a.evidence,1000,"validation evidence")
    c.execute("BEGIN IMMEDIATE")
    old=c.execute("SELECT summary,evidence FROM skill_uses WHERE workflow=? AND project=? AND task=?",(workflow,project,task)).fetchone()
    if old and (old["summary"],old["evidence"])!=(summary,evidence):
        raise ValueError("This workflow/task was already recorded with different evidence")
    if not old:
        c.execute("INSERT INTO skill_uses VALUES(?,?,?,?,?,?)",(workflow,project,task,summary,evidence,kb.now()))
    counts=count_uses(c,workflow,"global")
    local=count_uses(c,workflow,project)
    existing=promotion(c,workflow,project)
    c.commit()
    kb.emit({"status":"unchanged" if old else "recorded","workflow":workflow,
             "total":counts,"project_total":local,"minimum_distinct_tasks":MIN_TASKS,
             "action":"reuse_or_improve_existing" if existing else
                 "evaluate_and_create_or_extend_skill" if counts["tasks"]>=MIN_TASKS else "continue_observing",
             "existing":existing,"note":"Distinct reported validated tasks, not independently audited executions."})


def candidates(c,a):
    project=kb.validate_key(a.project) if a.project else None
    if project=="global":raise ValueError("Omit --project for all projects")
    if not 1<=a.limit<=100:raise ValueError("Limit must be 1–100")
    where="WHERE project=?" if project else ""
    params=[project] if project else []
    items=kb.rows(c,"SELECT workflow,count(*) AS tasks,count(DISTINCT project) AS projects FROM skill_uses "+where+
        " GROUP BY workflow HAVING count(*)>=? ORDER BY count(*) DESC,workflow LIMIT ?",(*params,MIN_TASKS,a.limit))
    for row in items:
        scope=project or "global"
        existing=promotion(c,row["workflow"],scope)
        sql="SELECT project,task,summary,evidence FROM skill_uses WHERE workflow=?"
        args=[row["workflow"]]
        if project:sql+=" AND project=?";args.append(project)
        row["examples"]=kb.rows(c,sql+" ORDER BY recorded DESC LIMIT 5",args)
        row["existing"]=existing
        row["action"]="reuse_or_improve_existing" if existing else "evaluate_and_create_or_extend_skill"
    kb.emit({"minimum_distinct_tasks":MIN_TASKS,"candidates":items,
             "note":"Private evidence references. Inventory existing skills and validate generalizability before creating."})


def strings(value,label,limit=12,required=True):
    if not isinstance(value,list) or len(value)>limit or (required and not value):
        raise ValueError(label+" must be a bounded list")
    out=[kb.text(x,1200,label) for x in value]
    if any("\n" in x or "\r" in x for x in out):
        raise ValueError("Use single-line entries in "+label)
    return out


def render(spec):
    required={"workflow","name","scope","description","steps","verification","failure_handling","public_evidence"}
    if not isinstance(spec,dict) or required-set(spec) or set(spec)-required-{"project","prerequisites","when_not_to_use"}:
        raise ValueError("Missing or unknown skill spec fields")
    workflow=kb.validate_key(spec["workflow"])
    name=spec["name"]
    if not isinstance(name,str) or not SLUG.fullmatch(name) or len(name)>64:
        raise ValueError("Skill name must be a lowercase hyphenated slug of at most 64 characters")
    if spec["scope"] not in ("shared","project"):raise ValueError("Invalid skill scope")
    scope=scope_key(spec["scope"],spec.get("project"))
    description=kb.text(spec["description"],400,"description")
    if "\n" in description or "\r" in description:raise ValueError("Description must be one line")
    # JSON-quoted scalars are valid YAML; no untrusted raw frontmatter.
    parts=["---","name: "+name,"description: "+json.dumps(description,ensure_ascii=False),"---","",
           "# "+name,"","<!-- agent-rules-workflow: "+workflow+" -->",""]
    for heading,key,required_list,numbered in (
        ("Prerequisites","prerequisites",False,False),("Procedure","steps",True,True),
        ("Verification","verification",True,False),("Failure handling","failure_handling",True,False),
        ("When not to use","when_not_to_use",False,False),("Repository-safe evidence","public_evidence",True,False)):
        vals=strings(spec.get(key,[]),key,required=required_list)
        if vals:
            parts+=["## "+heading,""]+[(str(i+1)+". " if numbered else "- ")+v for i,v in enumerate(vals)]+[""]
    content="\n".join(parts)
    if len(content.encode("utf-8"))>12000:raise ValueError("Skill too long; link a reference or tool instead")
    return name,workflow,scope,content


def create(c,a):
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
    name,workflow,scope,content=render(spec)
    root=root_path(a.target);folder=skill_root(root,spec["scope"])
    counts=count_uses(c,workflow,scope)
    if counts["tasks"]<MIN_TASKS:raise ValueError("Insufficient distinct validated tasks; collect "+str(MIN_TASKS)+" before promotion")
    existing=promotion(c,workflow,scope)
    if existing:raise ValueError("Workflow already promoted; reuse or improve the existing skill: "+existing["skill_path"])
    relative=folder+"/"+name+"/SKILL.md"
    dest=safe_path(root,relative)
    for r in inventory(root):
        if r["name"]==name or r["workflow"]==workflow:
            # Existing exact skill is never overwritten by a generator.
            raise ValueError("Existing skill overlaps by name/workflow; review and extend instead: "+r["path"])
    if a.apply:
        if not a.confirm_repo_safe:raise ValueError("Explicit repository-safe content confirmation required")
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("xb") as stream:stream.write(content.encode("utf-8"))
    kb.emit({"status":"created" if a.apply else "preview","path":relative,
             "workflow":workflow,"scope":scope,"validated_use_counts":counts,
             "sha256":hashlib.sha256(content.encode("utf-8")).hexdigest(),"content":content,
             "note":"Review inventory for semantic overlap, run procedure checks, commit authorized changes, then skill complete. No Git mutation performed."})


def complete(c,a):
    workflow=kb.validate_key(a.workflow);scope=scope_key(a.scope,a.project)
    root=root_path(a.target);folder=skill_root(root,a.scope)
    parts=a.skill_path.split("/")
    prefix=folder.split("/")
    if parts[:len(prefix)]!=prefix or len(parts)!=len(prefix)+2 or not SLUG.fullmatch(parts[-2]) or parts[-1]!="SKILL.md":
        raise ValueError("Skill path does not match the selected scope")
    if not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}",a.commit):
        raise ValueError("Use an exact committed Git SHA")
    if git(root,"rev-parse",a.commit+"^{commit}")!=a.commit:
        raise ValueError("Commit identity differs")
    git(root,"merge-base","--is-ancestor",a.commit,"HEAD")
    # Verify committed content, not an uncommitted claim or a local artifact.
    content=git(root,"show",a.commit+":"+a.skill_path)
    if not content.startswith("---\n") or not re.search(r"(?m)^description: .+$",content):
        raise ValueError("Commit does not contain a skill document")
    if a.disposition=="created" and "<!-- agent-rules-workflow: "+workflow+" -->" not in content:
        raise ValueError("Created skill lacks matching workflow marker")
    if a.disposition in ("created","extended"):
        changed=git(root,"diff-tree","--root","-m","--no-commit-id","--name-only","-r",a.commit,"--",a.skill_path)
        if a.skill_path not in changed.splitlines():raise ValueError("Commit did not change the reported skill")
    if count_uses(c,workflow,scope)["tasks"]<MIN_TASKS:
        raise ValueError("Insufficient distinct validated uses for promotion")
    # Repository label is stable and explicitly provided; private local path is not exported.
    repository=kb.validate_key(a.repository)
    c.execute("BEGIN IMMEDIATE")
    old=c.execute("SELECT * FROM skill_promotions WHERE workflow=? AND scope=?",(workflow,scope)).fetchone()
    values=(repository,a.skill_path,a.commit,a.disposition)
    if old:
        if tuple(old[k] for k in ("repository","skill_path","commit_sha","disposition"))!=values:
            raise ValueError("Workflow already has a recorded skill promotion; improve that skill through normal Git history")
    else:
        c.execute("INSERT INTO skill_promotions VALUES(?,?,?,?,?,?,?)",(workflow,scope,*values,kb.now()))
    c.commit()
    kb.emit({"status":"unchanged" if old else "promoted","workflow":workflow,"scope":scope,
             "repository":repository,"path":a.skill_path,"commit":a.commit,"disposition":a.disposition,
             "note":"Verified local Git commit; remote publication/PR and procedure validity must be established separately."})


def list_inventory(c,a):
    kb.emit({"skills":inventory(root_path(a.target))})


def dispatch(a):
    c=kb.connect(a)
    try:
        c.executescript(SCHEMA)
        a.handler(c,a)
    finally:c.close()
    return 0


def register(subs):
    p=subs.add_parser("skill",help="Discover repeated workflows and create reusable repository skills")
    p.add_argument("--db",help="Use the same private knowledge database")
    ss=p.add_subparsers(dest="skill_action",required=True)
    def sub(name,handler):
        s=ss.add_parser(name);s.set_defaults(func=dispatch,handler=handler);return s
    s=sub("record",record)
    for k in ("workflow","project","task","summary","evidence"):s.add_argument("--"+k,required=True)
    s=sub("candidates",candidates);s.add_argument("--project");s.add_argument("--limit",type=int,default=20)
    s=sub("inventory",list_inventory);s.add_argument("--target",required=True)
    s=sub("create",create);s.add_argument("--target",required=True);s.add_argument("--spec",required=True)
    s.add_argument("--apply",action="store_true");s.add_argument("--confirm-repo-safe",action="store_true")
    s=sub("complete",complete)
    for k in ("workflow","repository","target","skill-path","commit"):s.add_argument("--"+k,required=True)
    s.add_argument("--scope",choices=["shared","project"],required=True);s.add_argument("--project")
    s.add_argument("--disposition",choices=["created","extended","reused"],required=True)
