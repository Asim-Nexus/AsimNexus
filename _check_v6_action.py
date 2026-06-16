#!/usr/bin/env python3
"""Check docker/build-push-action@v6 action.yml for inputs."""
import urllib.request, json

url = 'https://raw.githubusercontent.com/docker/build-push-action/v6/action.yml'
req = urllib.request.Request(url)
resp = urllib.request.urlopen(req)
content = resp.read().decode('utf-8')
print(content[:5000])
