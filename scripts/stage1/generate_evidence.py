"""Run actual tests and emit redacted machine-readable evidence; no hard-coded PASS count."""
import datetime,hashlib,importlib.metadata,json,os,platform,re,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/stage1/evidence'
OUT.mkdir(parents=True,exist_ok=True)
CASES=['tests/stage1']
if (ROOT/'wp00_builder_b/tests').is_dir():
    CASES.insert(0,'wp00_builder_b/tests')
env=dict(os.environ)
if (ROOT/'wp00_builder_b').is_dir():
    env['PYTHONPATH']=str(ROOT/'wp00_builder_b')
command=[sys.executable,'-m','pytest','-q',*CASES]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
run=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
end=datetime.datetime.now(datetime.timezone.utc).isoformat()
stdout=(run.stdout+run.stderr).replace(str(ROOT),'<PROJECT_ROOT>')
(OUT/'WP00-local-pytest.log').write_text(stdout)
summary={k:int(v) for v,k in re.findall(r'(\d+)\s+(passed|failed|skipped|xfailed|xpassed|error|errors)',stdout)}
if run.returncode!=0 or not summary.get('passed') or any(summary.get(k) for k in ('failed','error','errors','xpassed')):
    status='FAIL'
else:status='PASS'
paths=[]
# Include every implementation/test/fixture input (not generated logs/evidence),
# so a changed native patcher, Compose, UI or existing WP00 fixture changes Tested Revision.
source_roots=('apps/a-vault','tests/stage1','scripts/stage1','wp00_builder_b/src',
              'wp00_builder_b/tests','wp00_builder_b/fixtures')
allow={'.py','.sh','.txt','.md','.json','.yml','.yaml','.js','.css','.pdf','.toml'}
for sub in source_roots:
    folder=ROOT/sub
    if not folder.exists(): continue
    paths.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in allow
                 and '__pycache__' not in p.parts)
file_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
snapshot=hashlib.sha256(json.dumps(file_hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
payload={'timestamp_start_utc':start,'timestamp_end_utc':end,
    'command':'python -m pytest -q '+' '.join(CASES),
    'local_preliminary_wp00_available':(ROOT/'wp00_builder_b/tests').is_dir(),
    'process_exit_code':run.returncode,'result_status':status,'parsed_results':summary,
    'python':sys.version,'pytest':importlib.metadata.version('pytest'),'os':platform.platform(),
    'snapshot_sha256':snapshot,'manifest_algorithm':'SHA256(sorted compact JSON path->file SHA256)',
    'file_sha256':file_hashes,'tested_source_pin':'5e285b7a2e435895c4ee99ad7e4b8d2af64c3239',
    'staging_backend':'RUNTIME_NOT_RUN','surrealdb':'RUNTIME_NOT_RUN','worker':'RUNTIME_NOT_RUN',
    'native_search':'RUNTIME_NOT_RUN','native_graph':'RUNTIME_NOT_RUN',
    'at01_through_at15':'NOT_RUN (partial local synthetic contract coverage only)'}
(OUT/'WP00-local-manifest.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
print('STATUS',status,'COUNTS',summary,'EXIT',run.returncode,'SNAPSHOT',snapshot)
raise SystemExit(run.returncode if status=='PASS' else 1)
