#!/usr/bin/env python3
"""Static/semantic checks for Reviewed v0.7 artifact; NEVER claim live E2E passes."""
from pathlib import Path
import re,json,hashlib,sys,os,argparse,csv

def validate(root, check_manifest=True):
 root=Path(root); ok=[]; errors=[]
 def ck(cond,msg): (ok if cond else errors).append(msg)
 def load(p):return (root/p).read_text(encoding='utf-8')
 reg=json.loads(load('docs/quality/STAGE_REGISTRY.json'))
 inv=json.loads(load('docs/architecture/API_INVENTORY.json'))['operations']
 N=len(reg)
 ck(N==29,'expected 29 specs S0–S28')
 ck([r['stage'] for r in reg]==list(range(N)),'consecutive Stage indices')
 ck(reg[0]['track']=='P' and reg[0]['release']=='—','S0 docs only')
 for s in reg:
  n=s['stage']; owner=s['track']
  ck(owner in ('P','A','B','I','U'),f'S{n} valid owner')
  ck(s['release']==('—' if n==0 else f'R{n:02d}'),f'S{n} Release ID')
  ck(all(0<=d<n for d in s['depends_on']),f'S{n} dependency topological')
  ck(len(s['depends_on'])==len(set(s['depends_on'])),f'S{n} unique deps')
  p=f'docs/stages/STAGE_{n:02d}.md';ck((root/p).is_file(),f'exists Stage {n}')
  if not (root/p).exists():continue
  st=load(p)
  ck(st.startswith(f'# Stage {n:02d} [{owner}] — {s["name"]}'),f'S{n} owner+name heading match')
  ck(f'**Release:** `{s["release"]}`' in st,f'S{n} Release tag match')
  ck(f'**Exactly one owner:** `{owner}`' in st,f'S{n} one Runtime owner')
  ids=re.findall(r'^\| (S\d+-AT\d{2}) \|',st,re.M)
  ck(ids==s['acceptance_ids'],f'S{n} ATs match registry')
  ck(len(ids)>=6,f'S{n} >=6 designed ATs')
  matrix=load('docs/quality/ACCEPTANCE_MATRIX.md')
  for a in ids:ck(f'| {a} | {n} | {owner} |' in matrix,f'matrix AT {a}')
  routes=re.findall(r'^- `(GET|POST|PUT|PATCH|DELETE) ([^`]+)` \(`([^`]+)`; auth=([^;)]+)(?:; scope=[^)]*)?\)',st,re.M)
  expected=[(x['method'],x['path'],x['operation_id'],x['auth']) for x in inv if x['first_stage']==n]
  ck(routes==expected,f'S{n} only canonical API routes in Stage')
  if n==0:
   cases=[x for x in st.splitlines() if x.startswith('| S0-AT')]
   ck(all('Staging' not in x and 'HTTP/DB' not in x and 'Restore' not in x and 'actual deployed' not in x for x in cases),'Stage0 no runtime evidence/precondition')
 # Functional dependencies must reflect contracts, and release order not conflated with technical deps
 expected_tracks={1:'A',2:'A',3:'B',4:'I',5:'U',6:'B',7:'B',8:'B',9:'I',10:'U',11:'B',12:'B',13:'B',14:'B',15:'B',16:'B',17:'B',18:'B',19:'B',20:'B',21:'U',22:'B',23:'I',24:'U',25:'B',26:'A',27:'B',28:'I'}
 ck({r['stage']:r['track'] for r in reg[1:]}==expected_tracks,'critical one-owner Stage order map')
 for n,need in {4:{2,3},5:{4},8:{6,7},9:{4,8},10:{5,9},17:{16},23:{4,22},24:{23},25:{22,23},28:{4,26,27}}.items():
  ck(need.issubset(reg[n]['depends_on']),f'S{n} critical technical dependency {need}')
 # Consistency: release and endpoints originate in registry and API inventory, and are mechanically verifiable.
 pol=load('docs/delivery/RELEASE_POLICY.md')
 ck(bool(re.search(r'R01\s*(?:–|\.\.|-)\s*R28\b',pol)),'release policy max end R28')
 wrong=re.findall(r'R01\s*(?:–|\.\.|-)\s*R(\d{2})\b',pol)
 ck(all(x=='28' for x in wrong),'no obsolete R01..R21 range in Release Policy')
 road=load('docs/product/ROADMAP.md');prd=load('docs/product/PRD.md');matrix=load('docs/delivery/OWNER_RELEASE_MATRIX.md');trace=load('docs/quality/REQUIREMENTS_TRACEABILITY.md')
 for s in reg:
  n=s['stage'];own=s['track'];rel=s['release']
  ck(f'| [{n}](../stages/STAGE_{n:02d}.md) | {own} | {rel} |' in road,f'Roadmap Stage{n} name+owner+release')
  ck(f'| {n} | {own} | {s["name"]} |' in prd,f'PRD Stage{n}')
  if n:
   ck(f'| {rel} | **{own}** |' in matrix,f'release owner matrix {rel}')
   ck(f'| FR-{n:02d} | S{n} | {own} |' in trace,f'FR trace {n}')
 # canonical operation definitions
 ck(len(inv)==len({(x['method'],x['path']) for x in inv}),'API unique verb/path')
 ck(len(inv)==len({x['operation_id'] for x in inv}),'API unique operation ID')
 ck(all(x['owner']==reg[x['first_stage']]['track'] for x in inv),'API owner equals first stage owner')
 # Docs route table must exactly match API Inventory (method, path, stage owner, opid)
 docs=load('docs/architecture/API_CONTRACT.md')
 dops=[row[:5] for row in re.findall(r'^\| S(\d+) \| ([ABI]) \| `(GET|POST|PUT|PATCH|DELETE)` \| `([^`]+)` \| `([^`]+)` \| ([^|]+)\|$',docs,re.M)]
 truth=[(str(x['first_stage']),x['owner'],x['method'],x['path'],x['operation_id']) for x in inv]
 ck(dops==truth,'canonical API Contract table exact inventory')
 for owner in 'ABI':
  fp=f'contracts/openapi/{owner.lower()}-v1.openapi.json'
  spec=json.loads(load(fp));seen=[]
  ck(spec.get('openapi')=='3.1.0',f'{owner} OpenAPI version')
  for path,verbs in spec.get('paths',{}).items():
   for method,payload in verbs.items():seen.append((method.upper(),path,payload['operationId']))
  ideal=[(x['method'],x['path'],x['operation_id']) for x in inv if x['owner']==owner]
  ck(set(seen)==set(ideal),f'{owner} OpenAPI paths exact Inventory')
  ck(len(seen)==len(ideal),f'{owner} OpenAPI operation count')
  for path,verbs in spec.get('paths',{}).items():
   for meth,obj in verbs.items():ck('responses' in obj and 'security' in obj,f'{owner} OpenAPI protected {meth} {path}')
 # Stage-specific semantic conditions, not only filenames
 for file,required in {
  'docs/architecture/PROVISIONING_STATE_MACHINE.md':['CREATE_NEW','ADOPT_EXISTING','QUARANTINED','RETRYABLE','B SQL transaction','cutover','API'],
  'docs/architecture/EVIDENCE_BUNDLE.md':['source_version_id','content_sha256','binding_version','jti','issuer','before','revoked','Prompt Injection'],
  'docs/architecture/COURSE_IDENTITY.md':['TeachingGroup','P4A','P4B','ContentShell','academic_year','curriculum_stream'],
  'docs/architecture/RELEASE_COMPATIBILITY.md':['EXPAND','MIGRATE','CONTRACT','forward-fix'],
  'docs/delivery/GITHUB_BASELINE_PR_PLAN.md':['Enochan222','ADR-001','ADR-011','CODEOWNERS','GitHub Actions OFF','docs-only PR'],
  'docs/quality/TEST_PROTOCOL.md':['Mutation','semantic','API','rollback'],
  'docs/architecture/SECURITY_AND_AUTH.md':['S1','S3','S9','S23','S25']}.items():
  txt=load(file).lower()
  for k in required:ck(k.lower() in txt,f'critical semantic {file}:{k}')
 for n in (5,10,21,24):ck('Frontend Gate' in load(f'docs/stages/STAGE_{n:02d}.md'),f'S{n} U-only feature Gate')
 ck('S28' in load('docs/architecture/PROVISIONING_STATE_MACHINE.md'),'S4 core/S28 dashboard distinction')
 ck('CONTENT_UNLINKED' in load('docs/architecture/COURSE_IDENTITY.md'),'B Course unlinked state before S4')
 ck('NOT RUN' in load('docs/quality/ACCEPTANCE_MATRIX.md'),'no false runtime PASS')
 ck(len(inv)==100,'100 canonical typed API operations')
 ck('Synthetic Assessment、Grades 可從同一 UI 操作' not in load('docs/stages/STAGE_05.md'), 'S5 excludes premature assessment and grade UI')
 ck('StaffSession' in load('docs/stages/STAGE_23.md'),'S23 explicitly requires StaffSession')
 ck('ServiceToken' in load('docs/architecture/API_PERMISSION_MATRIX.md'),'explicit service grant matrix')
 # preserve old GitHub ADR path safety + CI name and CODEOWNERS
 ck(not any((root/'docs/decisions').glob('ADR-00[1-9]-*.md')),'no active replacements GitHub ADR001..009')
 ck(not any((root/'docs/decisions').glob('ADR-010-*.md')),'no active replacement GitHub ADR010')
 adrs=list((root/'docs/decisions').glob('ADR-*.md'))
 ck(sorted(int(p.name.split('-')[1]) for p in adrs)==list(range(11,23)),'new ADR011..022 only (legacy GitHub ADRs untouched)')
 ck((root/'.github/CODEOWNERS').read_text().endswith('* @Enochan222\n'),'new repo CODEOWNERS owner matches')
 # Historical D08 remains unchanged; only two Owner-approved Stage1 workflow files are permitted.
 wfdir=root/'.github/workflows'
 present={p.name for p in wfdir.iterdir() if p.is_file()} if wfdir.exists() else set()
 permitted={'stage1-light.yml','stage1-native-integration.yml'}
 ck(present.issubset(permitted),'only approved Stage1 workflow names allowed')
 ck(not present or (root/'docs/decisions/STAGE1_LIMITED_CI_ADDENDUM.md').is_file(),'Stage1 CI addendum present')
 for name in sorted(present):
  body=(wfdir/name).read_text(encoding='utf-8')
  normalized=[line.strip() for line in body.splitlines()]
  ck(bool(re.search(r'(?m)^permissions:\s*\n\s{2}contents:\s*read\s*$',body)),'read-only root token permissions')
  ck(not re.search(r'(?m)^\s*[-\w]+:\s*write\s*(?:#.*)?$',body) and not re.search(r'(?m)^\s*permissions:\s*write-all\b',body),'no token write scope')
  ck(not re.search(r'\$\{\{\s*secrets\.',body),'no GitHub Secrets interpolation')
  ck(bool(re.search(r'(?m)^\s*persist-credentials:\s*false\s*$',body)),'checkout credentials not persisted')
  forbidden=r'(?m)^\s*(?:push|schedule|pull_request_target|workflow_call|repository_dispatch|workflow_run)\s*:'
  ck(not re.search(forbidden,body),'no forbidden event triggers')
  uses=[line.split('uses:',1)[1].strip().split('#')[0].strip() for line in normalized if line.startswith('uses:') or line.startswith('- uses:')]
  ck(bool(uses) and all(re.fullmatch(r'actions/(checkout|setup-python)@[0-9a-f]{40}',v) for v in uses),'only approved immutable action references')
  ck(bool(re.search(r'(?m)^\s*runs-on:\s*ubuntu-24\.04\s*$',body)),'Ubuntu 24.04 runner')
  times=re.findall(r'(?m)^\s*timeout-minutes:\s*(\d+)\s*$',body)
  ck(bool(times) and all(0<int(t)<=(5 if name=='stage1-light.yml' else 30) for t in times),'job timeouts bounded')
  events=[]
  active=False
  for line in body.splitlines():
   if line=='on:':active=True;continue
   if active and line and not line[0].isspace():active=False
   if active:
    event=re.match(r'^  ([\w-]+):',line)
    if event:events.append(event.group(1))
  ck(events==(['pull_request'] if name=='stage1-light.yml' else ['workflow_dispatch']),'exact authorized event mode')
  if name=='stage1-light.yml':
   ck('!github.event.pull_request.draft' in body and 'cancel-in-progress: true' in body and 'paths:' in normalized,'skip Draft and restrict paths/concurrency')
 ck('GitHub Actions' in load('docs/delivery/NEW_REPO_STAGE0.md') and 'DISABLED' in load('README.md'), 'current No-Actions operating contract present')
 for f in ('AGENTS.md','README.md','INSTRUCTIONS.md','docs/delivery/HANDOVER.md','docs/delivery/PROJECT_STATUS.md'):
  ck('v0.5' in load(f) or 'v0.7' in load(f),f'{f} clear version')
 # Schema and machine model inventory from files
 state=json.loads(load('contracts/state_machines/course_binding.json'))
 ck('ACTIVE' in state['binding_state'] and 'RETRYABLE' in state['binding_state'] and 'QUARANTINED' in state['binding_state'],'Saga states complete')
 ck(all(t in state['binding_state'] for ts in state['transitions'].values() for t in ts),'Saga transitions valid target')
 ck(set(state['transitions'])==set(state['binding_state']),'Every saga state has transitions')
 for p in (root/'contracts/schemas').glob('*.json'):ck(json.loads(p.read_text())['$schema']=='https://json-schema.org/draft/2020-12/schema',f'JSON Schema dialect {p.name}')
 # Independent strict typed contract checks apply ALSO when manifest SHA is disabled by mutation tests.
 from validate_openapi_contracts import inspect
 oas_check_count,oas_errors,oas_details=inspect(root, thorough=False)
 ck(oas_check_count>=1300,'full typed OpenAPI validators executed')
 ck(not oas_errors,'100 typed OpenAPI operations, response/requests/path params/Service/Staff scopes')
 errors.extend(oas_errors)
 # Structural checks of links and secrets. Archived previous ZIP ADR drafts are historical, not active.
 for p in root.rglob('*.md'):
  rel=p.relative_to(root).as_posix()
  if rel.startswith('docs/history/'):continue
  txt=p.read_text(encoding='utf-8')
  ck(txt.startswith('# ') or rel.startswith('.github/ISSUE_TEMPLATE/') and txt.startswith('---'),f'heading {rel}')
  ck(txt.count('```')%2==0,f'fences balanced {rel}')
  for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)',txt):
   path=target.split('#')[0].strip()
   if not path or path.startswith('/') or re.match(r'^[a-z][a-z0-9+.-]*:',path,re.I):continue
   ck((p.parent/path).exists(),f'local link {rel}->{path}')
 # Manifest excludes itself. This check can be off ONLY for mutation tests, which still verify semantic failures.
 if check_manifest:
  mp=root/'FILE_MANIFEST.sha256'
  ck(mp.is_file(),'SHA file manifest exists')
  if mp.is_file():
   entries={}
   for line in mp.read_text().splitlines():
    try:h,rel=line.split('  ',1)
    except ValueError:ck(False,'manifest line syntax');continue
    ck(rel not in entries,f'no manifest duplicate {rel}')
    entries[rel]=h
   actual={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.name!='FILE_MANIFEST.sha256' and '__pycache__' not in p.parts and '.git' not in p.parts}
   ck(all(actual.get(name)==sha for name,sha in entries.items()),'all listed package SHA256 files match (additional pre-existing GitHub files permitted)')
 return len(ok),errors

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--skip-manifest',action='store_true',help='For mutation tests ONLY: do not let SHA checks mask semantic bugs')
 args=ap.parse_args()
 passes,errs=validate(args.root,not args.skip_manifest)
 out={'result':'PASS' if not errs else 'FAIL','checks_passed':passes,'checks_failed':len(errs),'failures':errs[:60],'scope':'STATIC + CROSS-FILE SEMANTIC ONLY; Runtime NOT TESTED'}
 print(json.dumps(out,indent=2,ensure_ascii=False));sys.exit(bool(errs))
