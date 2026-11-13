"""Run independent per-engine DB inventory through two separate private networks.

No A root credentials are ever passed into the ON graph worker or vice versa.
Only disposable native-image Python verifier processes; no public ports.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess

ROLES={'a':('a_db_private','a_db'),'on':('on_db_private','on_db')}


def both(context,project,image):
    if not re.fullmatch(r'sunrise-s1-(?:restore-)?[a-z0-9-]{8,45}',project):
        raise RuntimeError('Wrong project for dual-engine inventory')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):
        raise RuntimeError('Immutable verifier image unavailable')
    code=(Path(__file__).parent/'db_inventory.py').read_text(encoding='utf-8')
    evidence={}
    for role,(network_service,dns) in ROLES.items():
        required=(('A_SURREAL_USER','A_SURREAL_PASSWORD','A_SURREAL_NAMESPACE',
                   'A_SURREAL_DATABASE') if role=='a'
                  else ('ON_SURREAL_USER','ON_SURREAL_PASSWORD','ON_GRAPH_NAMESPACE',
                        'ON_GRAPH_DATABASE'))
        if any(not os.environ.get(k) for k in required):
            raise RuntimeError('Independent physical DB credentials missing')
        command=['docker','--context',context,'run','--rm','--network',
                 project+'_'+network_service,'--read-only','--cap-drop','ALL',
                 '--security-opt','no-new-privileges','--pids-limit','64',
                 '-e','VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES',
                 '-e','SURREAL_URL=ws://'+dns+':8000/rpc']
        for name in required:
            # Docker CLI -e NAME inherits the local private value. Do NOT
            # serialize credentials into command arguments, logs or evidence.
            command.extend(['-e',name])
        command.extend(['--entrypoint','/app/.venv/bin/python',
                        image,'-c',code,'--role',role])
        result=subprocess.run(command,capture_output=True,text=True,timeout=120)
        if result.returncode!=0:
            raise RuntimeError('Physical '+role+' DB readback failed; do not trust aggregate')
        payload=json.loads(result.stdout)
        if (payload.get('classification')!='PHYSICAL_DB_INVENTORY_ONLY_NOT_ACCEPTANCE'
                or payload.get('physical_db',{}).get('role')!=role):
            raise RuntimeError('Unexpected/foreign physical DB inventory')
        evidence['a_journal' if role=='a' else 'native']=payload['physical_db']
    return {'classification':'DUAL_PHYSICAL_DB_INVENTORIES_ONLY_NOT_AT_PASS',
            'a_journal':evidence['a_journal'],'native':evidence['native'],
            'distinct_engines':True,'distinct_private_networks':True}



def read_a_owner_snapshot(context,project,image):
    """Private, bounded A physical DB readback, raw data confined to host pipe."""
    if not re.fullmatch(r'sunrise-s1-(?:restore-)?[a-z0-9-]{8,45}',project):
        raise RuntimeError('Foreign private A snapshot project')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):
        raise RuntimeError('Source snapshot verifier image not immutable')
    require=('A_SURREAL_USER','A_SURREAL_PASSWORD','A_SURREAL_NAMESPACE',
             'A_SURREAL_DATABASE')
    if any(not os.environ.get(k) for k in require):
        raise RuntimeError('A root auth context unavailable')
    code=(Path(__file__).parent/'a_owner_snapshot.py').read_text(encoding='utf-8')
    cmd=['docker','--context',context,'run','--rm','--network',
         project+'_a_db_private','--read-only','--cap-drop','ALL',
         '--security-opt','no-new-privileges','--pids-limit','64',
         '-e','VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES',
         '-e','SURREAL_URL=ws://a_db:8000/rpc']
    for name in require:
        cmd.extend(['-e',name])
    cmd.extend(['--entrypoint','/app/.venv/bin/python',image,'-c',code])
    proc=subprocess.run(cmd,text=True,capture_output=True,timeout=120)
    if proc.returncode!=0 or len(proc.stdout)>4<<20:
        raise RuntimeError('A physical SourceOwner readback failed or was oversized')
    result=json.loads(proc.stdout)
    if (result.get('classification')!='PRIVATE_A_OWNER_SNAPSHOT_NOT_ACCEPTANCE'
            or not isinstance(result.get('source_owner'),list)
            or not isinstance(result.get('content_shell'),list)):
        raise RuntimeError('A physical SourceOwner proof not trustworthy')
    return result


def native_readback(context,container_id,owner_snapshot,proof_script):
    """Pipe A snapshot into separately isolated ON container; no A credentials."""
    if not re.fullmatch(r'[a-f0-9]{64}',container_id):
        raise RuntimeError('Unattested Native container identity')
    payload=json.dumps(owner_snapshot,sort_keys=True,separators=(',',':'))
    if len(payload.encode('utf-8'))>4<<20:
        raise RuntimeError('A metadata input unbounded')
    cmd=['docker','--context',context,'exec','-i',
         '-e','VAULT_RUNTIME_SYNTHETIC_CONFIRM=YES',container_id,
         '/app/.venv/bin/python','-c',proof_script]
    attempt=subprocess.run(cmd,input=payload,capture_output=True,text=True,timeout=120)
    if attempt.returncode!=0:
        raise RuntimeError('Independent Native Graph/original verification failed')
    record=json.loads(attempt.stdout)
    if record.get('classification')!='NATIVE_OWNER_READBACK_NOT_FORMAL_AT':
        raise RuntimeError('Wrong ON readback classification')
    return record
