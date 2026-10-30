import sys
import subprocess
from datetime import datetime

models = ["meta-models/muse-spark-open-1026"]
arms = ["jamesian", "vanilla"]

print(f"[{datetime.now()}] [TASK 2: BASETEN] Starting full suite (trials=20)...", flush=True)

for model in models:
    for arm in arms:
        print(f"[{datetime.now()}] [BASETEN] Running {model} ({arm})...", flush=True)
        cmd = [
            ".venv/bin/agency-audit", "run",
            "--provider", "baseten",
            "--model", model,
            "--arm", arm,
            "--trials", "20",
            "--protocol", "dual-mode",
            "--seed", "7",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[{datetime.now()}] [BASETEN] COMPLETED {model} ({arm}):\n{res.stdout.strip()}", flush=True)
        else:
            print(f"[{datetime.now()}] [BASETEN] FAILED {model} ({arm}):\n{res.stderr.strip()}", flush=True)

print(f"[{datetime.now()}] [TASK 2: BASETEN] All runs finished.", flush=True)
