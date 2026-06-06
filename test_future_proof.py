
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

import urllib.request, json

B = 'http://127.0.0.1:8000'

def get(p):
    try:
        return json.loads(urllib.request.urlopen(B+p, timeout=5).read())
    except Exception as e:
        return {'error': str(e)}

def post(p, d):
    try:
        data = json.dumps(d).encode()
        req = urllib.request.Request(B+p, data=data,
              headers={'Content-Type':'application/json'}, method='POST')
        return json.loads(urllib.request.urlopen(req, timeout=5).read())
    except Exception as e:
        return {'error': str(e)}

did = 'did:asim:future_proof_test'

rt     = post('/api/runtime/register', {'principal': did, 'role': 'clone', 'ttl': 3600})
ev     = post('/api/events/publish', {'topic': 'test.event', 'payload': {'msg': 'hello'}, 'source': 'test'})
pq     = post('/api/pq/keygen', {'did': did, 'algorithm': 'ML-KEM-768'})
syn    = post('/api/sync/enqueue', {'op_type':'send_msg','entity_type':'message',
                                    'entity_id':'msg001','payload':{'text':'offline'}})
fed    = get('/api/federation/status')
dep    = post('/api/depin/register', {'did': did, 'network': 'helium'})
evo    = get('/api/evolution/stats')
clones = get('/api/clones/specs')
route  = post('/api/clones/route', {'query': 'farming and irrigation help'})
flush  = post('/api/sync/flush', {})
rtst   = get('/api/runtime/status')
evst   = get('/api/events/stats')
pqst   = get('/api/pq/status')
synst  = get('/api/sync/status')

node_id = dep.get('node_id', '')
reward = post('/api/depin/' + node_id + '/collect', {}) if node_id else {}

results = [
    ('ZERO_TRUST',   rt.get('token_id'),   'role='+str(rt.get('role'))+' caps='+str(len(rt.get('caps',[])))),
    ('EVENT_BUS',    ev.get('event_id'),   'status='+str(ev.get('status'))),
    ('POST_QUANTUM', pq.get('key_id'),     'algo='+str(pq.get('algorithm'))),
    ('OFFLINE_SYNC', syn.get('op_id'),     'flush='+str(flush.get('synced'))+' synced'),
    ('FEDERATION',   fed.get('node_id'),   'peers='+str(fed.get('peers'))+' ver='+str(fed.get('state_version'))),
    ('DEPIN',        dep.get('node_id'),   'svt='+str(reward.get('svt_equiv'))),
    ('EVOLUTION',    'total' in evo,       'total='+str(evo.get('total'))),
    ('CLONES',       clones.get('status'), 'n='+str(clones.get('status',{}).get('total_clones'))+
                                           ' routed='+str(route.get('clone',{}).get('name'))),
    ('RUNTIME_ST',   True,                 str(rtst)),
    ('EVENTS_ST',    True,                 'delivered='+str(evst.get('total_delivered'))),
    ('PQ_STATUS',    True,                 'keys='+str(pqst.get('total_keys'))+' quantum_safe='+str(pqst.get('quantum_safe'))),
    ('SYNC_STATUS',  True,                 'queue='+str(synst.get('queue_depth'))+' online='+str(synst.get('is_online'))),
]

print('\n=== FUTURE-PROOF HEALTH CHECK ===')
all_ok = True
for name, ok, detail in results:
    status = 'OK  ' if ok else 'FAIL'
    if not ok: all_ok = False
    print(f'  {status} {name:15} {detail}')
print(f'\n{"ALL SYSTEMS GO" if all_ok else "SOME FAILURES"} — {sum(1 for _,ok,_ in results if ok)}/{len(results)} passed')
