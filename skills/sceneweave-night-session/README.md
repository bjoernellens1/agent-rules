# SceneWeave Night Session skill (portable starter)

Copy this directory to `.agents/skills/sceneweave-night-session/` in the appropriate repository if your coding agent discovers skills there, or instruct the agent to read `SKILL.md` directly. Discovery paths and hooks vary by agent; no installation, scheduling, or remote repository modifications are performed by this package.

Suggested `AGENTS.md` addition:

> For autonomous overnight research, read and follow `.agents/skills/sceneweave-night-session/SKILL.md`. Work in parallel, isolated lanes and replenish the bounded backlog across multiple waves. Do not end a six-hour session merely because its first wave completes; review all authorized ready follow-ups and document any early-stop reason. Always obey hard budgets, experiment policy, and scientific gates. AGO is an external Gaussian lifecycle/resource strategy, not only an active-set selector.

Optional ledger guard (standard-library Python, read-only checks):

```sh
python scripts/night_guard.py init night_manifest.json --minutes 360 --reserve 45 --gpu-minutes 180
# Populate `tasks` from the backlog, and update statuses/actual GPU minutes as work progresses.
python scripts/night_guard.py status night_manifest.json
python scripts/night_guard.py finish night_manifest.json
```

A nonzero `finish` exit means the ledger does not authorize a normal handover yet (running work or a ready task fits). This is an advisory guard to wire into an agent's supported completion hook, not a daemon, job killer, or real hardware monitor. The coordinator must log actual GPU allocation, estimates, blockers and jobs. It cannot guarantee scientific integrity or prevent an agent from misreporting a ledger. See `scripts/test_night_guard.py` for examples; run `python -m unittest discover -s scripts -p 'test_*.py'`.
