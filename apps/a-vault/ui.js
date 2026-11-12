'use strict';
let csrf='', currentShell=null;
const $=id=>document.getElementById(id);
const status=message=>{$('status').textContent=message;};
async function request(path,options={}){
 const opts={credentials:'same-origin',...options};
 if(opts.method && opts.method!=='GET')opts.headers={'X-CSRF-Token':csrf,...(opts.headers||{})};
 const res=await fetch(path,opts);const type=res.headers.get('Content-Type')||'';
 if(!res.ok){let d=type.includes('json')?await res.json():{};throw Error((d.detail||res.statusText)+' ('+res.status+')');}
 return type.includes('json')?res.json():res;
}
async function reload(){const data=await request('/vault/v1/shells');const parent=$('shells');parent.replaceChildren();
 for(const s of data.shells){const button=document.createElement('button');button.textContent=[s.academic_year,s.grade,s.subject,s.curriculum_stream,s.archived?'(archived)':''].join(' ');
 button.addEventListener('click',()=>openShell(s));parent.appendChild(button);}}
async function openShell(s){currentShell=s;$('detail').hidden=false;$('heading').textContent=s.subject+' / '+s.grade+' / '+s.curriculum_stream;
 $('upload').hidden=!!s.archived;$('archive').disabled=!!s.archived;await loadMaterials();}
async function loadMaterials(){const data=await request(`/vault/v1/shells/${currentShell.shell_id}/materials`);const parent=$('materials');parent.replaceChildren();
 for(const m of data.materials){const b=document.createElement('button');b.textContent='Download '+m.title+' (SHA256 '+m.sha256.substring(0,12)+'…)';b.onclick=async()=>{
 try{const res=await request(`/vault/v1/shells/${currentShell.shell_id}/materials/${encodeURIComponent(m.source_id)}/download`);
 const blob=await res.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=m.original_name;a.click();URL.revokeObjectURL(url)}catch(e){status(e.message)}};parent.appendChild(b);}}
$('create').addEventListener('submit',async e=>{e.preventDefault();try{const data=Object.fromEntries(new FormData(e.target));
 const shell=await request('/vault/v1/shells',{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},body:JSON.stringify(data)});
 status('Shell created: '+shell.shell_id);await reload();await openShell(shell)}catch(e){status(e.message)}});
$('upload').addEventListener('submit',async e=>{e.preventDefault();try{const f=new FormData(e.target);const data=await request(`/vault/v1/shells/${currentShell.shell_id}/materials`,{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},body:f});status('Native processing submitted: '+data.source_id);await loadMaterials()}catch(e){status(e.message)}});
$('search').addEventListener('submit',async e=>{e.preventDefault();try{const q=new FormData(e.target).get('query');
 const data=await request(`/vault/v1/shells/${currentShell.shell_id}/search`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});
 $('search-results').textContent=JSON.stringify(data.results)}catch(e){status(e.message)}});
$('archive').addEventListener('click',async()=>{try{await request(`/vault/v1/shells/${currentShell.shell_id}/archive`,{method:'POST'});status('Archived');await reload();await openShell({...currentShell,archived:1})}catch(e){status(e.message)}});
$('logout').addEventListener('click',async()=>{try{await request('/auth/logout',{method:'POST'});location.href='/auth/login'}catch(e){status(e.message)}});
(async()=>{try{const me=await request('/auth/me');csrf=me.csrf_token;await reload();status('Logged in to server-held school '+me.school_id)}catch(e){location.href='/auth/login'}})();
