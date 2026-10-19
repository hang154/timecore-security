"""Create non-committed, random, per-user local lab credentials (never log passwords)."""
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

USERS = {
    'alice': ('alpha', 'member'),
    'bob': ('beta', 'member'),
    'carol': ('gamma', 'member'),
    'root_alpha': ('alpha', 'owner'),
}
ROUNDS = 240_000


def private_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as output:
        json.dump(payload, output, sort_keys=True)
        output.write('\n')


def create(state_dir: Path):
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_dir.chmod(0o700)
    accounts, client_credentials = {}, {}
    for name, (tenant, role) in USERS.items():
        password = secrets.token_urlsafe(32)
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ROUNDS)
        accounts[name] = {'tenant': tenant, 'role': role, 'salt': salt.hex(),
                          'password_hash': digest.hex(), 'rounds': ROUNDS}
        client_credentials[name] = password
    private_json(state_dir / 'users.json', accounts)
    private_json(state_dir / 'test-credentials.json', client_credentials)
    return state_dir / 'users.json', state_dir / 'test-credentials.json'


if __name__ == '__main__':
    location = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.state')
    user_file, client_file = create(location)
    print(f'Created ephemeral synthetic account fixtures: {user_file} / {client_file}; secrets not printed')
