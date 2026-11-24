"""Exercise real Git-backed skill creation with isolated synthetic evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI=Path(__file__).resolve().parents[1]/"tools/agent.py"

class SkillTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.env=dict(os.environ,AGENT_RULES_HOME=str(self.root/"private"),PYTHONIOENCODING="utf-8")
        self.project=self.root/"repo";self.project.mkdir()
        self.git("init","-q")
        self.git("config","user.email","test@example.invalid")
        self.git("config","user.name","Fixture")
        (self.project/"README.md").write_text("fixture\n",encoding="utf-8")
        self.git("add","README.md");self.git("commit","-qm","fixture")
        self.spec=self.root/"skill.json"
        self.data={"workflow":"gpu/paired-check","name":"paired-check","scope":"project","project":"alpha",
                   "description":"Use when comparing two matched fixture outputs.",
                   "steps":["Execute the fixture.","Compare the two outputs."],
                   "verification":["Check expected equal outputs."],
                   "failure_handling":["Stop on a mismatch."],
                   "public_evidence":["docs/fixture.md"]}
        self.write_spec()
    def git(self,*args):
        r=subprocess.run(["git","-C",str(self.project),*args],capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        return r.stdout.strip()
    def cli(self,*args,ok=0,cli=CLI):
        r=subprocess.run([sys.executable,str(cli),*map(str,args)],cwd=self.project,env=self.env,
                         capture_output=True,text=True,encoding="utf-8",timeout=30)
        self.assertEqual(r.returncode,ok,r.stdout+r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None
    def skill(self,*args,**kw):return self.cli("skill",*args,**kw)
    def record(self,task,project="alpha",workflow="gpu/paired-check",summary="Validated fixture procedure",ok=0):
        return self.skill("record","--workflow",workflow,"--project",project,"--task",task,
                          "--summary",summary,"--evidence","PRIVATE-EVIDENCE-"+task,ok=ok)
    def write_spec(self):self.spec.write_text(json.dumps(self.data),encoding="utf-8")
    def create(self,*args,ok=0):return self.skill("create","--target",self.project,"--spec",self.spec,*args,ok=ok)
    def complete(self,commit,path,disposition="created",*extra,ok=0):
        return self.skill("complete","--workflow",self.data["workflow"],"--scope",self.data["scope"],
                          "--repository","fixture","--target",self.project,"--skill-path",path,
                          "--commit",commit,"--disposition",disposition,*extra,ok=ok)

    def test_threshold_and_distinct_tasks(self):
        self.assertEqual(self.record("a")["total"]["tasks"],1)
        self.assertEqual(self.record("a")["status"],"unchanged")
        self.record("a",summary="different",ok=2)
        self.record("b")
        self.assertEqual(self.skill("candidates")["candidates"],[])
        self.create(ok=2)
        r=self.record("c")
        self.assertEqual(r["total"]["tasks"],3)
        self.assertEqual(r["action"],"evaluate_and_create_or_extend_skill")
        candidate=self.skill("candidates","--project","alpha")["candidates"][0]
        self.assertEqual(candidate["tasks"],3)
        self.assertEqual(candidate["projects"],1)

    def test_creation_and_verified_git_promotion(self):
        for task in ("a","b","c"):self.record(task)
        preview=self.create()
        path=preview["path"];dest=self.project/path
        self.assertFalse(dest.exists())
        self.assertNotIn("PRIVATE-EVIDENCE",preview["content"])
        self.create("--apply",ok=2)
        self.create("--apply","--confirm-repo-safe")
        self.assertTrue(dest.exists())
        self.assertIn("## Verification",dest.read_text(encoding="utf-8"))
        self.assertEqual(self.skill("inventory","--target",self.project)["skills"][0]["workflow"],self.data["workflow"])
        self.create("--apply","--confirm-repo-safe",ok=2)
        self.complete(self.git("rev-parse","HEAD"),path,"created","--project","alpha",ok=2)
        self.git("add",path);self.git("commit","-qm","Add validated fixture skill")
        head=self.git("rev-parse","HEAD")
        self.assertEqual(self.complete(head,path,"created","--project","alpha")["status"],"promoted")
        self.assertEqual(self.complete(head,path,"created","--project","alpha")["status"],"unchanged")
        self.assertEqual(self.record("d")["action"],"reuse_or_improve_existing")
        self.assertEqual(self.skill("candidates","--project","alpha")["candidates"][0]["existing"]["commit_sha"],head)

    def test_scope_and_existing_skill_overlap(self):
        self.record("a");self.record("b",project="beta");self.record("c",project="gamma")
        self.assertEqual(self.skill("candidates")["candidates"][0]["projects"],3)
        self.assertEqual(self.skill("candidates","--project","alpha")["candidates"],[])
        self.create(ok=2)
        self.data.pop("project");self.data["scope"]="shared";self.write_spec()
        self.create(ok=2) # not the central toolkit
        for file in ("rules/core.md","tools/agent.py","AGENT_INSTALL.md"):
            p=self.project/file;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("fixture\n",encoding="utf-8")
        self.create("--apply","--confirm-repo-safe")
        self.data["name"]="different-name";self.write_spec()
        self.create(ok=2) # same workflow marker
        self.data["workflow"]="gpu/another";self.data["name"]="paired-check";self.write_spec()
        for task in ("a","b","c"):self.record(task,workflow="gpu/another")
        self.create(ok=2) # same skill name

    def test_vendored_skill_creation_tool(self):
        self.cli("install","--target",self.project,"--profile","research")
        vendored=self.project/".agent-rules/agent.py"
        self.assertTrue((self.project/".agents/skills/skill-forge/SKILL.md").is_file())
        self.assertEqual(self.cli("skill","candidates",cli=vendored)["candidates"],[])
        self.assertIn("skill-forge",(self.project/"AGENTS.md").read_text(encoding="utf-8"))

if __name__=="__main__":unittest.main()
