import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

CLI=Path(__file__).resolve().parents[1]/"tools/agent.py"

class ExtensionsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.env=dict(os.environ,AGENT_RULES_HOME=str(self.root/"private"),PYTHONIOENCODING="utf-8")
        self.project=self.root/"repo";self.project.mkdir()
        for args in (("init","-q"),("config","user.email","test@example.invalid"),("config","user.name","Test")):
            subprocess.run(["git","-C",str(self.project),*args],check=True,capture_output=True)
        (self.project/"README.md").write_text("fixture\n")
        subprocess.run(["git","-C",str(self.project),"add","."],check=True,capture_output=True)
        subprocess.run(["git","-C",str(self.project),"commit","-qm","fixture"],check=True,capture_output=True)
        self.context=self.root/"context.json";self.context.write_text('{"fixture":true}')
    def cli(self,*args,ok=0,raw=False,cli=CLI):
        r=subprocess.run([sys.executable,str(cli),*map(str,args)],cwd=self.project,env=self.env,
                         capture_output=True,text=True,encoding="utf-8",timeout=30)
        self.assertEqual(r.returncode,ok,r.stdout+r.stderr)
        return r.stdout if raw else json.loads(r.stdout) if r.stdout.strip() else None
    def kb(self,*args,**kw):return self.cli("knowledge",*args,**kw)
    def add(self,project="alpha",topic="gpu/scale",body="Measured scale is 1.04.",source="commit:abc"):
        return self.kb("add","--project",project,"--topic",topic,"--body",body,"--evidence",source)["observation"]
    def propose(self,oid,project="alpha",topic="gpu/scale",body="Measured scale is 1.04.",extra=()):
        return self.kb("propose","--project",project,"--topic",topic,"--body",body,"--observations",oid,*extra)["proposal"]
    def approve(self,pid):
        return self.kb("decide",pid,"approve","--reviewer","fixture-reviewer","--reason","fixture verified")["fact"]
    def test_exact_dedup_and_review_lifecycle(self):
        a=self.add();b=self.add(body="Measured  scale is 1.04.",source="run:def")
        self.assertEqual(a,b)
        self.assertEqual(self.kb("search","--project","alpha","--query","scale")["records"],[])
        p=self.kb("maintain","--project","alpha")["proposals"][0]
        fid=self.approve(p)
        result=self.kb("search","--project","alpha","--query","scale")["records"]
        self.assertEqual(result[0]["id"],fid);self.assertEqual(len(result[0]["evidence"]),2)
        newer=self.add(body="Measured scale is 1.02.",source="run:new")
        p1=self.propose(newer,body="Scale is now 1.02.")
        p2=self.propose(newer,body="Different claim.")
        second=self.approve(p1)
        self.kb("decide",p2,"approve","--reviewer","reviewer","--reason","stale",ok=2)
        history=self.kb("history","--project","alpha","--topic","gpu/scale")["facts"]
        self.assertEqual({h["status"] for h in history},{"active","superseded"})
        self.assertEqual(history[0]["id"],second)
        self.assertEqual(self.kb("audit")["integrity"],["ok"])
    def test_scope_and_global_promotion(self):
        oid=self.add()
        self.kb("propose","--project","beta","--topic","gpu/scale","--body","Wrong scope","--observations",oid,ok=2)
        self.kb("propose","--project","global","--topic","gpu/scale","--body","General scale lesson","--observations",oid,ok=2)
        p=self.propose(oid,project="global",body="General scale lesson",extra=("--cross-project",))
        self.approve(p)
        self.assertEqual(self.kb("search","--project","beta")["records"],[])
        self.assertEqual(len(self.kb("search","--project","beta","--include-global","--query","scale")["records"]),1)
        self.assertEqual(len(self.kb("packet","--project","alpha")["observations"]),1)
    def test_curate_rejections_and_exchange(self):
        oid=self.add()
        script=self.root/"curator.py"
        script.write_text('import json,sys\np=json.load(sys.stdin)\no=p["observations"][0]\nprint(json.dumps({"proposals":[{"topic":o["topic"],"kind":o["kind"],"body":"Condensed evidence","observations":[o["id"]]}]}))')
        p=self.kb("curate","--project","alpha","--",sys.executable,script)["proposals"][0]
        self.kb("decide",p,"reject","--reviewer","reviewer","--reason","Needs more context")
        packet=self.kb("packet","--project","alpha")
        self.assertEqual(packet["observations"][0]["prior_rejections"][0]["reason"],"Needs more context")
        raw=self.kb("export-observations","--project","alpha",raw=True)
        ex=self.root/"exchange.jsonl";ex.write_text(raw,encoding="utf-8")
        other=self.root/"other.sqlite3"
        for _ in range(2):
            self.cli("knowledge","--db",other,"import-observations","--project","alpha","--input",ex)
        packet=self.cli("knowledge","--db",other,"packet","--project","alpha")
        self.assertEqual(len(packet["observations"]),1)
        self.assertEqual(len(packet["observations"][0]["evidence"]),1)
        backup=self.root/"backup.sqlite3"
        self.kb("backup","--output",backup)
        self.assertEqual(self.cli("knowledge","--db",backup,"audit")["integrity"],["ok"])
    def test_reviewed_writeback_preserves_repo(self):
        fid=self.approve(self.propose(self.add(source="PRIVATE_SOURCE_NOT_FOR_REPO")))
        args=("writeback",fid,"--target",self.project,"--public-evidence","docs/experiment.md")
        preview=self.kb(*args)
        dest=self.project/preview["path"]
        self.assertFalse(dest.exists());self.assertNotIn("PRIVATE_SOURCE",preview["content"])
        self.kb(*args,"--apply",ok=2)
        self.kb(*args,"--apply","--confirm-repo-safe")
        self.assertIn("Measured scale",dest.read_text(encoding="utf-8"))
        self.assertEqual(self.kb(*args)["status"],"unchanged")
        oid=self.add(body="Scale now 1.02.",source="run:new")
        updated=self.approve(self.propose(oid,body="Scale now 1.02."))
        newargs=("writeback",updated,"--target",self.project,"--public-evidence","docs/new.md")
        preview=self.kb(*newargs)
        self.kb(*newargs,"--apply","--confirm-repo-safe",ok=2)
        self.kb(*newargs,"--apply","--confirm-repo-safe","--expected-sha",preview["existing_sha256"])
        self.assertIn("1.02",dest.read_text(encoding="utf-8"))
        self.kb(*args,ok=2)
    def test_concurrent_observations(self):
        commands=[[sys.executable,str(CLI),"knowledge","add","--project","alpha","--topic","same","--body","same claim","--evidence","run:"+str(i)] for i in range(4)]
        workers=[subprocess.Popen(x,cwd=self.project,env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for x in commands]
        for p in workers:
            out,err=p.communicate(timeout=30)
            self.assertEqual(p.returncode,0,(out,err))
        packet=self.kb("packet","--project","alpha")
        self.assertEqual(len(packet["observations"]),1)
        self.assertEqual(len(packet["observations"][0]["evidence"]),4)
    def test_telemetry_matched_and_missing(self):
        base={"campaign":"fixture","task":"t","trial":0,"protocol_sha256":"a"*64,"base_commit":"b"*40,
              "harness":"h","model":"m","outcome":"accepted","elapsed_s":10,"evidence":"review"}
        path=self.root/"t.json"
        for variant,elapsed in (("base",10),("candidate",7)):
            row=dict(base,id=variant,variant=variant,elapsed_s=elapsed)
            path.write_text(json.dumps(row))
            self.cli("telemetry","record","--input",path)
            self.assertEqual(self.cli("telemetry","record","--input",path)["status"],"unchanged")
        result=self.cli("benchmark","compare","--campaign","fixture","--baseline","base","--candidate","candidate")
        self.assertEqual(result["both_accepted"],1)
        self.assertEqual(result["accepted_pair_metrics"]["elapsed_s"]["median_paired_delta"],-3)
        self.assertIsNone(result["accepted_pair_metrics"]["input_tokens"]["candidate_median"])
        row=dict(base,id="extra",variant="base",trial=1,outcome="timeout")
        path.write_text(json.dumps(row));self.cli("telemetry","record","--input",path)
        self.cli("benchmark","compare","--campaign","fixture","--baseline","base","--candidate","candidate",ok=2)
    def test_scheduler_manifests_and_validation(self):
        spec={"context":"fixture","namespace":"research","name":"probe","image":"example/image@sha256:"+"a"*64,
              "resources":{"cpu":2,"memory_mib":1024,"gpu":1,"gpu_resource":"amd.com/gpu"},
              "timeout_s":60,"command":["python","/source/run.py"],"scheduler_name":"kai-scheduler",
              "volumes":{"source":"src","data":"devdata","output":"results"}}
        file=self.root/"scheduler.json";file.write_text(json.dumps(spec))
        plan=self.cli("scheduler","plan","--spec",file)
        pod=plan["spec"]["template"]["spec"]
        self.assertEqual(pod["schedulerName"],"kai-scheduler")
        self.assertFalse(pod["automountServiceAccountToken"])
        self.assertEqual(pod["containers"][0]["resources"]["limits"]["amd.com/gpu"],"1")
        self.cli("scheduler","submit","--spec",file,ok=2)
        spec.update(backend="argo",service_account="workflow-runner")
        file.write_text(json.dumps(spec))
        self.assertEqual(self.cli("scheduler","plan","--spec",file)["kind"],"Workflow")
        spec["volumes"]["evaluator"]="sealed"
        file.write_text(json.dumps(spec));self.cli("scheduler","plan","--spec",file,ok=2)
    def test_sandbox_mount_boundaries_and_project_plan(self):
        dirs={}
        for role in ("evaluator","data","predictions","output"):
            dirs[role]=str(self.root/role);Path(dirs[role]).mkdir()
        spec={"stage":"evaluator","image":"fixture@sha256:"+"a"*64,"mounts":dirs,
              "cpu":1,"memory_mib":256,"timeout_s":10,"command":["python","evaluate.py"]}
        file=self.root/"sandbox.json";file.write_text(json.dumps(spec))
        plan=self.cli("sandbox","plan","--spec",file)["argv"]
        self.assertIn("--network=none",plan)
        self.assertIn("--read-only",plan)
        self.assertTrue(any("target=/predictions,readonly" in s for s in plan))
        self.cli("sandbox","run","--spec",file,ok=2)
        spec["mounts"]["source"]=dirs["data"];file.write_text(json.dumps(spec))
        self.cli("sandbox","plan","--spec",file,ok=2)
        p=self.root/"project.json";p.write_text('{"commands":{"check":["python","-m","unittest"]}}')
        self.assertEqual(self.cli("project","plan","--config",p,"check")["argv"],["python","-m","unittest"])
    def wait_state(self,folder,terminal=False):
        deadline=time.monotonic()+12
        while time.monotonic()<deadline:
            try:
                data=json.loads((folder/"receipt.json").read_text())
            except (FileNotFoundError,PermissionError):
                time.sleep(.05);continue
            if terminal and data["status"] not in ("pending","running"):return data
            if not terminal and (self.root/"private/leases/device/owner.json").exists():return data
            time.sleep(.05)
        self.fail("Run state deadline")
    def test_lease_and_cancel(self):
        a=self.root/"a"
        self.cli("scheduler","local-submit","--device","device","--out",a,"--context",self.context,"--timeout","20",
                 "--confirm","--",sys.executable,"-c","import time;time.sleep(15)")
        self.wait_state(a)
        b=self.root/"b"
        self.cli("run","--out",b,"--context",self.context,"--timeout","2","--lease","device",
                 "--",sys.executable,"-c","pass",ok=1)
        self.cli("cancel",a)
        self.assertEqual(self.wait_state(a,True)["status"],"cancelled")
        self.assertFalse((self.root/"private/leases/device").exists())
        c=self.root/"c"
        self.cli("run","--out",c,"--context",self.context,"--timeout","2","--lease","device",
                 "--",sys.executable,"-c","pass")
        if os.name=="nt":time.sleep(.25)
    def test_vendored_extensions(self):
        self.cli("install","--target",self.project,"--profile","research")
        self.cli("knowledge","audit",cli=self.project/".agent-rules/agent.py")
        self.assertIn("Learning is part of completion",(self.project/"AGENTS.md").read_text(encoding="utf-8"))

if __name__=="__main__":unittest.main()
