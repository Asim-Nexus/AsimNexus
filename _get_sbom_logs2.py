#!/usr/bin/env python3
"""Get the SBOM step logs for Docker Publish run 27379622159."""
import urllib.request, json, os, time

os.environ['PYTHONIOENCODING'] = 'utf-8'
REPO = 'Asim-Nexus/AsimNexus'
RUN_ID = 27379622159

# Get run info to get jobs_url
url = f'https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
run = json.loads(resp.read())

# Get jobs
jobs_url = run['jobs_url']
req2 = urllib.request.Request(jobs_url)
req2.add_header('Accept', 'application/vnd.github+json')
resp2 = urllib.request.urlopen(req2)
jobs_data = json.loads(resp2.read())

# Find the SBOM step in build-and-push job
for job in jobs_data['jobs']:
    if job['name'] == 'build-and-push':
        for step in job['steps']:
            if step['name'] == 'Generate SBOM':
                print(f"SBOM Step Status: {step['status']}")
                print(f"SBOM Step Conclusion: {step['conclusion']}")
                print(f"SBOM Step Number: {step['number']}")
                
                # Try to get step logs
                logs_url = f'https://api.github.com/repos/{REPO}/actions/jobs/{job["id"]}/logs'
                req3 = urllib.request.Request(logs_url)
                req3.add_header('Accept', 'application/vnd.github+json')
                try:
                    resp3 = urllib.request.urlopen(req3)
                    logs = resp3.read().decode('utf-8', errors='replace')
                    # Find SBOM section in logs
                    lines = logs.split('\n')
                    sbom_lines = []
                    in_sbom = False
                    for i, line in enumerate(lines):
                        if 'Generate SBOM' in line and not in_sbom:
                            in_sbom = True
                        if in_sbom:
                            sbom_lines.append((i+1, line))
                            if len(sbom_lines) > 200:  # cap at 200 lines
                                break
                            # Stop at next major step
                            if len(sbom_lines) > 5 and ('::' in line and 'SBOM' not in line and '##[' in line):
                                break
                    
                    print(f"\nSBOM Logs ({len(sbom_lines)} lines):")
                    for line_num, line in sbom_lines:
                        print(f"  L{line_num}: {line}")
                except Exception as e:
                    print(f"Could not get logs: {e}")
                    
                    # Try the step's log URL directly
                    try:
                        step_log_url = f'https://api.github.com/repos/{REPO}/actions/jobs/{job["id"]}/logs'
                        step_req = urllib.request.Request(step_log_url)
                        step_req.add_header('Accept', 'application/vnd.github+json')
                        # Use range to get last 50KB
                        step_req.add_header('Range', 'bytes=-51200')
                        step_resp = urllib.request.urlopen(step_req)
                        content_range = step_resp.headers.get('Content-Range', '')
                        print(f"Content-Range: {content_range}")
                        # Read last portion
                        logs_chunk = step_resp.read().decode('utf-8', errors='replace')
                        # Find SBOM-related lines
                        for line in logs_chunk.split('\n'):
                            if 'sbom' in line.lower() or 'SBOM' in line or 'error' in line.lower() or 'fail' in line.lower():
                                print(f"  {line}")
                    except Exception as e2:
                        print(f"Also failed: {e2}")
