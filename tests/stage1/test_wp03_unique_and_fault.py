"""WP03 index drift and real loopback TCP ACK-suppression component checks.

These DO NOT substitute for SurrealDB v2.3.10 / pinned Open Notebook runtime.
"""
import asyncio
from copy import deepcopy
import pathlib
import sys

import pytest

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/a-vault'))
sys.path.insert(0,str(ROOT/'scripts/stage1'))
from surreal_store import (EXPECTED_INDEXES, SCHEMA, SurrealStore, SurrealUnavailable,
                          verify_unique_index_definitions)
from native_ack_loss_probe import create_and_drop_ack


def definitions(as_dict=False):
    result={}
    for table, indexes in EXPECTED_INDEXES.items():
        result[table]={}
        for name,fields in indexes.items():
            sql=f'DEFINE INDEX {name} ON {table} FIELDS '+', '.join(fields)+' UNIQUE'
            result[table][name]={'sql':sql} if as_dict else sql
    return result


@pytest.mark.parametrize('as_dict',[True,False])
def test_exact_index_definitions_accept_v2_info_representations(as_dict):
    for table, indexes in definitions(as_dict).items():
        verify_unique_index_definitions(table,indexes)


def test_wrong_unique_index_definition_fails_start_even_correct_name():
    specs=definitions()
    altered=[]
    original=specs['content_shell']['shell_scope_unique']
    altered.append(original.replace('school_id, academic_year','academic_year, school_id'))
    altered.append(original.replace('grade, subject','grade, wrong_field'))
    altered.append(original.replace('ON content_shell','ON source_owner'))
    altered.append(original.replace('DEFINE INDEX shell_scope_unique','DEFINE INDEX malicious_unique'))
    altered.append(original.replace(' UNIQUE',''))
    altered.append(original+' COMMENT "UNIQUE"')
    altered.append(original+' UNIQUE')
    for wrong in altered:
        obj=deepcopy(specs['content_shell'])
        obj['shell_scope_unique']=wrong
        with pytest.raises(SurrealUnavailable):
            verify_unique_index_definitions('content_shell',obj)
    for obj in (None,{},'not-a-dict',{'shell_scope_unique':original},
                {**specs['content_shell'],'injected_index':'DEFINE INDEX injected_index ON content_shell FIELDS x UNIQUE'}):
        with pytest.raises(SurrealUnavailable):
            verify_unique_index_definitions('content_shell',obj)


def test_migration_executes_info_check_and_fails_if_index_mispointed():
    class FakeRPC:
        def __init__(self, definitions):
            self.definitions=definitions
            self.statements=[]
        def query(self,statement,variables=None):
            self.statements.append(statement)
            if statement==SCHEMA:return [None]
            table=statement.removeprefix('INFO FOR TABLE ').removesuffix(';')
            return [{'indexes':self.definitions[table]}]
    store=SurrealStore.__new__(SurrealStore)
    store.rpc=FakeRPC(definitions(as_dict=True))
    store.migrate()
    assert len(store.rpc.statements)==len(EXPECTED_INDEXES)+1
    bad=definitions(as_dict=True)
    bad['vault_operation']['op_key_unique']['sql']=bad['vault_operation']['op_key_unique']['sql'].replace(
        'school_id, actor_id','actor_id, school_id')
    store.rpc=FakeRPC(bad)
    with pytest.raises(SurrealUnavailable,match='vault_operation.op_key_unique'):
        store.migrate()


def test_fresh_concurrency_runtime_harness_has_three_independent_race_modes():
    source=(ROOT/'scripts/stage1/wp03_races.py').read_text()
    assert 'threading.Barrier(workers)' in source
    assert 'with ThreadPoolExecutor(max_workers=workers)' in source
    assert 'same_key_same_body' in source
    assert 'different_key_same_scope' in source
    assert 'same_key_different_body' in source
    assert "(len(operations),len(claims),len(shells))!=(1,1,0)" in source
    assert 'def native_lost_ack(' in source
    runner=(ROOT/'scripts/stage1/surreal_journal_smoke.py').read_text()
    assert 'first_reservation_races(configuration,actor,secret or None)' in runner
    assert 'native_lost_ack(configuration,actor' in runner
    assert "real_native_crash_after_create_before_journal_commit" in runner


def test_actual_tcp_downstream_lost_ack_component_without_native_runtime():
    # An actual loopback TCP service receives the forwarded POST, returns a valid
    # native-style receipt, and the proxy deliberately discards its response.
    # This tests fault injection mechanics, NOT pinned native durability.
    async def run():
        seen=[]
        async def fake_native(reader,writer):
            try:
                head=await reader.readuntil(b'\r\n\r\n')
                length=next(int(x.split(b':',1)[1]) for x in head.split(b'\r\n')
                    if x.lower().startswith(b'content-length:'))
                body=await reader.readexactly(length)
                seen.append(body)
                reply=b'{"id":"notebook:real_tcp_component"}'
                writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n'
                             +f'Content-Length: {len(reply)}\r\nConnection: close\r\n\r\n'.encode()+reply)
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
        server=await asyncio.start_server(fake_native,'127.0.0.1',0)
        try:
            port=server.sockets[0].getsockname()[1]
            status=await create_and_drop_ack('synthetic-secret-only-2026',
                'sunrise-a-op-v1:'+'a'*64,f'http://127.0.0.1:{port}')
            assert status=={'forwarded':1,'upstream_ack':True,'downstream_ack_sent':False}
            assert len(seen)==1 and b'sunrise-a-op-v1:' in seen[0]
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())
