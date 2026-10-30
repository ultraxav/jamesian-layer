import os
import sys
import time
import subprocess
import glob

TASK_LOG = "/home/ultraxav/.gemini/antigravity/brain/db4cb382-a1d4-4beb-8f99-3f9a0e01a3c7/.system_generated/tasks/task-231.log"
PROJECT_LOG = "/home/ultraxav/projects/jamesian-layer/logs/local_suite_execution.log"
FAIL_LOG = "/home/ultraxav/projects/jamesian-layer/logs/failures.log"
NEW_MODELS_LOG = "/home/ultraxav/projects/jamesian-layer/logs/new_models_execution.log"

new_models = [
    "google/gemma-4-e4b",
    "prism-ml/bonsai-27b",
    "google/gemma-4-12b",
    "liquid/lfm2.5-1.2b",
]

def sync_logs():
    if os.path.exists(TASK_LOG):
        try:
            with open(TASK_LOG, "r") as f_in, open(PROJECT_LOG, "w") as f_out:
                f_out.write(f_in.read())
            subprocess.run(f"grep -E 'FAILED' {PROJECT_LOG} > {FAIL_LOG} 2>/dev/null", shell=True)
        except Exception:
            pass

def is_strata_finished():
    # Strata model is qwen3.8-flash-next-iq2_xs
    j = glob.glob("reports/audit_report_*qwen3.8-flash-next-iq2_xs*_jamesian_*.json")
    v = glob.glob("reports/audit_report_*qwen3.8-flash-next-iq2_xs*_vanilla_*.json")
    # Or check if task-231 log says "All local runs finished."
    if os.path.exists(TASK_LOG):
        with open(TASK_LOG, "r") as f:
            content = f.read()
            if "All local runs finished." in content:
                return True
    return bool(j and v)

print("Pipeline controller active. Waiting for Strata to complete before triggering new models...", flush=True)

# Phase 1: Wait for current local run (including Strata) to finish
while not is_strata_finished():
    sync_logs()
    time.sleep(15)

sync_logs()
print("STRATA_COMPLETED: Current suite finished. Now triggering new LM Studio models...", flush=True)

# Phase 2: Run new models
with open(NEW_MODELS_LOG, "a") as f_out:
    proc = subprocess.Popen(
        [".venv/bin/python", "run_task_new_models.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in iter(proc.stdout.readline, ""):
        f_out.write(line)
        f_out.flush()
        # Also append to main local_suite_execution.log and check failures
        with open(PROJECT_LOG, "a") as f_proj:
            f_proj.write(line)
            f_proj.flush()
        if "FAILED" in line:
            with open(FAIL_LOG, "a") as f_fail:
                f_fail.write(line)
                f_fail.flush()
        if "COMPLETED" in line and "(" in line:
            print(f"NEW_MODEL_COMPLETED: {line.strip()}", flush=True)

proc.wait()
print("ALL_NEW_MODELS_FINISHED", flush=True)
