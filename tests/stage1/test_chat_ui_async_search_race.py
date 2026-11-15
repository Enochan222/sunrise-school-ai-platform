"""Behavioral Node DOM-shim regression for stale Search after session hydration.

This exercises the actual production UI source, not a fake Search function.
No network, browser profile, credentials or real Docker is used.
"""
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
UI=ROOT/'apps/a-vault/ui.js'

NODE=r"""
'use strict';
const fs=require('node:fs');
const assert=require('node:assert/strict');
let code=fs.readFileSync(process.argv[1],'utf8');
const anchor="  void checkSession();\n}\n\nif (document.body.dataset.page";
assert.equal(code.split(anchor).length,2,'UI test instrumentation anchor changed');
code=code.replace(anchor,
    "  globalThis.__sunrise_qa={state,clearPrivate,checkSession,search,syncControls};\n"+anchor);
const elements=new Map();
function node(id) {
  return {
    id,dataset:{},value:'',textContent:'',disabled:false,hidden:false,children:[],handlers:{},
    addEventListener(name,handler){this.handlers[name]=handler;},
    replaceChildren(...children){this.children=children;},
    append(...children){this.children.push(...children);},
    reset(){this.value='';},
    focus(){},
    setAttribute(){},
    classList:{add(){},remove(){}}
  };
}
const document={
  body:{dataset:{page:'admin'},append(){}},
  getElementById(id) {
    if (!elements.has(id)) elements.set(id,node(id));
    return elements.get(id);
  },
  createElement(tag){return node(tag)}
};
const window={
  addEventListener(){},setTimeout(){return 1;},
  location:{replace(){}},confirm(){return true}
};
class Headers{
  constructor(obj){this.values={...obj}}
  set(name,value){this.values[name]=value}
  get(name){return this.values[name]}
}
class AbortController{
  constructor(){this.signal={}}
  abort(){}
}
let searchCount=0, heldSearchResponse;
const ok=(body)=>({
  ok:true, headers:{get(){return 'application/json'}},
  json:async()=>body
});
async function fetch(path){
  if (path==='/auth/me') return ok({
    school_id:'synthetic-a',actor_id:'synthetic-admin',csrf_token:'synthetic-csrf',
    available_schools:['synthetic-a']
  });
  if (path==='/vault/v1/shells') return ok({shells:[]});
  if (path==='/vault/v1/shells/shell-a/search'){
    searchCount++;
    if (searchCount===1) return new Promise(resolve=>{heldSearchResponse=resolve});
    return ok({search_type:'text',results:[]});
  }
  throw Error('Unexpected synthetic fetch: '+path);
}
function flush(){return Promise.resolve()}
async function run(){
  new Function('document','window','fetch','Headers','AbortController','clearTimeout',code)
    (document,window,fetch,Headers,AbortController,()=>{});
  const hooks=globalThis.__sunrise_qa;
  for(let i=0;i<20;i++)await flush();
  assert.equal(hooks.state.session?.school_id,'synthetic-a');
  hooks.state.shell={shell_id:'shell-a',school_id:'synthetic-a',archived:false};
  hooks.syncControls();
  document.getElementById('query').value='old search';
  const old=hooks.search({preventDefault(){}});
  for(let i=0;i<8;i++)await flush();
  assert.equal(searchCount,1);
  assert.equal(hooks.state.searching,true);
  hooks.clearPrivate();
  assert.equal(hooks.state.searching,false,'Session clear retained stale Search flag');
  await hooks.checkSession();
  assert.equal(hooks.state.session?.school_id,'synthetic-a');
  hooks.state.shell={shell_id:'shell-a',school_id:'synthetic-a',archived:false};
  hooks.syncControls();
  assert.equal(document.getElementById('search-submit').disabled,false,
      'Search remained disabled after rehydration');
  heldSearchResponse(ok({search_type:'text',results:[{
    source_id:'source:stale',title:'Stale from revoked session'
  }]}));
  await old;
  assert.equal(document.getElementById('search-results').children.length,0,
      'Old session search populated current school UI');
  document.getElementById('query').value='fresh search';
  await hooks.search({preventDefault(){}});
  assert.equal(searchCount,2,'New authenticated Search request never sent');
  assert.equal(hooks.state.searching,false,'New Search never returned to idle');
  hooks.syncControls();
  assert.equal(document.getElementById('search-submit').disabled,false);
  process.stdout.write(JSON.stringify({cases:5,search_count:searchCount,
    stale_response_discarded:true,rehydrated:true})+'\n');
}
run().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1});
"""


def test_ui_search_reenabled_after_revoked_session_with_old_pending_result():
    node=shutil.which('node')
    assert node,'Node.js required for actual UI JS behavior regression'
    proc=subprocess.run([node,'-e',NODE,str(UI)],cwd=ROOT,
                        capture_output=True,text=True,timeout=25)
    assert proc.returncode==0,proc.stderr
    evidence=json.loads(proc.stdout)
    assert evidence['cases']==5 and evidence['search_count']==2
    assert evidence['rehydrated'] and evidence['stale_response_discarded']
