#!/usr/bin/env python3
"""Strict P02/P04 before/after assertions. 7 core BA cases plus defense regressions."""
import concurrent.futures
import json
import os
import uuid
from testlib import BEFORE, AFTER, Suite, req

with open(os.environ['SUNYEDO_TEST_CREDENTIALS_FILE'], encoding='utf-8') as f:
    PASSWORDS = json.load(f)
s = Suite('before_after')


def login(username, password=None):
    status, data = req(AFTER, 'POST', '/auth/token',
                       {'username': username, 'password': password if password is not None else PASSWORDS[username]})
    return status, data.get('access_token') if status == 200 and isinstance(data, dict) else None


def headers(token, **kwargs):
    return {'Authorization': 'Bearer ' + token, **kwargs}


def assert_code(cid, status, expect, **kwargs):
    s.check(cid, status, expect, **kwargs)

al_st, alice = login('alice')
bo_st, bob = login('bob')
ro_st, root = login('root_alpha')
assert_code('SEC-00-alice-token', al_st, 200, extra_ok=bool(alice))
assert_code('SEC-01-bob-token', bo_st, 200, extra_ok=bool(bob))
assert_code('SEC-02-owner-token', ro_st, 200, extra_ok=bool(root))
wrong_status, wrong_tok = login('root_alpha', 'wrong-password')
assert_code('SEC-03-no-password-impersonation', wrong_status, 401, extra_ok=wrong_tok is None)
unknown_status,_=login('not-a-user','wrong-password')
assert_code('SEC-04-unknown-account',unknown_status,401)
# P02 BA-01: normal user retains access; preserve the original response body.
b_st,b_data=req(BEFORE,'GET','/p02/tenants/alpha/records',headers={'X-Lab-Tenant':'alpha','X-Lab-Role':'member'})
a_st,a_data=req(AFTER,'GET','/p02/tenants/alpha/records',headers=headers(alice))
s.check('BA-01', {'before':b_st,'after':a_st,'same_body':b_data==a_data},
        {'before':200,'after':200,'same_body':True})
a_st,_=req(AFTER,'GET','/p02/tenants/alpha/records')
assert_code('BA-02',a_st,401)
a_st,_=req(AFTER,'GET','/p02/tenants/beta/records',headers=headers(alice))
assert_code('BA-03',a_st,403)
# P02 BA-04: role self-assertion must have no effect on a privileged route.
mem,_=req(AFTER,'GET','/p02/tenants/alpha/admin-report',headers=headers(alice, **{'X-Lab-Role':'owner'}))
own,_=req(AFTER,'GET','/p02/tenants/alpha/admin-report',headers=headers(root, **{'X-Lab-Role':'viewer'}))
s.check('BA-04', {'member_claiming_owner':mem,'real_owner_claiming_viewer':own},
        {'member_claiming_owner':403,'real_owner_claiming_viewer':200})

# P04 BA-05: before anonymous leaks; after anonymous blocked, genuine owner allowed,
# and other authenticated user cannot access owner's payment.
key='ba5-'+uuid.uuid4().hex[:12]
payload={'amount':500000,'currency':'KRW','booking_id':'ba5'}
pre_post, _=req(BEFORE,'POST','/p04/payments',payload,{'Idempotency-Key':key})
pre_get, pre_body=req(BEFORE,'GET','/p04/payments/'+key)
post_owner,_=req(AFTER,'POST','/p04/payments',payload,headers(alice,**{'Idempotency-Key':key}))
a_anon,_=req(AFTER,'GET','/p04/payments/'+key)
a_owner,owner_body=req(AFTER,'GET','/p04/payments/'+key,headers=headers(alice))
a_other,_=req(AFTER,'GET','/p04/payments/'+key,headers=headers(bob))
s.check('BA-05',
        {'before_created':pre_post,'before_anon':pre_get,'after_created':post_owner,
         'after_anon':a_anon,'after_owner':a_owner,'after_other_user':a_other,
         'owner_amount':owner_body.get('amount') if isinstance(owner_body,dict) else None},
        {'before_created':200,'before_anon':200,'after_created':200,
         'after_anon':401,'after_owner':200,'after_other_user':404,'owner_amount':500000},
        extra_ok=isinstance(pre_body,dict) and pre_body.get('amount')==500000)
