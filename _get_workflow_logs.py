#!/usr/bin/env python3
"""Get the full workflow logs URL for Docker Publish run 27379622159."""
import urllib.request, json, os

os.environ['PYTHONIOENCODING'] = 'utf-8'
REPO = 'Asim-Nexus/AsimNexus'
RUN_ID = 27379622159

# Get run info
url = f'https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
run = json.loads(resp.read())

# Check log URL
print(f"Logs URL: {run.get('logs_url', 'N/A')}")
print(f"Jobs URL: {run.get('jobs_url', 'N/A')}")

# Get jobs to find the failed step details
jobs_url = run['jobs_url']
req2 = urllib.request.Request(jobs_url)
req2.add_header('Accept', 'application/vnd.github+json')
resp2 = urllib.request.urlopen(req2)
jobs_data = json.loads(resp2.read())

for job in jobs_data['jobs']:
    print(f"\nJob: {job['name']}")
    print(f"  Status: {job['status']}")
    print(f"  Conclusion: {job.get('conclusion') or 'N/A'}")
    print(f"  Step count: {len(job['steps'])}")
    for step in job['steps']:
        print(f"  Step #{step['number']}: {step['name']}")
        print(f"    Status: {step['status']}, Conclusion: {step.get('conclusion') or 'N/A'}")
        if step.get('conclusion') == 'failure':
            # Print available info about the failure
            print(f"    *** FAILED ***")
