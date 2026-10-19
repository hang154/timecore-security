# timecore-security — Evidence-backed API & Payment Security Portfolio

**Synthetic laboratory studies · P02 authorization · P04 payment integrity**

> This repository illustrates two reproducible synthetic API security studies.
> It is **not a client penetration test**, a payment-gateway certification,
> or evidence of real customer loss or prevention of loss.

## Cases

| Case | Observed risk in a deliberately vulnerable fixture | Local defensive retest |
| --- | --- | --- |
| [P02 Tenant Isolation](portfolio/cases/p02-tenant-isolation.md) | Caller-defined organization/role headers let a caller impersonate a tenant | Anonymous 401, cross-tenant 403; own-tenant 200 preserved |
| [P04 Payment Integrity](portfolio/cases/p04-payment-integrity.md) | Anonymous payment lookup and global idempotency-key collision | Anonymous 401, owner 200, other user 404; principal-scoped keys |

## Verification results (recorded 2026-10-18)

- **13 / 13** baseline P02 cases matched expected observations (some insecure).
- **18 / 18** baseline P04 cases matched expected observations (some insecure).
- **20 / 20** hardened and security-regression cases passed.
- **51 / 51** total *test assertions* matched expectations. This is **not**
  a security certification or a proof that all vulnerabilities are fixed.

Evidence: [machine-readable JSON](artifacts/verification-v2.json) ·
[synthetic report](portfolio/SAMPLE_REPORT.md) ·
[reproduction notes](reports/REVALIDATION_V2.md)

## Reproduce on your own computer

Python 3.10+ and a disposable local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lab.txt
bash scripts/reproduce_all.sh
python scripts/validate_portfolio.py
```

The runner binds to loopback-only random ports, creates random test credentials,
checks the original baseline SHA-256, and deletes the temporary servers and data.
No live user, PG, SaaS subscription, refund, webhook, cloud RLS, or external
customer infrastructure is tested.

## Intended application / portfolio services

[Proposed review service scopes](portfolio/SERVICES.md) ·
[Shop and D2C application](portfolio/industries/ecommerce.md) ·
[B2B SaaS](portfolio/industries/b2b-saas.md)

Any service engagement requires **written owner authorization**, an agreed
asset list, and scoped safe testing. The public synthetic reports are not
prior paid customer case studies.

## Publication / provenance

This curated snapshot was generated from a private research repository without
its original Git history or historical private log files. Inspect
[publication notes](reports/PUBLICATION_GATE.md) and
[NOTICE.md](NOTICE.md). Public visibility is **not** an open-source license.
Copyright (c) 2026 timecore-security. All rights reserved.

**한국어:** 실제 고객사나 결제대행사 시스템이 아닌 합성 테스트 환경에서
테넌트 격리, 결제정보 소유권, 멱등성 키 충돌을 재현하고 보완했습니다.
보안진단 고객 실적 또는 PG 보안 인증으로 표시하지 않습니다.
