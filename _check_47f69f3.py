#!/usr/bin/env python3
"""Check workflows triggered by 47f69f3."""
import urllib.request, json, os, time
os.environ['PYTHONIOENCODING'] = 'utf-8'

REPO = "Asim-Nexus/AsimNexus"

# Wait a moment for workflows to start
time.sleep(5)

url = f'https://api.github.com/repos/{REPO}/actions/runs?branch=main&event=push&per_page=8'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

print(f"{'RUN ID':12s} | {'SHA':8s} | {'WORKFLOW':40s} | {'STATUS':10s} | {'CONCLUSION':12s}")
print("="*90)
for r in data['workflow_runs']:
    sha = r['head_sha'][:7]
    name = r['name'][:38]
    status = r['status']
    conclusion = r['conclusion'] or 'N/A'
    print(f"{r['id']:12d} | {sha:8s} | {name:40s} | {status:10s} | {conclusion:12s}")

# If there's a new Docker Publish run, check its status
docker_runs = [r for r in data['workflow_runs'] 
               if r['name'] == 'AsimNexus Docker Publish' and r['head_sha'].startswith('47f69f3')]
if docker_runs:
    run = docker_runs[0]
    print(f"\n\nLatest Docker Publish (run {run['id']}):")
    print(f"Status: {run['status']}, Conclusion: {run['conclusion'] or 'N/A'}")
    
    # Check jobs
    jobs_url = run['jobs_url']
    req2 = urllib.request.Request(jobs_url)
    req2.add_header('Accept', 'application/vnd.github+json')
    try:
        resp2 = urllib.request.urlopen(req2)
        jobs_data = json.loads(resp2.read())
        for job in jobs_data['jobs']:
            print(f"\n  Job: {job['name']} ({job['status']} / {job['conclusion'] or 'N/A'})")
            for step in job['steps']:
                mark = "[FAIL]" if step['conclusion'] == 'failure' else \
                       "[OK]" if step['conclusion'] == 'success' else \
                       "[...]" if step['status'] == 'in_progress' else \
                       "[SKIP]"
                print(f"    {mark} {step['name']}: {step['status']} / {step['conclusion'] or 'N/A'}")
    except Exception as e:
        print(f"  (Could not get jobs: {e})")
else:
    print("\n\nNo Docker Publish run found for 47f69f3 yet (still being created)...")
