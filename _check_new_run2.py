#!/usr/bin/env python3
"""Check Docker Publish run 27381634609 (e5418c9) status."""
import urllib.request, json, os

os.environ['PYTHONIOENCODING'] = 'utf-8'
REPO = 'Asim-Nexus/AsimNexus'
RUN_ID = 27381634609

url = f'https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
run = json.loads(resp.read())

status = run['status']
conclusion = run.get('conclusion') or 'N/A'
print(f"Docker Publish Run {RUN_ID} (e5418c9): {status} / {conclusion}")

jobs_url = run['jobs_url']
req2 = urllib.request.Request(jobs_url)
req2.add_header('Accept', 'application/vnd.github+json')
resp2 = urllib.request.urlopen(req2)
jobs_data = json.loads(resp2.read())

for job in jobs_data['jobs']:
    print(f"\n  Job: {job['name']} ({job['status']} / {job.get('conclusion') or 'N/A'})")
    for step in job['steps']:
        mark = '[FAIL]' if step['conclusion'] == 'failure' else \
               '[OK]' if step['conclusion'] == 'success' else \
               '[...]' if step['status'] == 'in_progress' else \
               '[SKIP]'
        print(f"    {mark} {step['name']}: {step['status']} / {step['conclusion'] or 'N/A'}")
