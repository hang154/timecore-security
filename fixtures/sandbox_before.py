"""Synthetic environment services. No real payments, customers or model calls."""
import hashlib
import json
import sqlite3
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="Synthetic portfolio services", version="1.0")
ROLES = ["viewer", "member", "support", "billing", "manager", "auditor", "admin", "owner"]


def db():
    conn = sqlite3.connect(ROOT / ".state/sandbox.sqlite")
    conn.execute("CREATE TABLE IF NOT EXISTS payments (key TEXT PRIMARY KEY, fingerprint TEXT, amount INTEGER, status TEXT)")
    return conn


@app.get("/health")
def health():
    return {"status": "ready", "synthetic": True, "modules": ["P02", "P03", "P04"]}


@app.get("/p02/fixtures")
def fixtures():
    return {"tenants": ["alpha", "beta", "gamma"], "roles": ROLES,
            "identity": "X-Lab-Tenant and X-Lab-Role are synthetic test identities, not production authentication"}


@app.get("/p02/tenants/{tenant}/records")
def records(tenant: str, x_lab_tenant: str = Header(), x_lab_role: str = Header()):
    if tenant not in ["alpha", "beta", "gamma"]:
        raise HTTPException(404)
    if x_lab_tenant != tenant or x_lab_role not in ROLES:
        raise HTTPException(403)
    return {"tenant": tenant, "records": [{"id": tenant + "-001", "data": "SYNTHETIC ONLY"}]}


@app.get("/p03/v1/models")
def models():
    return {"object": "list", "data": [{"id": "synthetic-agent", "object": "model"}]}


@app.post("/p03/v1/chat/completions")
def completion(payload: dict):
    if payload.get("model") != "synthetic-agent":
        raise HTTPException(400, "Use synthetic-agent")
    return {"id": "lab-only", "object": "chat.completion", "model": "synthetic-agent",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "SYNTHETIC_AGENT_READY"}, "finish_reason": "stop"}]}


class Payment(BaseModel):
    amount: int = Field(gt=0, le=1000000)
    currency: str = Field(pattern="^KRW$")
    booking_id: str = Field(min_length=1, max_length=80)


@app.post("/p04/payments")
def pay(body: Payment, idempotency_key: str = Header(min_length=1, max_length=100)):
    fingerprint = hashlib.sha256(json.dumps(body.model_dump(), sort_keys=True).encode()).hexdigest()
    conn = db()
    try:
        with conn:
            conn.execute("INSERT OR IGNORE INTO payments VALUES (?, ?, ?, 'authorized')",
                         (idempotency_key, fingerprint, body.amount))
            row = conn.execute("SELECT fingerprint, amount, status FROM payments WHERE key=?", (idempotency_key,)).fetchone()
        if row[0] != fingerprint:
            raise HTTPException(409, "Idempotency key already used for another request")
        return {"synthetic": True, "payment_id": idempotency_key, "amount": row[1], "status": row[2]}
    finally:
        conn.close()


@app.get("/p04/payments/{key}")
def payment(key: str):
    conn = db()
    try:
        row = conn.execute("SELECT amount,status FROM payments WHERE key=?", (key,)).fetchone()
        if not row:
            raise HTTPException(404)
        return {"synthetic": True, "amount": row[0], "status": row[1]}
    finally:
        conn.close()