# BA-06 principal-scoped keys: the first actor must not sabotage the second.
k2='ba6-'+uuid.uuid4().hex[:12]
small={'amount':1,'currency':'KRW','booking_id':'ba6-attacker'}
large={'amount':500000,'currency':'KRW','booking_id':'ba6-owner'}
p1,_=req(BEFORE,'POST','/p04/payments',small,{'Idempotency-Key':k2})
p2,_=req(BEFORE,'POST','/p04/payments',large,{'Idempotency-Key':k2})
p3,pb=req(BEFORE,'GET','/p04/payments/'+k2)
q1,_=req(AFTER,'POST','/p04/payments',small,headers(root,**{'Idempotency-Key':k2}))
q2,_=req(AFTER,'POST','/p04/payments',large,headers(alice,**{'Idempotency-Key':k2}))
q3,qb=req(AFTER,'GET','/p04/payments/'+k2,headers=headers(alice))
s.check('BA-06',{'before': [p1,p2,p3,pb.get('amount')],
                 'after':[q1,q2,q3,qb.get('amount')]},
        {'before':[200,409,200,1], 'after':[200,200,200,500000]})
# BA-07 strict amount rejection.
k3='ba7-'+uuid.uuid4().hex[:12]
stringpay={'amount':'1000','currency':'KRW','booking_id':'ba7'}
t1,_=req(BEFORE,'POST','/p04/payments',stringpay,{'Idempotency-Key':k3})
t2,_=req(AFTER,'POST','/p04/payments',stringpay,headers(alice,**{'Idempotency-Key':k3}))
s.check('BA-07',[t1,t2],[200,422])
# Additional security regressions beyond BA-01..07.
for who, value in [('string','1000'),('bool',True),('float',1000.0),('negative',-1),('zero',0)]:
    p={'amount':value,'currency':'KRW','booking_id':'validation'}
    status,_=req(AFTER,'POST','/p04/payments',p,headers(alice,**{'Idempotency-Key':'val-'+uuid.uuid4().hex[:10]}))
    assert_code('SEC-input-'+who,status,422)
# Same principal: stable retry and conflicting body properly rejected.
key4='idem-'+uuid.uuid4().hex[:12]
normal={'amount':500,'currency':'KRW','booking_id':'same'}
u1,v1=req(AFTER,'POST','/p04/payments',normal,headers(alice,**{'Idempotency-Key':key4}))
u2,v2=req(AFTER,'POST','/p04/payments',normal,headers(alice,**{'Idempotency-Key':key4}))
u3,_=req(AFTER,'POST','/p04/payments',dict(normal,amount=700),headers(alice,**{'Idempotency-Key':key4}))
s.check('SEC-idempotent-same-principal',{'first':u1,'retry':u2,'different':u3,'equal_body':v1==v2},
        {'first':200,'retry':200,'different':409,'equal_body':True})
# Race: two incompatible requests, same identity and key; exactly one accepted.
key5='race-'+uuid.uuid4().hex[:12]
def race(amount):
    return req(AFTER,'POST','/p04/payments',
               {'amount':amount,'currency':'KRW','booking_id':f'race-{amount}'},
               headers(alice,**{'Idempotency-Key':key5}))[0]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    codes=sorted([f.result() for f in [pool.submit(race,10),pool.submit(race,20)]])
s.check('SEC-concurrent-same-principal',codes,[200,409])
# Invalid bearer token and role spoofing cannot elevate a standard user.
status,_=req(AFTER,'GET','/p02/tenants/alpha/admin-report',headers={'Authorization':'Bearer invalid','X-Lab-Role':'owner'})
assert_code('SEC-invalid-token',status,401)
s.finish()
