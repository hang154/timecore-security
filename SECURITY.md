# Security and responsible research policy

This repository contains **intentionally vulnerable synthetic examples**.
Never deploy `fixtures/sandbox_before.py` on a public interface or treat
`scripts/sandbox_safe.py` as a production identity/payment implementation.
All reproduced attack behavior is restricted to disposable loopback services
and fictional users/ledger entries.

## Authorized testing only

The case studies explain safe testing of server-side authorization and
payment idempotency. They do not authorize testing other companies'
systems. Written permission and an agreed scope are required for any
assessment of a customer environment.

## Reporting security concerns

For a potential security issue in this portfolio, **contact the repository
owner privately** through the owner's verified channel; do not post
credentials or a working third-party exploit in a public issue.
The portfolio makes no assurance that it covers every security risk.
