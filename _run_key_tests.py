#!/usr/bin/env python3
"""
ASIMNEXUS Key Test Suite Runner - Run 4 specific test files and report results
"""
import subprocess
import sys
import os
import json
import time

os.chdir(r"C:\AsimNexus")

test_files = [
    ("1. test_power_balance_constitution.py", r"tests\real\test_power_balance_constitution.py"),
    ("2. test_life_journey.py", r"tests\real\test_life_journey.py"),
    ("3. test_mesh_full_stack.py", r"tests\real\test_mesh_full_stack.py"),
    ("4. test_milestone3.py", r"tests\real\test_milestone3.py"),
]

results = {}

for name, path in test_files:
    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"{'='*70}")
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", path, "-v", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=r"C:\AsimNexus"
        )
        elapsed = time.time() - start
        output = proc.stdout + "\n" + proc.stderr
        results[name] = {
            "returncode": proc.returncode,
            "elapsed": round(elapsed, 1),
            "output": output[-4000:],  # last 4k chars
        }
        # Print summary lines
        lines = output.splitlines()
        for line in lines:
            if "PASSED" in line or "FAILED" in line or "ERROR" in line or "passed" in line or "failed" in line:
                print(line)
        if proc.returncode != 0:
            print(f"\n[!] FAILED with exit code {proc.returncode}")
            # Print failure details
            for line in lines:
                if "FAILED" in line or "AssertionError" in line or "Error" in line or "assert " in line:
                    print(f"  {line.strip()}")
    except subprocess.TimeoutExpired:
        results[name] = {"returncode": -1, "elapsed": 300, "output": "TIMEOUT after 300s"}
        print("[!] TIMEOUT")
    except Exception as e:
        results[name] = {"returncode": -2, "elapsed": 0, "output": str(e)}
        print(f"[!] ERROR: {e}")

# Save results
with open(r"C:\AsimNexus\_key_test_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n\n" + "="*70)
print("RESULTS SAVED to _key_test_results.json")
print("="*70)

# Summary
for name, r in results.items():
    status = "PASS" if r["returncode"] == 0 else f"FAIL (exit {r['returncode']})"
    print(f"{name}: {status} ({r.get('elapsed', '?')}s)")
