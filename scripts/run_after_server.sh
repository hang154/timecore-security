#!/usr/bin/env bash
# Standalone isolated After demo, using ephemeral randomized accounts (not real auth).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
STATE="${SUNYEDO_LAB_STATE_DIR:-$(mktemp -d -t sunyedo-safe-XXXXXX)}"
if [[ ! -f "$STATE/users.json" ]]; then
    python3 scripts/fixture_auth.py "$STATE"
fi
export SUNYEDO_LAB_STATE_DIR="$STATE"
export SUNYEDO_LAB_USERS_FILE="$STATE/users.json"
echo 'Standalone After synthetic server on 127.0.0.1:8421; credentials kept in private fixture file, not printed.'
exec python3 -m uvicorn sandbox_safe:app --app-dir scripts --host 127.0.0.1 --port 8421
