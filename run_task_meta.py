import sys
import subprocess
from datetime import datetime

models = [
    "muse-spark-1.3",
    "muse-spark-1.2",
    "muse-spark-1.1",
    "muse-wonder-1.0",
]
arms = ["jamesian", "vanilla"]

print(f"[{datetime.now()}] [TASK 1: META] Starting full suite (trials=20)...", flush=True)

for model in models:
    for arm in arms:
        print(f"[{datetime.now()}] [META] Running {model} ({arm})...", flush=True)
        cmd = [
            ".venv/bin/agency-audit", "run",
            "--provider", "meta",
            "--model", model,
            "--arm", arm,
            "--trials", "20",
            "--protocol", "dual-mode",
            "--seed", "7",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[{datetime.now()}] [META] COMPLETED {model} ({arm}):\n{res.stdout.strip()}", flush=True)
        else:
            print(f"[{datetime.now()}] [META] FAILED {model} ({arm}):\n{res.stderr.strip()}", flush=True)

print(f"[{datetime.now()}] [TASK 1: META] All runs finished.", flush=True)
