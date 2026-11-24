"""Synthetic smoke example, not a scientific/GPU benchmark."""
import json
import os
from pathlib import Path

out = Path(os.environ["AGENT_RUN_DIR"])
(out / "metrics.json").write_text(json.dumps({"quality": 0.9, "latency_ms": 10.0}) + "\n", encoding="utf-8")
print("Synthetic smoke metrics written.")
