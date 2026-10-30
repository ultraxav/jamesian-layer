import sys
import subprocess
from datetime import datetime
from jamesian_layer.config import Settings
from jamesian_layer.middleware.models import discover_available_models

settings = Settings()
lmstudio_models = discover_available_models("lmstudio", settings)
strata_models = ["qwen3.8-flash-next-iq2_xs"]
arms = ["jamesian", "vanilla"]

print(f"[{datetime.now()}] [TASK 3: LOCAL] Starting full suite (trials=20)...", flush=True)
print(f"[{datetime.now()}] [TASK 3: LOCAL] Discovered {len(lmstudio_models)} LM Studio models: {lmstudio_models}", flush=True)

# 1. LM Studio models
for model in lmstudio_models:
    for arm in arms:
        print(f"[{datetime.now()}] [LMSTUDIO] Running {model} ({arm})...", flush=True)
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
            print(f"[{datetime.now()}] [LMSTUDIO] COMPLETED {model} ({arm}):\n{res.stdout.strip()}", flush=True)
        else:
            print(f"[{datetime.now()}] [LMSTUDIO] FAILED {model} ({arm}):\n{res.stderr.strip()}", flush=True)

# 2. Strata models
print(f"[{datetime.now()}] [TASK 3: LOCAL] LM Studio complete. Transitioning to Strata...", flush=True)
for model in strata_models:
    for arm in arms:
        print(f"[{datetime.now()}] [STRATA] Running {model} ({arm})...", flush=True)
        cmd = [
            ".venv/bin/agency-audit", "run",
            "--provider", "strata",
            "--model", model,
            "--arm", arm,
            "--trials", "20",
            "--protocol", "dual-mode",
            "--seed", "7",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[{datetime.now()}] [STRATA] COMPLETED {model} ({arm}):\n{res.stdout.strip()}", flush=True)
        else:
            print(f"[{datetime.now()}] [STRATA] FAILED {model} ({arm}):\n{res.stderr.strip()}", flush=True)

print(f"[{datetime.now()}] [TASK 3: LOCAL] All local runs finished.", flush=True)
