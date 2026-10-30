import sys
import subprocess
from datetime import datetime

models = [
    "nvidia/nemotron-3-nano-4b",
    "google/gemma-4-e4b",
    "prism-ml/bonsai-27b",
    "google/gemma-4-12b",
    "liquid/lfm2.5-1.2b",
]
arms = ["jamesian", "vanilla"]

print(f"[{datetime.now()}] [NEW MODELS & RETRY QUEUE] Starting run for {models} (trials=20)...", flush=True)

for model in models:
    for arm in arms:
        print(f"[{datetime.now()}] [LMSTUDIO-QUEUE] Running {model} ({arm})...", flush=True)
        cmd = [
            ".venv/bin/agency-audit", "run",
            "--provider", "lmstudio",
            "--model", model,
            "--arm", arm,
            "--trials", "20",
            "--protocol", "dual-mode",
            "--seed", "7",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[{datetime.now()}] [LMSTUDIO-QUEUE] COMPLETED {model} ({arm}):\n{res.stdout.strip()}", flush=True)
        else:
            print(f"[{datetime.now()}] [LMSTUDIO-QUEUE] FAILED {model} ({arm}):\n{res.stderr.strip()}", flush=True)

print(f"[{datetime.now()}] [NEW MODELS & RETRY QUEUE] All runs finished.", flush=True)
