"""P02/P04 synthetic Before/After defense lab; NOT a production authentication service."""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, StrictInt

ROOT = Path(__file__).resolve().parents[1]
STATE = Path(os.environ.get('SUNYEDO_LAB_STATE_DIR', str(ROOT / '.state'))).resolve()
USERS_FILE = os.environ.get('SUNYEDO_LAB_USERS_FILE')
if not USERS_FILE:
    raise RuntimeError('SUNYEDO_LAB_USERS_FILE is required; use reproduce_all.sh')
with open(USERS_FILE, encoding='utf-8') as f:
    USERS = json.load(f)
if not USERS or not all(set(('tenant', 'role', 'salt', 'password_hash', 'rounds')) <= set(u) for u in USERS.values()):
    raise RuntimeError('Synthetic users config incomplete')
STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
STATE.chmod(0o700)
DB_PATH = STATE / 'sandbox_safe.sqlite'
ROLES = ['viewer', 'member', 'support', 'billing', 'manager', 'auditor', 'admin', 'owner']
TENANTS = ['alpha', 'beta', 'gamma']
TOKENS = {}
TOKENS_LOCK = threading.Lock()
TOKEN_TTL_SECONDS = 3600
app = FastAPI(title='Synthetic P02/P04 defense lab', version='2.1')


def db():
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.execute('PRAGMA busy_timeout = 15000')
    conn.execute('CREATE TABLE IF NOT EXISTS payments ('
                 'principal TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL,'
                 'amount INTEGER NOT NULL, status TEXT NOT NULL, '
                 'PRIMARY KEY(principal,key))')
    return conn


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


@app.post('/auth/token')
def issue_token(credentials: Login):
    account = USERS.get(credentials.username)
    if not account:
        raise HTTPException(401, 'Invalid credentials')
    digest = hashlib.pbkdf2_hmac('sha256', credentials.password.encode(),
                                bytes.fromhex(account['salt']), int(account['rounds']))
    if not hmac.compare_digest(digest, bytes.fromhex(account['password_hash'])):
        raise HTTPException(401, 'Invalid credentials')
    token = secrets.token_urlsafe(32)
    with TOKENS_LOCK:
        TOKENS[token] = (credentials.username, account['tenant'], account['role'],
                         time.monotonic() + TOKEN_TTL_SECONDS)
    return {'access_token': token, 'token_type': 'bearer', 'expires_in': TOKEN_TTL_SECONDS}


def auth(authorization: str):
    if not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Missing bearer token')
    token = authorization[7:].strip()
    with TOKENS_LOCK:
        session = TOKENS.get(token)
        if session and session[3] < time.monotonic():
            TOKENS.pop(token, None)
            session = None
    if not session:
        raise HTTPException(401, 'Invalid or expired token')
    return session[:3]


@app.get('/health')
def health():
    return {'status': 'ready', 'synthetic': True, 'safe': True, 'modules': ['P02', 'P04']}


@app.get('/p02/tenants/{tenant}/records')
def records(tenant: str, authorization: str = Header(default='')):
    _, own_tenant, _ = auth(authorization)
    if tenant not in TENANTS:
        raise HTTPException(404, 'Unknown tenant')
    if own_tenant != tenant:
        raise HTTPException(403, 'Not your tenant')
    return {'tenant': tenant, 'records': [{'id': tenant + '-001', 'data': 'SYNTHETIC ONLY'}]}


@app.get('/p02/tenants/{tenant}/admin-report')
def admin_report(tenant: str, authorization: str = Header(default='')):
    _, own_tenant, role = auth(authorization)
    if tenant not in TENANTS:
        raise HTTPException(404, 'Unknown tenant')
    if tenant != own_tenant:
        raise HTTPException(403, 'Not your tenant')
    if role not in ('admin', 'owner'):
        raise HTTPException(403, 'Insufficient role')
    return {'tenant': tenant, 'report': 'SYNTHETIC ADMIN REPORT'}


class Payment(BaseModel):
    amount: StrictInt = Field(gt=0, le=1_000_000)
    currency: str = Field(pattern=r'^KRW$')
    booking_id: str = Field(min_length=1, max_length=80)


@app.post('/p04/payments')
def pay(body: Payment, idempotency_key: str = Header(min_length=1, max_length=100),
        authorization: str = Header(default='')):
    username, tenant, _ = auth(authorization)
    principal = f'{tenant}:{username}'
    fingerprint = hashlib.sha256(json.dumps(body.model_dump(), sort_keys=True).encode()).hexdigest()
    conn = db()
    try:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute("INSERT OR IGNORE INTO payments (principal,key,fingerprint,amount,status) "
                     "VALUES (?,?,?,?, 'authorized')",
                     (principal, idempotency_key, fingerprint, body.amount))
        row = conn.execute('SELECT fingerprint,amount,status FROM payments '
                           'WHERE principal=? AND key=?', (principal, idempotency_key)).fetchone()
        conn.commit()
        if row[0] != fingerprint:
            raise HTTPException(409, 'Idempotency key reused with another request')
        return {'synthetic': True, 'payment_id': idempotency_key,
                'amount': row[1], 'status': row[2]}
    finally:
        conn.close()


@app.get('/p04/payments/{key}')
def payment(key: str, authorization: str = Header(default='')):
    username, tenant, _ = auth(authorization)
    principal = f'{tenant}:{username}'
    conn = db()
    try:
        row = conn.execute('SELECT amount,status FROM payments WHERE principal=? AND key=?',
                           (principal, key)).fetchone()
        if row is None:
            raise HTTPException(404, 'Payment not found')
        return {'synthetic': True, 'amount': row[0], 'status': row[1]}
    finally:
        conn.close()
