#!/usr/bin/env bash
# Independent synthetic Before/After replay; does NOT touch port 8420.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec python3 scripts/reproduce_all.py
