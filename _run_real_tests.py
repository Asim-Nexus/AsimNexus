
import subprocess
import sys
import json

test_files = [
    "tests/real/test_power_balance_constitution.py",
    "tests/real/test_life_journey.py",
    "tests/real/test_mesh_full_stack.py",
    "tests/real/test_milestone3.py",
]

results = {}
for tf in test_files:
    print(f"\n{'='*60}\nRunning: {tf}\n{'='*60}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", tf, "-v", "--tb=short", "-q"],
            capture_output=True, text=True, timeout=300
        )
        results[tf] = {
            "returncode": result.returncode,
            "stdout": result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout,
            "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
        }
        print(result.stdout[-3000:])
        if result.stderr:
            print("STDERR:", result.stderr[-1000:])
    except Exception as e:
        results[tf] = {"returncode": -1, "error": str(e)}
        print(f"ERROR: {e}")

with open("test_run_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n\nAll done. Results saved to test_run_results.json")
