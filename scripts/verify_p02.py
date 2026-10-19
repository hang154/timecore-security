#!/usr/bin/env python3
"""Before P02: 13 explicit expected observations. Fails closed on a mismatch."""
from testlib import BEFORE, Suite, req

s = Suite('p02_before')
for tenant in ('alpha', 'beta', 'gamma'):
    code, body = req(BEFORE, 'GET', f'/p02/tenants/{tenant}/records',
        headers={'X-Lab-Tenant': tenant, 'X-Lab-Role': 'member'})
    s.check('P02-01-' + tenant, code, 200, extra_ok=isinstance(body, dict) and body.get('tenant') == tenant)

cases = [
    ('P02-02-cross', 'beta', {'X-Lab-Tenant': 'alpha', 'X-Lab-Role': 'member'}, 403, 'CONTROL'),
    ('P02-03-claim', 'gamma', {'X-Lab-Tenant': 'gamma', 'X-Lab-Role': 'owner'}, 200, 'VULNERABILITY_REPRODUCED'),
    ('P02-04-mismatch', 'beta', {'X-Lab-Tenant': 'alpha', 'X-Lab-Role': 'member'}, 403, 'CONTROL'),
    ('P02-05-admin', 'alpha', {'X-Lab-Tenant': 'alpha', 'X-Lab-Role': 'admin'}, 200, 'VULNERABILITY_REPRODUCED'),
    ('P02-06-owner', 'alpha', {'X-Lab-Tenant': 'alpha', 'X-Lab-Role': 'owner'}, 200, 'VULNERABILITY_REPRODUCED'),
    ('P02-07-no-headers', 'alpha', {}, 422, 'CONTROL'),
    ('P02-08-only-role', 'alpha', {'X-Lab-Role': 'admin'}, 422, 'CONTROL'),
    ('P02-09-unknown-tenant', 'delta', {'X-Lab-Tenant': 'delta', 'X-Lab-Role': 'member'}, 404, 'CONTROL'),
    ('P02-10-unknown-role', 'alpha', {'X-Lab-Tenant': 'alpha', 'X-Lab-Role': 'superuser'}, 403, 'CONTROL'),
]
for cid, tenant, headers, expected, category in cases:
    status, body = req(BEFORE, 'GET', f'/p02/tenants/{tenant}/records', headers=headers)
    s.check(cid, status, expected, category, extra_ok=(category != 'VULNERABILITY_REPRODUCED' or (isinstance(body, dict) and body.get('tenant') == tenant)))

_, admin = req(BEFORE, 'GET', '/p02/tenants/alpha/records', headers={'X-Lab-Tenant': 'alpha', 'X-Lab-Role': 'admin'})
status, viewer = req(BEFORE, 'GET', '/p02/tenants/alpha/records', headers={'X-Lab-Tenant': 'alpha', 'X-Lab-Role': 'viewer'})
s.check('P02-11-role-no-diff', status, 200, 'VULNERABILITY_REPRODUCED', extra_ok=admin == viewer)
s.finish()
