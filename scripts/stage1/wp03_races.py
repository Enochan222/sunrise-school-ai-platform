"""Real A SurrealDB FIRST-reservation competition and real native HTTP lost ACK.

Called only by the explicitly gated native journal smoke on a disposable host.
"""
from __future__ import annotations
import asyncio
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import secrets
import threading

from surreal_store import SurrealStore,_digest
from store import Conflict,Indeterminate
from native import Native
from native_ack_loss_probe import create_and_drop_ack


def first_reservation_races(configuration,actor,secret,native_endpoint,workers=8):
    evidence={}
    for mode in ('same_key_same_body','different_key_same_scope','same_key_different_body'):
        school='synthetic-first-race-'+secrets.token_hex(8)
        details={'academic_year':'2026','grade':'P4','subject':'Mathematics',
                 'curriculum_stream':'synthetic'}
        # All connections are independently instantiated BEFORE the first claim.
        stores=[SurrealStore(configuration,actor) for _ in range(workers)]
        gate=threading.Barrier(workers)
        def compete(i):
            key='race_'+mode+(str(i) if mode=='different_key_same_scope' else '')
            body={**details,'grade':'P5' if mode=='same_key_different_body' and i%2 else 'P4'}
            gate.wait(timeout=30)
            try:
                record,fresh=stores[i].start_shell(school,key,body)
                return ('FRESH' if fresh else 'REPLAY',key,body,record['shell_id'])
            except Conflict:
                return ('CONFLICT',key,body,None)
            except Indeterminate:
                return ('INDETERMINATE',key,body,None)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            outcomes=list(pool.map(compete,range(workers)))
        verdicts=Counter(row[0] for row in outcomes)
        if (verdicts['FRESH']!=1 or verdicts['REPLAY'] or
                sum(verdicts.values())!=workers):
            raise AssertionError('Fresh concurrent reservation violated: '+str(dict(verdicts)))
        journal=SurrealStore(configuration,actor)
        operations=journal.query('SELECT * FROM vault_operation WHERE school_id=$school;',school=school)[-1]
        claims=journal.query('SELECT * FROM vault_scope_claim WHERE school_id=$school;',school=school)[-1]
        shells=journal.query('SELECT * FROM content_shell WHERE school_id=$school;',school=school)[-1]
        if (len(operations),len(claims),len(shells))!=(1,1,0):
            raise AssertionError('Duplicate or partial first claim/transaction commit')
        winner=next(row for row in outcomes if row[0]=='FRESH')
        persisted=journal.operation(school,winner[1],'shell')
        if persisted['shell_id']!=winner[3] or persisted['payload_sha']!=_digest(winner[2]):
            raise AssertionError('First-claim winner does not match durable journal')
        verified_native_posts=0
        mapped_shells=0
        if secret:
            # Only the one durable FIRST claimant is permitted to create upstream.
            marker=persisted['marker']
            native=Native(native_endpoint,secret)
            async def create_once():
                notebook=await native.create_notebook('SYNTHETIC FIRST CLAIM '+mode,marker=marker)
                identities=await native.find_notebooks_by_marker(marker)
                if identities!=[notebook]:
                    raise AssertionError('Native marker is not exclusively linked to first claim')
                return notebook
            notebook=asyncio.run(create_once())
            confirmed=journal.complete_shell(school,winner[1],
                {'shell_id':persisted['shell_id'],'school_id':school,**winner[2]},notebook)
            if confirmed['notebook_id']!=notebook:
                raise AssertionError('First claimant Notebook mapping corrupt')
            mapped_shells=1
            verified_native_posts=1
            # Retry the originally disputed operations after creation; no request
            # may become a fresh claimant or generate a second native side effect.
            for status,key,body,_ in outcomes:
                if status=='FRESH':continue
                try:
                    replay,created=journal.start_shell(school,key,body)
                    if created or replay['notebook_id']!=notebook:
                        raise AssertionError('Another native claim was granted after commit')
                except Conflict:
                    continue
        evidence[mode]={'outcomes':dict(verdicts),'durable_operations':1,'durable_scope_claims':1,
                        'durable_shells':mapped_shells,'native_create_posts':verified_native_posts}
    return evidence


def native_lost_ack(configuration,actor,secret,native_endpoint):
    """Distinct downstream TCP ACK suppression after a real native create commit."""
    school='synthetic-lost-ack-'+secrets.token_hex(8)
    key='lost_ack_'+secrets.token_hex(8)
    payload={'academic_year':'2026','grade':'P4','subject':'Mathematics',
             'curriculum_stream':'ack-loss-only'}
    journal=SurrealStore(configuration,actor)
    claim,fresh=journal.start_shell(school,key,payload)
    if not fresh:raise AssertionError('Lost-ACK probe did not reserve a fresh operation')
    receipt=asyncio.run(create_and_drop_ack(secret,claim['creation_marker'],native_endpoint))
    if receipt['forwarded']!=1 or not receipt['upstream_ack'] or receipt['downstream_ack_sent']:
        raise AssertionError('Lost-ACK TCP fault not proven')
    # Fresh independent DB/Native connections; never POST another notebook.
    resumed=SurrealStore(configuration,actor)
    op=resumed.operation(school,key,'shell')
    if not op or op['status']!='PENDING':raise AssertionError('Missing pre-ACK journal')
    native=Native(native_endpoint,secret)
    matches=asyncio.run(native.find_notebooks_by_marker(op['marker']))
    if len(matches)!=1:raise AssertionError('Unknown/duplicate native marker after lost ACK')
    committed=resumed.complete_shell(school,key,
        {'shell_id':op['shell_id'],'school_id':school,**payload},matches[0])
    replay,first=resumed.start_shell(school,key,payload)
    if first or replay['notebook_id']!=committed['notebook_id']:
        raise AssertionError('Same-key replay duplicated native notebook')
    try:resumed.start_shell(school,key,{**payload,'grade':'P5'})
    except Conflict:pass
    else:raise AssertionError('Different payload failed to conflict after ACK loss')
    if resumed.shell('synthetic-foreign-school',op['shell_id']) is not None:
        raise AssertionError('Cross-school shell lookup leaked')
    return {'native_create_posts':1,'client_received_post_ack':False,
            'persisted_mapping_count':1,'original_notebook_sha256':hashlib.sha256(matches[0].encode()).hexdigest()}
