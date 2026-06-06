
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

import urllib.request, json

B = 'http://127.0.0.1:8000'

def get(p):
    try: return json.loads(urllib.request.urlopen(B+p, timeout=4).read())
    except Exception as e: return {'_err': str(e)[:60]}

def post(p, d):
    try:
        req = urllib.request.Request(B+p, json.dumps(d).encode(), {'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(req, timeout=4).read())
    except Exception as e: return {'_err': str(e)[:60]}

tests = [
    ('Nepal status',         lambda: get('/api/nepal/status').get('status') == 'active'),
    ('Chat ZeroTrust live',  lambda: post('/chat',{'message':'hello'}).get('source') != 'runtime'),
    ('Events recent',        lambda: 'events' in get('/api/events/recent')),
    ('Events DLQ',           lambda: 'dlq' in get('/api/events/dlq')),
    ('Runtime violations',   lambda: 'violations' in get('/api/runtime/violations')),
    ('Evolution propose',    lambda: bool(post('/api/evolution/propose',{
                                'title':'t','target_file':'x.py',
                                'old_code':'a','new_code':'b','proposed_by':'test'}).get('patch_id'))),
    ('Federation status',    lambda: 'peers' in get('/api/federation/status')),
    ('Federation sync-pkt',  lambda: 'node_id' in get('/api/federation/sync-packet')),
    ('Clone #1 Dharma',      lambda: get('/api/clones/1/spec').get('name') == 'Dharma Guardian'),
    ('Clone #15 Sovereignty',lambda: get('/api/clones/15/spec').get('name') == 'Sovereignty Shield'),
    ('Sync queue',           lambda: 'queue' in get('/api/sync/queue')),
    ('PQ quantum_safe',      lambda: get('/api/pq/status').get('quantum_safe') is True),
    ('DePIN network_status', lambda: 'networks' in get('/api/depin/status')),
    ('Events publish',       lambda: bool(post('/api/events/publish',{
                                'topic':'master.test','payload':{'x':1},'source':'test'}).get('event_id'))),
    ('Runtime register',     lambda: bool(post('/api/runtime/register',{
                                'principal':'test:master','role':'clone','ttl':100}).get('token_id'))),
    ('Clone route farming',  lambda: post('/api/clones/route',{'query':'crop disease farming'}).get('clone',{}).get('name') == 'Agriculture Guide'),
]

print('\n=== MASTER INTEGRATION TEST ===')
passed = 0
for name, fn in tests:
    try:
        ok = bool(fn())
    except Exception as e:
        ok = False
        print(f'  FAIL {name} -- {e}')
        continue
    status = 'OK  ' if ok else 'FAIL'
    if ok: passed += 1
    print(f'  {status} {name}')

verdict = 'ALL SYSTEMS GREEN' if passed == len(tests) else 'SOME FAILURES - CHECK ABOVE'
print(f'\n{passed}/{len(tests)} passed -- {verdict}')
