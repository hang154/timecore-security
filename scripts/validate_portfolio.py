#!/usr/bin/env python3
"""Validate claim-to-evidence consistency for SUNYEDO synthetic P02/P04 portfolio.

Inputs: artifacts/verification-v2.json; artifacts/p02_test_matrix.csv;
  artifacts/p04_test_matrix.csv; artifacts/before_after_results.csv;
  artifacts/claim_evidence_matrix.csv; fixtures/sandbox_before.py; README.md.
Outputs: stdout summary + nonzero exit code on mismatches (no file mutation).
Parameters: fixed v2 case totals 13/18/20 and baseline fixture SHA-256.
Dedupe rule: unique case id within each suite and unique case_id in each CSV.
Calendar denominator: none; counts are per unique test, not per day.
Random seed: none; the integration runner uses random ephemeral credentials/ports.
Run: python3 scripts/validate_portfolio.py
Existing-artifact comparison: JSON case results vs CSV rows and evidence hashes.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
EXPECTED = {"p02_before": 13, "p04_before": 18, "before_after": 20}
CSVS = {
    "p02_before": "p02_test_matrix.csv",
    "p04_before": "p04_test_matrix.csv",
    "before_after": "before_after_results.csv",
}
SOURCE_SHA = "375c0a4e94cf669489ebfff320e505afde826f6ac1546348010cc7d3a52503d5"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    path = ART / "verification-v2.json"
    raw = path.read_bytes()
    results = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()

    source = ROOT / "fixtures/sandbox_before.py"
    require(hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA,
            "Baseline fixture SHA-256 mismatch")
    require(results.get("before_source_sha256") == SOURCE_SHA,
            "Evidence refers to a different baseline source")
    require(results.get("version") == 2, "Unexpected evidence version")
    require(results.get("kind") == "isolated-synthetic-http-replay",
            "Evidence is not an isolated HTTP replay")
    require(results.get("all_passed") is True, "Evidence reports failed assertions")

    total = 0
    for suite, count in EXPECTED.items():
        cases = results["cases"][suite]
        totals = results["suite_counts"][suite]
        ids = [row["id"] for row in cases]
        require(len(cases) == len(set(ids)) == count, f"{suite}: missing/duplicate IDs")
        require(totals == {"total": count, "passed": count, "failed": 0},
                f"{suite}: aggregate mismatch")
        require(all(r.get("pass") is True and r.get("observed") == r.get("expected")
                    for r in cases), f"{suite}: individual mismatch")
        with (ART / CSVS[suite]).open(newline="", encoding="utf-8") as fh:
            csv_rows = list(csv.DictReader(fh))
        require(len(csv_rows) == count, f"{suite}: CSV row count mismatch")
        require({r["case_id"] for r in csv_rows} == set(ids),
                f"{suite}: CSV case IDs mismatch")
        index = {r["id"]: r for r in cases}
        for row in csv_rows:
            actual = index[row["case_id"]]
            require(row["pass"] == "yes" and json.loads(row["expected"]) == actual["expected"]
                    and json.loads(row["observed"]) == actual["observed"],
                    f"{suite}: CSV and JSON differ for {row['case_id']}")
        total += count

    ba = {r["id"]: r for r in results["cases"]["before_after"]}
    require(ba["BA-05"]["observed"]["after_anon"] == 401, "BA-05 anonymous read")
    require(ba["BA-05"]["observed"]["after_owner"] == 200, "BA-05 owner read")
    require(ba["BA-05"]["observed"]["after_other_user"] == 404, "BA-05 other user")
    require(ba["BA-06"]["observed"]["after"] == [200, 200, 200, 500000],
            "BA-06 per-principal key isolation")
    require(ba["BA-07"]["observed"] == [200, 422], "BA-07 strict typing")

    with (ART / "claim_evidence_matrix.csv").open(newline="", encoding="utf-8") as fh:
        evidence_rows = list(csv.DictReader(fh))
    for row in evidence_rows:
        if "artifacts/verification-v2.json" in row["evidence"]:
            require(row["evidence_hash"] == digest,
                    f"Evidence hash stale for {row['claim']}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for marker in ("synthetic", "51 / 51", "13 / 13", "18 / 18", "20 / 20",
                   "not a client penetration test", "publication_gate.md"):
        require(marker in readme, f"README missing disclosure/evidence marker: {marker}")
    for relative in ("portfolio/cases/p02-tenant-isolation.md",
                     "portfolio/cases/p04-payment-integrity.md",
                     "portfolio/SAMPLE_REPORT.md",
                     "portfolio/SERVICES.md", "reports/PUBLICATION_GATE.md"):
        require((ROOT / relative).is_file(), f"Missing portfolio document: {relative}")

    require(total == 51, "Expected exactly 51 assertions")
    print("PASS: 51/51 case assertions match their expected observations.")
    print("NOTE: 31 baseline assertions include reproduced insecure behavior.")
    print("PASS: v2 JSON, generated CSVs, baseline SHA-256 and claim hashes agree.")
    print("PASS: portfolio disclosure and core case documents present.")
    print("This is NOT a secret-history scan or authorization to publish.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL portfolio evidence check: {exc}", file=sys.stderr)
        sys.exit(1)
