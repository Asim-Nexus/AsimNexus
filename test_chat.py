import requests
tests = [
    {'m': 'hello', 'c': 'auto'},
    {'m': 'health check', 'c': 'health_sage'},
    {'m': 'code review', 'c': 'tech_architect'},
]
for t in tests:
    r = requests.post('http://127.0.0.1:8000/api/brain/process', 
                     json={'message': t['m'], 'context': {'clone': t['c']}})
    d = r.json()
    with open('test_results.txt', 'a', encoding='utf-8') as f:
        f.write(f"{t['c']}: {d.get('source')} - {d.get('response', '')[:40]}\n")