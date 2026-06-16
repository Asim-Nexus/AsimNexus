#!/usr/bin/env python3
"""Check GitHub API rate limit and workflow status."""
import urllib.request, json, os, time

os.environ['PYTHONIOENCODING'] = 'utf-8'

REPO = 'Asim-Nexus/AsimNexus'

# Check rate limit
url = 'https://api.github.com/rate_limit'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
core = data['resources']['core']
print(f"Rate limit: {core['remaining']}/{core['limit']} remaining")
reset_time = core['reset']
print(f"Resets at: {time.strftime('%H:%M:%S', time.localtime(reset_time))}")

# Check Docker Publish run
RUN_ID = 27379622159
url = f'https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
run = json.loads(resp.read())

status = run['status']
conclusion = run.get('conclusion') or 'N/A'
print(f"\nDocker Publish Run {RUN_ID}: {status} / {conclusion}")

if status == 'completed':
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
