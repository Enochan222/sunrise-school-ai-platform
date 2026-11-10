#!/usr/bin/env python3
"""Independent v0.7.5 review: reuse decisions, dependency consumers, AT rendering.
No live HTTP/DB/AI tests. This source audit relies on separately examined
Open Notebook ZIP; optional --upstream-root can recheck some source facts.
"""
from pathlib import Path
import re, json, sys, argparse

REQUIRED_DEP={21:{10,17,18,19,20},22:{3,17,18,20},24:{5,21,23},27:{17,18,20,25}}
OWNERS='PABIU'
BANNED_TRAPS={1:['不得將原生', 'Policy Gateway'],2:['不可變', 'Source'],8:['Queue', 'B'],21:['S18','S19'],22:['S18','S20']}
def inspect(root, upstream_root=None):
 root=Path(root);errors=[];ncheck=0
 def ck(b,msg):
  nonlocal ncheck
  ncheck+=1
  if not b:errors.append(msg)
 reg=json.loads((root/'docs/quality/STAGE_REGISTRY.json').read_text())
 control=json.loads((root/'docs/quality/STAGE_CONTROL_MATRIX.json').read_text())
 x=json.loads((root/'docs/quality/STAGE_REUSE_MAP.json').read_text())
 ck(len(reg)==len(control)==len(x)==29,'29 stage/controls/reuse')
 ck([a['stage'] for a in x]==list(range(29)),'ordered 29 reuse records')
 owner={a['stage']:a['track'] for a in reg}
 for n,(a,b,c) in enumerate(zip(reg,control,x)):
  ck(a['stage']==b['stage']==c['stage']==n,f'S{n} stage IDs match')
  ck(a['track'] in OWNERS and b['owner']==c['owner']==a['track'],f'S{n} only one owner')
  ck(a['depends_on']==b['depends_on']==c['depends_on'],f'S{n} reuse/card/registry technical deps same')
  ck(all(0<=i<n for i in a['depends_on']),f'S{n} topological prerequisites')
  for k in ('reuse_existing_or_reference','do_not_rebuild','sunrise_owner_gap','critical_risk','impact_on_next','trial_surface'):
   ck(isinstance(c.get(k),str) and len(c[k])>25,f'S{n} substantive {k}')
  fp=root/f'docs/stages/STAGE_{n:02d}.md';text=fp.read_text()
  ck(text.count('## v0.7.5 — Reuse-first 工程決策')==1,f'S{n} one reuse section')
  for k in ('reuse_existing_or_reference','do_not_rebuild','sunrise_owner_gap','critical_risk','impact_on_next','trial_surface'):
   ck(c[k] in text,f'S{n} {k} shown')
  refs=[int(t) for t in re.findall(r'\bS(\d{1,2})\b',' '.join([c['impact_on_next']]))]
  ck(not refs or all(0<=t<=28 for t in refs),f'S{n} refs in range')
  header=f"**Technical prerequisites:** {', '.join('S'+str(d) for d in a['depends_on']) or 'None'}"
  ck(header in text,f'S{n} stage header matches deps')
  # Validate the entire Markdown acceptance table is contiguous, correctly
  # bounded by table header and no stray rows that markdown parsers omit.
  lines=text.splitlines();ids=a['acceptance_ids']
  indices=[idx for idx,line in enumerate(lines) if re.fullmatch(r'\| S\d+-AT\d{2} \|.*\|',line)]
  ck(len(indices)==len(ids),f'S{n} acceptance count matches registry')
  ck(indices==list(range(indices[0],indices[-1]+1)) if indices else False,f'S{n} AT table contiguous, no blank row')
  got=[re.match(r'^\| (S\d+-AT\d{2}) \|',lines[j]).group(1) for j in indices]
  ck(got==ids,f'S{n} actual markdown AT order/IDs')
  ck(f'（{len(ids)} 項）' in text,f'S{n} displayed AT count correct')
  ck('**真實試用入口：**' in text,f'S{n} demo/access mechanism stated')
 for n,needed in REQUIRED_DEP.items():ck(needed.issubset(reg[n]['depends_on']),f'S{n} critical consumer dependencies')
 children={n:[] for n in range(29)}
 for a in reg:
  for dep in a['depends_on']:children[dep].append(a['stage'])
 for a,b in zip(reg,control):ck(children[a['stage']]==b['downstream'],f'S{a["stage"]} control children mirror Registry')
 roadmap=(root/'docs/product/ROADMAP.md').read_text()
 backlog=(root/'docs/delivery/BACKLOG.md').read_text()
 for a in reg:
  n=a['stage']; dep=', '.join('S'+str(d) for d in a['depends_on']) or '—'
  matching=[line for line in roadmap.splitlines() if line.startswith(f'| [{n}](../stages/STAGE_{n:02d}.md) |')]
  ck(len(matching)==1 and matching[0].split('|')[4].strip()==dep,f'S{n} roadmap dependency exact')
  w=[line for line in backlog.splitlines() if line.startswith(f'| S{n:02d}-{a["track"]}-WORK |')]
  ck(len(w)==1 and w[0].split('|')[3].strip()==dep,f'S{n} backlog dependency exact')
  ck(not w or w[0].split('|')[5].strip().endswith(a['acceptance_ids'][-1].split('-')[-1]),f'S{n} backlog AT range end')
 # B/U/I/A independence & substantive references
 for rel in ('docs/architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md','docs/delivery/STAGE_FLOW_ENGINEERING_AUDIT.md','docs/delivery/REUSE_FIRST_IMPLEMENTATION_RULES.md'):
  ck((root/rel).is_file(),f'new document {rel}')
 audit=(root/'docs/architecture/OPEN_NOTEBOOK_REUSE_AUDIT.md').read_text()
 for fact in ('ON-01','ON-16','api/auth.py','api/command_service.py','SourceCreate.notebooks','GET /sources','SourceVersion','Gemini','podcast'):
  ck(fact.lower() in audit.lower(),f'upstream capabilities / warning {fact}')
 ck('100 candidate' in audit and '310 designed ATs' in audit,'do not claim new API or AT count')
 if upstream_root:
  up=Path(upstream_root)
  files=['api/routers/notebooks.py','api/routers/sources.py','api/routers/search.py','api/auth.py','api/models.py','api/command_service.py','api/routers/credentials.py','api/routers/transformations.py','docker-compose.yml']
  for rel in files:ck((up/rel).is_file(),f'upstream source exists {rel}')
  source=lambda name:(up/name).read_text(encoding='utf-8')
  ck('if not self.password:' in source('api/auth.py'),'upstream auth disabled when password absent')
  ck('return []' in source('api/command_service.py') and 'return True' in source('api/command_service.py'),'upstream command listing/cancel placeholders')
  ck('An empty scope means the whole knowledge base' in source('api/models.py'),'upstream global scope empty')
  ck('notebooks: Optional[List[str]]' in source('api/models.py'),'upstream multi notebook sources')
  ck('GET /credentials' in source('api/routers/credentials.py'),'upstream native credential management')
  ck('@router.post("/search", response_model=SearchResponse)' in source('api/routers/search.py'),'upstream text/vector search')
  ck('127.0.0.1:8000:8000' in source('docker-compose.yml'),'surreal DB bind observed')
  ck('root:root' in source('docker-compose.yml'),'surreal default credential risk')
  ck('OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me' in source('docker-compose.yml'),'upstream placeholder encryption key')
 return ncheck,errors
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--upstream-root');ns=ap.parse_args()
 n,e=inspect(ns.root,ns.upstream_root)
 print(json.dumps({'result':'PASS' if not e else 'FAIL','checks':n,'failures':e[:30],'failure_count':len(e),'scope':'SOURCE STATIC + STAGE CONTRACT QA, NOT RUNTIME'},ensure_ascii=False,indent=2))
 sys.exit(bool(e))
