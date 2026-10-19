#!/usr/bin/env python3
"""Before P04: 18 observations including strict concurrent HTTP status validation."""
import concurrent.futures
import uuid
from testlib import BEFORE, Suite, req

s = Suite('p04_before')
def key(): return 'srf-' + uuid.uuid4().hex[:14]
def pay(amount, k, booking='bk-1', currency='KRW'):
    return req(BEFORE, 'POST', '/p04/payments',
               {'amount': amount, 'currency': currency, 'booking_id': booking},
               {'Idempotency-Key': k})

def check(cid, response, status, category='CONTROL', extra_ok=True):
    s.check(cid, response[0], status, category, extra_ok)

check('P04-01-valid', pay(1000, key()), 200)
check('P04-02-zero', pay(0, key()), 422)
check('P04-03-negative', pay(-100, key()), 422)
check('P04-04-too-big', pay(1000001, key()), 422)
for cid, value, expected_amount in [
    ('P04-05-string', '1000', 1000), ('P04-06-bool', True, 1),
    ('P04-07-float', 1000.0, 1000)]:
    status, body = pay(value, key())
    s.check(cid, status, 200, 'VULNERABILITY_REPRODUCED',
            extra_ok=isinstance(body, dict) and body.get('amount') == expected_amount)
check('P04-08-currency', pay(1000, key(), currency='USD'), 422)
check('P04-09-no-key', req(BEFORE,'POST','/p04/payments',
      {'amount':1000,'currency':'KRW','booking_id':'bk-1'}), 422)

k = key()
assert pay(500000, k, booking='owner')[0] == 200
response = req(BEFORE, 'GET', '/p04/payments/' + k)
check('P04-10-anon-read', response, 200, 'VULNERABILITY_REPRODUCED',
      isinstance(response[1], dict) and response[1].get('amount') == 500000)
check('P04-11-oracle', req(BEFORE, 'GET', '/p04/payments/srf-does-not-exist'), 404)
# Explicit attack chain; same key must remain occupied by the first amount.
ks=key()
check('P04-12-squat', pay(1,ks,booking='attacker'), 200, 'VULNERABILITY_REPRODUCED')
check('P04-13-squat-owner', pay(500000,ks,booking='owner'), 409, 'VULNERABILITY_REPRODUCED')
r=req(BEFORE,'GET','/p04/payments/'+ks)
check('P04-14-residual', r, 200,'VULNERABILITY_REPRODUCED',isinstance(r[1],dict) and r[1].get('amount')==1)
check('P04-15-squat-assert', r, 200,'VULNERABILITY_REPRODUCED',isinstance(r[1],dict) and r[1].get('amount')==1)
check('P04-16-owner-newkey', pay(500000,key(),booking='owner'),200)
k2=key()
a=pay(2000,k2,booking='retry');b=pay(2000,k2,booking='retry')
check('P04-17-idempotent-retry', b, 200, extra_ok=a[0]==200 and a[1]==b[1])
k3=key()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(pay,amount,k3,f'concurrent-{amount}') for amount in (100,999999)]
    results=[f.result() for f in futures]
statuses=sorted(status for status,body in results)
# Compare a whole result, not a response tuple against integer 200.
s.check('P04-18-concurrent', statuses, [200,409], extra_ok=sum(status==200 for status,body in results)==1)
s.finish()
