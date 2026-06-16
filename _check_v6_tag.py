#!/usr/bin/env python3
"""Check if docker/build-push-action@v6 exists as a valid tag."""
import urllib.request, json

# Check releases of docker/build-push-action
url = 'https://api.github.com/repos/docker/build-push-action/releases?per_page=15'
req = urllib.request.Request(url)
req.add_header('Accept', 'application/vnd.github+json')
resp = urllib.request.urlopen(req)
releases = json.loads(resp.read())

print("Releases:")
for r in releases:
    print(f"  {r['tag_name']}: {r['published_at'][:10]}")

# Check if v6 tag resolution works - look at what HEAD of v6 branch points to
print("\nChecking tag resolution...")
# v6 is a major version tag, let's check what v6 resolves to
url2 = 'https://api.github.com/repos/docker/build-push-action/git/ref/tags/v6'
try:
    req2 = urllib.request.Request(url2)
    req2.add_header('Accept', 'application/vnd.github+json')
    resp2 = urllib.request.urlopen(req2)
    ref_data = json.loads(resp2.read())
    print(f"v6 tag ref: {json.dumps(ref_data, indent=2)[:500]}")
except Exception as e:
    print(f"v6 tag: {e}")

# Also check v5
url3 = 'https://api.github.com/repos/docker/build-push-action/git/ref/tags/v5'
try:
    req3 = urllib.request.Request(url3)
    req3.add_header('Accept', 'application/vnd.github+json')
    resp3 = urllib.request.urlopen(req3)
    ref_data3 = json.loads(resp3.read())
    print(f"\nv5 tag ref: {json.dumps(ref_data3, indent=2)[:500]}")
except Exception as e:
    print(f"v5 tag: {e}")
