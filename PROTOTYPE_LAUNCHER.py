#!/usr/bin/env python3
"""
AsimNexus Prototype Launcher
Start the constitutional digital platform in one command.

Flow: Identity → Chat → Dharma Veto → Human Approval → Execute → Audit
"""
import subprocess
import sys
import time
import webbrowser

BANNER = r"""
   ╔══════════════════════════════════════════════════════╗
   ║       AsimNexus — Constitutional Digital Platform   ║
   ║       Local-first · Human-controlled · Auditable    ║
   ╚══════════════════════════════════════════════════════╝
"""

FLOW = """
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ ① WHO?  │ →  │ ② WHAT? │ →  │ ③ DHARMA│
   │ Identity │    │   Chat   │    │  Veto    │
   └──────────┘    └──────────┘    └──────────┘
        │               │               │
        ↓               ↓               ↓
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ ④ HUMAN │ →  │ ⑤ EXEC  │ →  │ ⑥ AUDIT │
   │ Approve  │    │          │    │          │
   └──────────┘    └──────────┘    └──────────┘
"""


def main():
    print(BANNER)
    print(FLOW)
    print("   Starting AsimNexus backend...\n")

    backend = subprocess.Popen(
        [sys.executable, "simple_backend.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    time.sleep(2)
    print("   ✓ Backend running at http://localhost:8000")
    print("   ✓ API docs at http://localhost:8000/docs")
    print("   ✓ Health check: http://localhost:8000/health")
    print("\n   Constitution:  CONSTITUTION.md")
    print("   Source:        simple_backend.py")
    print("\n   Press Ctrl+C to stop.\n")

    try:
        webbrowser.open("http://localhost:8000/docs")
        for line in backend.stdout:
            print(line.decode().rstrip())
    except KeyboardInterrupt:
        print("\n   Shutting down...")
        backend.terminate()
        print("   ✓ AsimNexus stopped.")


if __name__ == "__main__":
    main()