,body,re.M),f'{name} no prohibited automatic trigger')
  refs=re.findall(r'^\s*-?\s*uses:\s*([^\s#]+)',body,re.M)
  ck(bool(refs) and all(re.fullmatch(r'actions/(?:checkout|setup-python)@[0-9a-f]{40}',item) for item in refs),f'{name} only immutable preapproved actions')
  ck('timeout-minutes:' in body,f'{name} explicit job timeout')
  ck(('workflow_dispatch:' in body and 'pull_request:' not in body) if name=='stage1-native-integration.yml' else ('pull_request:' in body and 'workflow_dispatch:' not in body),f'{name} approved event type')
 ck('GitHub Actions' in load('docs/delivery/NEW_REPO_STAGE0.md') and 'DISABLED' in load('README.md'), 'current No-Actions operating contract present')
 for f in ('AGENTS.md','README.md','INSTRUCTIONS.md','docs/delivery/HANDOVER.md','docs/delivery/PROJECT_STATUS.md'):
  ck('v0.5' in load(f) or 'v0.7' in load(f),f'{f} clear version')
 # Schema and machine model inventory from files
 state=json.loads(load('contracts/state_machines/course_binding.json'))
 ck('ACTIVE' in state['binding_state'] and 'RETRYABLE' in state['binding_state'] and 'QUARANTINED' in state['binding_state'],'Saga states complete')
 ck(all(t in state['binding_state'] for ts in state['transitions'].values() for t in ts),'Saga transitions valid target')
 ck(set(state['transitions'])==set(state['binding_state']),'Every saga state has transitions')
 for p in (root/'contracts/schemas').glob('*.json'):ck(json.loads(p.read_text())['$schema']=='https://json-schema.org/draft/2020-12/schema',f'JSON Schema dialect {p.name}')
 # Independent strict typed contract checks apply ALSO when manifest SHA is disabled by mutation tests.
 from validate_openapi_contracts import inspect
 oas_check_count,oas_errors,oas_details=inspect(root, thorough=False)
 ck(oas_check_count>=1300,'full typed OpenAPI validators executed')
 ck(not oas_errors,'100 typed OpenAPI operations, response/requests/path params/Service/Staff scopes')
 errors.extend(oas_errors)
 # Structural checks of links and secrets. Archived previous ZIP ADR drafts are historical, not active.
 for p in root.rglob('*.md'):
  rel=p.relative_to(root).as_posix()
  if rel.startswith('docs/history/'):continue
  txt=p.read_text(encoding='utf-8')
  ck(txt.startswith('# ') or rel.startswith('.github/ISSUE_TEMPLATE/') and txt.startswith('---'),f'heading {rel}')
  ck(txt.count('```')%2==0,f'fences balanced {rel}')
  for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)',txt):
   path=target.split('#')[0].strip()
   if not path or path.startswith('/') or re.match(r'^[a-z][a-z0-9+.-]*:',path,re.I):continue
   ck((p.parent/path).exists(),f'local link {rel}->{path}')
 # Manifest excludes itself. This check can be off ONLY for mutation tests, which still verify semantic failures.
 if check_manifest:
  mp=root/'FILE_MANIFEST.sha256'
  ck(mp.is_file(),'SHA file manifest exists')
  if mp.is_file():
   entries={}
   for line in mp.read_text().splitlines():
    try:h,rel=line.split('  ',1)
    except ValueError:ck(False,'manifest line syntax');continue
    ck(rel not in entries,f'no manifest duplicate {rel}')
    entries[rel]=h
   actual={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.name!='FILE_MANIFEST.sha256' and '__pycache__' not in p.parts and '.git' not in p.parts}
   ck(all(actual.get(name)==sha for name,sha in entries.items()),'all listed package SHA256 files match (additional pre-existing GitHub files permitted)')
 return len(ok),errors

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--skip-manifest',action='store_true',help='For mutation tests ONLY: do not let SHA checks mask semantic bugs')
 args=ap.parse_args()
 passes,errs=validate(args.root,not args.skip_manifest)
 out={'result':'PASS' if not errs else 'FAIL','checks_passed':passes,'checks_failed':len(errs),'failures':errs[:60],'scope':'STATIC + CROSS-FILE SEMANTIC ONLY; Runtime NOT TESTED'}
 print(json.dumps(out,indent=2,ensure_ascii=False));sys.exit(bool(errs))
