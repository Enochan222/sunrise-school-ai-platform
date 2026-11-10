#!/usr/bin/env python3
"""Independent, fast semantic QA of Stage aims/gates/collisions/future dependencies.
Design assurance only, NOT a runtime, DB, provider or deployment test.
"""
from pathlib import Path
from copy import deepcopy
import re,sys,json,argparse

REQUIRED=['goal','demo','gates','watch','prior','future','open']
HEADINGS=['## Stage 目標、驗收與跨 Stage 邊界（現行規劃判準）',
          '### 1. 目標：這一期完成甚麼？','### 2. 驗收：甚麼情況才可以標記完成？',
          '### 3. 需要特別留意的風險','### 4. 不可以與之前已完成的功能撞／互相破壞',
          '### 5. 對之後 Stage 的影響／現在應預留但不提早做',
          '### 6. 暫定參考，暫時不作技術承諾','### 7. 這一期的停工／退回判準']

def inspect(root,records=None,check_files=True):
    root=Path(root)
    errs=[];passed=0
    def ck(ok,why):
        nonlocal passed
        if ok:passed+=1
        else:errs.append(why)
    reg=json.loads((root/'docs/quality/STAGE_REGISTRY.json').read_text(encoding='utf8'))
    records=records if records is not None else json.loads((root/'docs/quality/STAGE_CONTROL_MATRIX.json').read_text(encoding='utf8'))
    ck(len(reg)==29 and len(records)==29,'exactly 29 registry and control records')
    ck([r['stage'] for r in records]==list(range(29)),'control records ordered S0..S28')
    byid={r['stage']:r for r in records}
    children={n:[] for n in range(29)}
    for s in reg:
        for dep in s['depends_on']:children[dep].append(s['stage'])
    for s in reg:
        n=s['stage'];x=byid.get(n)
        ck(x is not None,f'S{n} control exists')
        if x is None:continue
        ck(x['owner']==s['track'],f'S{n} owner matches Registry')
        ck(x['release']==s['release'],f'S{n} release matches Registry')
        ck(x['depends_on']==s['depends_on'],f'S{n} technical deps identical')
        ck(x['downstream']==children[n],f'S{n} complete actual direct downstream')
        ck(x['acceptance_ids']==s['acceptance_ids'],f'S{n} no missing/re-numbered ATs')
        ck(x['stage_filename']==f'STAGE_{n:02d}.md',f'S{n} file path stable')
        for key in REQUIRED:
            value=x.get(key)
            ck(value is not None and bool(value),f'S{n} {key} nonempty')
            if isinstance(value,list):
                ck(all(isinstance(v,str) and len(v.strip())>=14 for v in value),f'S{n} {key} substantive statements')
                ck(len(set(value))==len(value),f'S{n} {key} no duplicate points')
        ck(len(x.get('gates',[]))>=3,f'S{n} >=3 concrete release gates')
        ck(len(x.get('watch',[]))>=2,f'S{n} >=2 risks')
        ck(len(x.get('prior',[]))>=2,f'S{n} >=2 backward-collision conditions')
        ck(len(x.get('future',[]))>=2,f'S{n} >=2 future/forward conditions')
        ck(len(x.get('open',[]))>=1,f'S{n} >=1 explicitly deferred choice')
        ck(isinstance(x['goal'],str) and len(x['goal'])>=28,f'S{n} clear goal')
        ck(isinstance(x['demo'],str) and len(x['demo'])>=28,f'S{n} demonstrable outcome')
        refs=[]
        for key in ('gates','watch','prior','future','open'):
            for part in x.get(key,[]):
                refs.extend(int(t) for t in re.findall(r'\bS(\d+)\b',part))
        ck(all(0<=z<=28 for z in refs),f'S{n} stage references within 0..28')
        fut=[int(t) for line in x.get('future',[]) for t in re.findall(r'\bS(\d+)\b',line)]
        ck(n==28 or any(t>n for t in fut),f'S{n} explicit later Stage or last stage')
        ck((n==0 and x['owner']=='P') or (n>0 and x['owner'] in 'ABIU'),f'S{n} exactly one runtime Owner')
        if check_files:
            p=root/'docs/stages'/f'STAGE_{n:02d}.md'
            ck(p.is_file(),f'S{n} spec file exists')
            if not p.is_file():continue
            text=p.read_text(encoding='utf8')
            for heading in HEADINGS:ck(text.count(heading)==1,f'S{n} unique card section {heading}')
            ck(text.index(HEADINGS[0])<text.index('## User-visible product deliverable'),f'S{n} Stage gates ahead of implementation details')
            for key in ('goal','demo'):
                ck(x[key] in text,f'S{n} {key} shown in spec')
            for key in ('gates','watch','prior','future','open'):
                for point in x[key]:ck(point in text,f'S{n} {key} point preserved in spec')
            ck(n==0 or '未經 Provider/Consumer 真實測試前均屬暫定' in text,f'S{n} technical draft warning')
            for aid in x['acceptance_ids']:
                ck(re.search(r'^\| '+re.escape(aid)+r' \|',text,re.M) is not None,f'S{n} AT {aid} still exists')
    if check_files:
        for p in ('docs/product/STAGE_BOUNDARY_MATRIX.md','docs/delivery/STAGE_DECISION_POLICY.md'):
            ck((root/p).is_file(),f'cross-stage policy document {p}')
        m=(root/'docs/product/STAGE_BOUNDARY_MATRIX.md').read_text(encoding='utf8')
        ck(len(re.findall(r'^\| \[\d{2} [PABIU]\]',m,re.M))==29,'29 matrix Stage rows')
        policy=(root/'docs/delivery/STAGE_DECISION_POLICY.md').read_text(encoding='utf8')
        for phrase in ('MUST','RELEASE GATE','REFERENCE/TBD','停工','跨 Owner'):
            ck(phrase in policy,f'policy has {phrase}')
        # Stage-specific checks of the highest-impact historic leakage points
        s1=(root/'docs/stages/STAGE_01.md').read_text(encoding='utf8')
        s4=(root/'docs/stages/STAGE_04.md').read_text(encoding='utf8')
        s5=(root/'docs/stages/STAGE_05.md').read_text(encoding='utf8')
        s17=(root/'docs/stages/STAGE_17.md').read_text(encoding='utf8')
        s25=(root/'docs/stages/STAGE_25.md').read_text(encoding='utf8')
        ck('S1 不依賴 B BYOK' in s1,'S1 independent of B Gemini')
        ck('S4 的核心對帳／恢復不能推遲' in s4,'S4 core not delayed to S28')
        ck('S5 Course/Materials' not in s5 or 'S21' in s5,'S5 cannot claim future analytics')
        ck('不可覆寫' in s17 and 'Expected Revision' in s17,'S17 ledger revision preserved')
        ck('未批准' in s25 and 'Fail Closed' in s25,'S25 real PII explicitly gated')
    return passed,errs

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    args=parser.parse_args()
    count,errors=inspect(args.root)
    print(json.dumps({'result':'PASS' if not errors else 'FAIL','stage_count':29,'checks_passed':count,'checks_failed':len(errors),'failures':errors[:80],'scope':'STAGE PLAN/COLLISION QA ONLY; NOT DEPLOYED TESTS'},ensure_ascii=False,indent=2))
    sys.exit(bool(errors))
