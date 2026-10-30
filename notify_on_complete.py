import os
import sys
import time
import glob
import subprocess

TASK_LOG = "/home/ultraxav/.gemini/antigravity/brain/db4cb382-a1d4-4beb-8f99-3f9a0e01a3c7/.system_generated/tasks/task-231.log"
PROJECT_LOG = "/home/ultraxav/projects/jamesian-layer/logs/local_suite_execution.log"
FAIL_LOG = "/home/ultraxav/projects/jamesian-layer/logs/failures.log"

lmstudio_models = [
    'google/gemma-4-26b-a4b',
    'google/gemma-4-31b',
    'google/gemma-4-e2b',
    'liquid/lfm2-24b-a2b',
    'meta-llama_-_llama-3.2-1b',
    'meta-llama_-_llama-3.2-3b',
    'nvidia/nemotron-3-nano-4b',
    'nvidia/nemotron-3-nano-omni',
    'openai/gpt-oss-20b',
    'qwen/qwen3.5-9b',
    'qwen/qwen3.8-27b',
    'zai-org/glm-4.7-flash',
]
strata_models = ['qwen3.8-flash-next-iq2_xs']
all_models = lmstudio_models + strata_models

known_completed = set()

def sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "-" for c in name)

for m in all_models:
    s = sanitize(m)
    j = glob.glob(f"reports/audit_report_*_{s}_jamesian_*.json")
    v = glob.glob(f"reports/audit_report_*_{s}_vanilla_*.json")
    if j and v:
        known_completed.add(m)

print(f"Watcher started. Already fully completed: {list(known_completed)}", flush=True)

last_fail_count = 0
if os.path.exists(FAIL_LOG):
    with open(FAIL_LOG, "r") as f:
        last_fail_count = len(f.readlines())

while True:
    # 1. Sync logs and check for new failures
    if os.path.exists(TASK_LOG):
        try:
            with open(TASK_LOG, "r") as f_in, open(PROJECT_LOG, "w") as f_out:
                f_out.write(f_in.read())
            subprocess.run(f"grep -E 'FAILED' {PROJECT_LOG} > {FAIL_LOG} 2>/dev/null", shell=True)
            with open(FAIL_LOG, "r") as f:
                current_fail_count = len(f.readlines())
            if current_fail_count > last_fail_count:
                print(f"NEW_FAILURE_RECORDED (total: {current_fail_count})", flush=True)
                sys.exit(0)
        except Exception:
            pass

    # 2. Check for completed models
    for m in all_models:
        if m in known_completed:
            continue
        s = sanitize(m)
        j = glob.glob(f"reports/audit_report_*_{s}_jamesian_*.json")
        v = glob.glob(f"reports/audit_report_*_{s}_vanilla_*.json")
        if j and v:
            known_completed.add(m)
            print(f"MODEL_COMPLETED: {m}", flush=True)
            sys.exit(0)
    time.sleep(10)
