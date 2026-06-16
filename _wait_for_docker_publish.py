#!/usr/bin/env python3
"""Poll Docker Publish workflow until complete or timeout."""
import urllib.request, json, os, time, sys

REPO = "Asim-Nexus/AsimNexus"
RUN_ID = 27379622159  # Docker Publish run for 47f69f3
POLL_INTERVAL = 30  # seconds
MAX_POLLS = 40  # 20 minutes max

os.environ['PYTHONIOENCODING'] = 'utf-8'

for i in range(MAX_POLLS):
    # Get run info
    url = f'https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}'
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/vnd.github+json')
    resp = urllib.request.urlopen(req)
    run = json.loads(resp.read())
    
    status = run['status']
    conclusion = run.get('conclusion') or 'N/A'
    
    print(f"\n[Poll {i+1}/{MAX_POLLS}] Run {RUN_ID}: {status} / {conclusion}")
    
    # Get jobs
    jobs_url = run['jobs_url']
    req2 = urllib.request.Request(jobs_url)
    req2.add_header('Accept', 'application/vnd.github+json')
    resp2 = urllib.request.urlopen(req2)
    jobs_data = json.loads(resp2.read())
    
    for job in jobs_data['jobs']:
        job_status = job['status']
        job_conc = job.get('conclusion') or 'N/A'
        print(f"  Job: {job['name']} ({job_status} / {job_conc})")
        for step in job['steps']:
            mark = "[FAIL]" if step['conclusion'] == 'failure' else \
                   "[OK]" if step['conclusion'] == 'success' else \
                   "[...]" if step['status'] == 'in_progress' else \
                   "[SKIP]"
            print(f"    {mark} {step['name']}: {step['status']} / {step['conclusion'] or 'N/A'}")
    
    if status == 'completed':
        print(f"\n{'='*60}")
        print(f"WORKFLOW COMPLETED: {conclusion}")
        print(f"{'='*60}")
        sys.exit(0 if conclusion == 'success' else 1)
    
    print(f"\nWaiting {POLL_INTERVAL}s...")
    time.sleep(POLL_INTERVAL)

print(f"\nTIMEOUT after {MAX_POLLS * POLL_INTERVAL}s")
sys.exit(2)
