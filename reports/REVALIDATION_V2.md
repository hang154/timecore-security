# Synthetic P02/P04 verification — publication snapshot

- On 2026-10-18, two disposable loopback instances were used to compare a
  source-locked intentionally vulnerable baseline against the example fix.
- P02 Before: 13/13 matching expected behavior, including insecure behavior.
- P04 Before: 18/18 matching expected behavior, including insecure behavior.
- Hardened and defensive regression checks: 20/20 matching expected behavior.
- The runner refuses mismatched observations and preserves legitimate user access.
- The raw historical audit logs remain in the **private original**, not this
  independently packaged public snapshot; only sanitized v2 results are shipped.

Limitations: synthetic FastAPI and SQLite, not real payment gateway,
refund/webhook, production OAuth, MFA, RLS, customer deployment, or client audit.

Reproduce with \`bash scripts/reproduce_all.sh\` and
\`python scripts/validate_portfolio.py\`.
