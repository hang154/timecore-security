# Sample Security Finding — Authorized Payment Lookup

**DEMO ONLY · Synthetic lab · Not a client report · 2026-10-18**

This is an **illustrative sanitized deliverable** constructed from the repository's recorded P04 test results. No real company was assessed and no real payment or personal information was accessed.

| Field | Value |
| --- | --- |
| Demo ID | `SYNTH-P04-OWNERSHIP-01` |
| Asset | Local synthetic FastAPI payment fixture |
| Surface | `GET /p04/payments/{key}` |
| Category | Missing authentication / object-level authorization |
| Evidence IDs | `P04-10-anon-read` and `BA-05` |
| Verification | 2026-10-18 isolated synthetic HTTP replay |
| Severity | **Not formally rated** — context and production exploitability are unassessed |

## Executive summary

In the vulnerable synthetic application, a payment identifier alone was enough to read the corresponding synthetic payment record. The hardened example requires a verified requester and returns the record only to its owning principal.

This pattern can matter to a real store or subscription product because payment IDs are not meant to replace authentication. **No customer data leak, financial loss, or third-party weakness is claimed by this experiment.**

## Observed behavior

| Step | Expected security boundary | Recorded Before | Recorded After |
| --- | --- | --- | --- |
| Anonymous reads an existing key | Deny unauthenticated access | **HTTP 200** | **HTTP 401** |
| Authenticated owner reads own key | Preserve legitimate access | Not available: Before app had no authentication | **HTTP 200** |
| Another authenticated principal reads key | Do not disclose a different user's object | Not available: Before app had no authentication | **HTTP 404** |
| Legitimate amount on owner read | Preserve original object value | Synthetic 500,000 KRW record read anonymously | Synthetic **500,000 KRW** visible to owner |

**Evidence:** [verification-v2.json — BA-05](../artifacts/verification-v2.json), [test assertion](../scripts/verify_before_after.py), [hardened sample](../scripts/sandbox_safe.py).

## Root cause

The Before handler performed a key-based lookup and returned its record without establishing a user identity or validating ownership. A key’s presence is not sufficient authorization.

## Example remediation guidance

- Authenticate the API caller using a trusted server-side identity.
- Resolve the requested object **and** its owner within a principal-scoped database query.
- Fail anonymous access and avoid revealing whether other users’ payment objects exist.
- Re-run the legitimate owner read alongside both negative access-control cases.

## Retest conclusion

**Verified in the synthetic lab, within the listed scenarios:** `BA-05` matches 401/200/404 and preserves the owner’s recorded amount. This is not a certification of the service as a whole. Other endpoints, tenant SQL policies, refunds, provider-hosted checkout, webhook signatures, and production authentication lifecycle were not assessed.

## What a real client receives

A confidential report with agreed assets, exact testing window and identities, method, reproducible minimal evidence, risk/likelihood with assumptions, fix recommendations, and a post-fix test status. Customer reports remain private unless release is separately approved.

*Internal evidence maturity label: E4 synthetic verification. No external accreditation or client history is implied.*
