#!/usr/bin/env python3
"""Fetch anchore/sbom-action action.yml to check supported inputs."""
import urllib.request, json, os

os.environ['PYTHONIOENCODING'] = 'utf-8'

# Try multiple tag variants
tags = ['v0', 'v0.24.0', 'v0.23.0', 'v0.22.0', 'main']
for tag in tags:
    url = f'https://raw.githubusercontent.com/anchore/sbom-action/{tag}/action.yml'
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req)
        content = resp.read().decode('utf-8')
        print(f"=== {tag} action.yml ===")
        print(content[:3000])
        print()
        break  # Found it
    except Exception as e:
        print(f"{tag}: {e}")

# Also check what the actual latest release version is
url = 'https://api.github.com/repos/anchore/sbom-action/releases?per_page=5'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
releases = json.loads(resp.read())
print("\n=== Latest releases ===")
for r in releases:
    print(f"  {r['tag_name']} ({r['published_at']})")
