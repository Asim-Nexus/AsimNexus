#!/usr/bin/env python3
"""Wait for rate limit to reset, then check Docker Publish workflow status."""
import urllib.request, json, os, time

os.environ['PYTHONIOENCODING'] = 'utf-8'
REPO = 'Asim-Nexus/AsimNexus'
RUN_ID = 27379622159

# Wait for rate limit reset (currently at 21:58 UTC, reset at 22:21 UTC)
# Current time
now = time.time()
reset_time = 1749666073  # ~22:21:13 UTC
wait_secs = max(0, reset_time - now + 10)  # +10s buffer

if wait_secs > 0:
    print(f"Rate limit resets in {wait_secs:.0f}s ({wait_secs/60:.1f} min). Waiting...")
    time.sleep(wait_secs)

print("Checking workflow status...")

url = f'https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
run = json.loads(resp.read())

status = run['status']
conclusion = run.get('conclusion') or 'N/A'
print(f"\nDocker Publish Run {RUN_ID}: {status} / {conclusion}")

jobs_url = run['jobs_url']
req2 = urllib.request.Request(jobs_url)
req2.add_header('Accept', 'application/vnd.github+json')
resp2 = urllib.request.urlopen(req2)
jobs_data = json.loads(resp2.read())

for job in jobs_data['jobs']:
    print(f"  Job: {job['name']} ({job['status']} / {job.get('conclusion') or 'N/A'})")
    for step in job['steps']:
        mark = '[FAIL]' if step['conclusion'] == 'failure' else \
               '[OK]' if step['conclusion'] == 'success' else \
               '[...]' if step['status'] == 'in_progress' else \
               '[SKIP]'
        print(f"    {mark} {step['name']}: {step['status']} / {step['conclusion'] or 'N/A'}")
