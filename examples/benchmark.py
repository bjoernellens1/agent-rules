"""Synthetic smoke example, not a scientific/GPU benchmark."""
import json
import os
from pathlib import Path

out = Path(os.environ["AGENT_RUN_DIR"])
(out / "metrics.json").write_text(json.dumps({"quality": 0.9, "latency_ms": 10.0}) + "\n", encoding="utf-8")
(out / "curve.json").write_text(json.dumps({"quality": [{"t_s": 0, "value": 0.4}, {"t_s": 1, "value": 0.9}]}) + "\n", encoding="utf-8")
print("Synthetic smoke metrics and example curve written (not real timing).")
