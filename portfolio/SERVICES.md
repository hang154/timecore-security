# timecore-security — Scoped Web & API Security Reviews

**Positioning:** Application-security reviews of **business-critical trust boundaries**, not generic mass scanning. This document describes *proposed* services, not completed client engagements or currently active marketplace listings.

## Who this is for

| Product type | Customer concern | Relevant demonstration |
| --- | --- | --- |
| **E-commerce / D2C / subscriptions** | Another user's order or payment exposed; retry logic interferes with sales | [P04 payment integrity](cases/p04-payment-integrity.md) |
| **B2B / AI SaaS** | Cross-tenant access, user/role escalation, sensitive tool authority | [P02 tenant isolation](cases/p02-tenant-isolation.md); AgentRisk evidence is stored-result only |
| **Online education / LMS** | Student/teacher/admin access boundaries, paid-content permissions, account recovery | [P02 pattern](cases/p02-tenant-isolation.md); LMS and recovery flows themselves are *not* freshly reproduced here |

## Proposed engagement sizes (scope must be confirmed)

| Offer | Example boundary | Deliverables | Target turnaround |
| --- | --- | --- | --- |
| **Security Snapshot** | One defined web/API flow, up to 2 test roles, about 10–15 selected test scenarios | One-page executive summary, reproducible findings, scoped limitations | ~3 business days |
| **Business Logic Review** | Agreed priority workflows, up to 3 roles, about 25–35 selected scenarios | Role/object-access matrix, prioritized technical report, fix guidance, one agreed retest | ~5–7 business days |
| **Launch Security Review** | Agreed web/API + payment *or* agent authority module, up to 5 roles, about 40–60 selected scenarios | Executive and engineering reports, prioritized fixes, follow-up review and one scoped retest | ~7–10 business days |

Numbers above are **proposal design limits**, not observed throughput, customer work statistics, a guarantee that a particular risk will be found, or an offer to test every endpoint in an application. Pricing and final deliverables require a signed scope of work.

## Marketplace fit (planning, not live offer links)

| Channel | Target | Suggested offer wording |
| --- | --- | --- |
| **Kmong / 크몽** | Korean small stores and education operators | 주문·결제·회원 권한 보안 사전점검 및 수정 후 재검증 |
| **Upwork** | Overseas SaaS and AI SaaS startups | API Authorization & SaaS Business-Logic Security Review |
| **Contra** | Indie founders shipping a SaaS product | Launch-Ready SaaS Security Review |
| **Wishket / 위시켓** | Korean development companies, scoped B2B projects | 출시 전 웹/API 접근통제 점검 프로젝트 |
| **Fiverr** | Small web-app operators with one high-priority API flow | Authorized Web/API Security Snapshot |

## How work starts

1. **Ownership and authorization.** Written proof of authority from the asset owner; explicit domain/API/IP allowlist and permitted activity.
2. **Rules of engagement.** Staging preferred, agreed accounts and roles, approved window, rate limits, interruption contacts, excluded vendors.
3. **Baseline and targeted checks.** Manual authorization/business-logic scenarios and low-impact automation within the authorized scope.
4. **Confidential report.** Reproducible observations, severity *and* uncertainty, remediation guidance, affected boundary, test limitations.
5. **Optional retest.** Same agreed checks after the customer's fixes; reported as “verified in scope” rather than “fully secure.”

Default exclusions: DoS/load testing, phishing, destructive actions, high-volume extraction of personal information, third-party payment processors/cloud services/CDNs without their permission, and publication of customer vulnerabilities without separate written consent.

## Example report

View the [**synthetic sample report**](SAMPLE_REPORT.md). It is a document-layout illustration based on the lab, **not a paid client deliverable**.

**한국어:** 정상적인 서비스 사용 흐름이 유지되는지까지 함께 검증합니다. 보안 점검은 서면으로 승인된 소유 자산에만 수행하며, 실제 PG/호스팅/플랫폼 사업자의 시스템을 고객 요청만으로 시험하지 않습니다.
