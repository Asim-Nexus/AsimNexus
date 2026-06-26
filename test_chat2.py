import requests, json
tests = [
    {"msg": "hello", "clone": "auto"},
    {"msg": "code review", "clone": "tech_architect"},
    {"msg": "health check", "clone": "health_sage"},
]
for t in tests:
    r = requests.post('http://127.0.0.1:8000/api/brain/process', 
                     json={'message': t['msg'], 'context': {'clone': t['clone']}})
    d = r.json()
    with open('test_out.txt', 'a', encoding='utf-8') as f:
        f.write(f"{t['clone']}: {d.get('source')} - {d.get('response', '')[:60]}\n")