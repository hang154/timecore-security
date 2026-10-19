#!/usr/bin/env python3
"""One-command isolated before/after HTTP replay without touching the live :8420 server."""
import csv
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from fixture_auth import create
from sync_evidence_hashes import sync_claim_matrix

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'
BEFORE_SOURCE=ROOT/'fixtures/sandbox_before.py'
BEFORE_SHA='375c0a4e94cf669489ebfff320e505afde826f6ac1546348010cc7d3a52503d5'


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


def healthy(url, process):
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError(f'Lab process exited with {process.returncode}')
        try:
            with urllib.request.urlopen(url+'/health',timeout=.4) as resp:
                if resp.status==200:return
        except Exception:pass
        time.sleep(.1)
    raise RuntimeError('Lab server health timed out')


def run_suite(name, env, results_dir):
    p=subprocess.run([sys.executable,str(SCRIPT/name)],env=env,text=True,capture_output=True)
    print(p.stdout, end='')
    if p.stderr:
        print(p.stderr[-1600:],file=sys.stderr)
    if p.returncode:
        raise RuntimeError(f'{name} returned code {p.returncode}')
    filename={'verify_p02.py':'p02_before.json','verify_p04.py':'p04_before.json',
              'verify_before_after.py':'before_after.json'}[name]
    return json.loads((results_dir/filename).read_text())


def write_csv(filename, rows):
    filename.parent.mkdir(parents=True,exist_ok=True)
    with filename.open('w',newline='',encoding='utf-8') as fh:
        writer=csv.DictWriter(fh,fieldnames=['case_id','category','expected','observed','pass'])
        writer.writeheader()
        for row in rows:
            writer.writerow({'case_id':row['id'],'category':row['category'],
                'expected':json.dumps(row['expected'],ensure_ascii=False),
                'observed':json.dumps(row['observed'],ensure_ascii=False),
                'pass':'yes' if row['pass'] else 'no'})


def main():
    sha=hashlib.sha256(BEFORE_SOURCE.read_bytes()).hexdigest()
    if sha!=BEFORE_SHA:
        raise RuntimeError(f'Before fixture was modified, expected {BEFORE_SHA}; got {sha}')
    with tempfile.TemporaryDirectory(prefix='sunyedo-security-lab-') as workdir:
        work=Path(workdir)
        src=work/'before'/'fixtures';src.mkdir(parents=True)
        (work/'before'/'.state').mkdir()
        shutil.copy2(BEFORE_SOURCE,src/'sandbox_before.py')
        state=work/'after-state'
        users_file,client_file=create(state)
        bport,aport=port(),port()
        if bport==aport:aport=port()
        b_url=f'http://127.0.0.1:{bport}';a_url=f'http://127.0.0.1:{aport}'
        env=os.environ.copy()
        env.update({'SUNYEDO_BEFORE_URL':b_url,'SUNYEDO_AFTER_URL':a_url,
                    'SUNYEDO_LAB_USERS_FILE':str(users_file),
                    'SUNYEDO_LAB_STATE_DIR':str(state),
                    'SUNYEDO_TEST_CREDENTIALS_FILE':str(client_file),
                    'SUNYEDO_RESULTS_DIR':str(work/'results')})
        with (work/'before.log').open('w') as before_log, (work/'after.log').open('w') as after_log:
            before=subprocess.Popen([sys.executable,'-m','uvicorn','sandbox_before:app',
                '--app-dir',str(src),'--host','127.0.0.1','--port',str(bport)],
                stdout=before_log,stderr=subprocess.STDOUT,env=env)
            after=subprocess.Popen([sys.executable,'-m','uvicorn','sandbox_safe:app',
                '--app-dir',str(SCRIPT),'--host','127.0.0.1','--port',str(aport)],
                stdout=after_log,stderr=subprocess.STDOUT,env=env)
            try:
                healthy(b_url,before);healthy(a_url,after)
                results_dir=work/'results'
                suites=[run_suite(s,env,results_dir) for s in
                        ('verify_p02.py','verify_p04.py','verify_before_after.py')]
            except Exception:
                for log in (work/'before.log',work/'after.log'):
                    print(f'{log.name} (tail): {log.read_text()[-1300:]}',file=sys.stderr)
                raise
            finally:
                for p in (before,after):
                    if p.poll() is None:p.terminate()
                for p in (before,after):
                    try:p.wait(timeout=5)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
        counts={s['suite']:{'total':s['total'],'passed':s['passed'],'failed':s['failed']} for s in suites}
        if any(s['failed'] for s in suites):
            raise RuntimeError('Fail-closed: unexpected scenario result')
        evidence={'version':2,'checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'kind':'isolated-synthetic-http-replay','before_source_sha256':sha,
            'original_before_reference':'hang154/whitehat-workspace@5194860 runtime/sandbox.py',
            'live_8420_touched':False,'all_passed':True,'suite_counts':counts,
            'cases':{s['suite']:s['cases'] for s in suites}}
        artifacts=ROOT/'artifacts';artifacts.mkdir(exist_ok=True)
        (artifacts/'verification-v2.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
        write_csv(artifacts/'p02_test_matrix.csv',suites[0]['cases'])
        write_csv(artifacts/'p04_test_matrix.csv',suites[1]['cases'])
        write_csv(artifacts/'before_after_results.csv',suites[2]['cases'])
        sync_claim_matrix(artifacts/'verification-v2.json',
                          artifacts/'claim_evidence_matrix.csv')
        print('PASS all suites; recorded sanitized artifacts/verification-v2.json')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'FAIL reproducibility gate: {exc}',file=sys.stderr)
        raise SystemExit(1)
