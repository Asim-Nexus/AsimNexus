#!/usr/bin/env python3
"""Wait for rate limit to reset, then check Docker Publish workflow."""
import urllib.request, json, os, time

os.environ['PYTHONIOENCODING'] = 'utf-8'
REPO = 'Asim-Nexus/AsimNexus'
RUN_ID = 27379622159

# First, check rate limit to get reset time
url = 'https://api.github.com/rate_limit'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
core = data['resources']['core']
remaining = core['remaining']
reset_epoch = core['reset']

print(f"Rate limit: {remaining}/{core['limit']} remaining")
print(f"Reset at epoch: {reset_epoch} ({time.strftime('%H:%M:%S UTC', time.gmtime(reset_epoch))})")
print(f"Current time: {time.strftime('%H:%M:%S UTC', time.gmtime(time.time()))}")

if remaining == 0:
    wait = reset_epoch - time.time() + 5  # +5s buffer
    if wait > 0:
        print(f"Rate limited. Waiting {wait:.0f}s ({wait/60:.1f} min)...")
        time.sleep(wait)
        print("Resume time reached, checking workflow...")
    else:
        print(f"Wait time negative ({wait}s), checking now...")
else:
    print("Rate limit available, checking workflow...")

# Now check the workflow
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
