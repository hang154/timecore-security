#!/usr/bin/env python3
"""Synchronize SHA-256 evidence references after a fresh isolated replay.

Inputs: artifacts/verification-v2.json and artifacts/claim_evidence_matrix.csv.
Outputs: updated claim_evidence_matrix.csv evidence_hash fields (atomic replace).
Parameter: SHA-256 of the exact UTF-8 JSON file bytes, not a normalized object.
Dedupe: rows remain unchanged; duplicate claims are not collapsed.
Calendar denominator: none; SHA-256 is a byte digest, not a time-series metric.
Random seed: none; generated timestamp changes the digest on each replay.
Comparison: verifies each updated reference against the freshly computed digest.
Run: python3 scripts/sync_evidence_hashes.py
"""
import csv
import hashlib
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sync_claim_matrix(verification: Path, matrix: Path) -> str:
    digest = hashlib.sha256(verification.read_bytes()).hexdigest()
    with matrix.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames
        if not names or not {"claim", "evidence", "evidence_hash"} <= set(names):
            raise ValueError("Claim-evidence matrix schema mismatch")
        rows = list(reader)
    changed = 0
    for row in rows:
        if "artifacts/verification-v2.json" in row["evidence"]:
            row["evidence_hash"] = digest
            changed += 1
    if changed == 0:
        raise ValueError("No v2 evidence references found; refusing silent manifest mismatch")

    matrix.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="",
                                         dir=matrix.parent, prefix=".claim-",
                                         delete=False) as out:
            tmp = out.name
            writer = csv.DictWriter(out, fieldnames=names)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, matrix)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    with matrix.open(newline="", encoding="utf-8") as f:
        actual = list(csv.DictReader(f))
    for row in actual:
        if "artifacts/verification-v2.json" in row["evidence"] and row["evidence_hash"] != digest:
            raise AssertionError("New evidence hash did not persist")
    return digest


if __name__ == "__main__":
    d = sync_claim_matrix(ROOT / "artifacts/verification-v2.json",
                          ROOT / "artifacts/claim_evidence_matrix.csv")
    print(f"PASS synchronized evidence hashes to current v2 JSON SHA-256: {d}")
