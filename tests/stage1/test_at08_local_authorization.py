"""AT08 local startup authorization must not fabricate external observation."""
import importlib.util
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))


@pytest.mark.parametrize('at,synthetic,observer,allowed',[
    ('S1-AT08','YES',None,True),
    ('S1-AT08',None,None,False),
    ('S1-AT02','YES',None,False),
    ('S1-AT07','YES',None,False),
    ('S1-AT09','YES',None,False),
    ('S1-AT02','YES','YES',True),
    ('S1-AT08',None,'YES',False),
])
def test_case_specific_authorization(at,synthetic,observer,allowed,monkeypatch,tmp_path):
    spec=importlib.util.spec_from_file_location('security_local_gate',ROOT/'scripts/stage1/acceptance/security_at.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for name,value in [('VAULT_RUNTIME_SYNTHETIC_CONFIRM',synthetic),('VAULT_OBSERVER_ISOLATED_CONFIRM',observer)]:
        if value is None:monkeypatch.delenv(name,raising=False)
        else:monkeypatch.setenv(name,value)
    argv=['security_at.py','--at-id',at,'--gateway','https://127.0.0.1:9876','--gateway-ca-file',str(tmp_path/'ca')]
    for key,value in {'runtime-identity':str(tmp_path/'identity'),'context':'desktop-linux','project':'sunrise-s1-local-test','source-sha':'a'*40,'source-tree':'b'*40,'target-private-ip':'192.168.1.2','out':str(tmp_path/'out')}.items():argv+=['--'+key,value]
    monkeypatch.setattr(sys,'argv',argv)
    class ReachedSourceValidation(Exception):pass
    def source_guard(*args,**kwargs):raise ReachedSourceValidation
    monkeypatch.setattr(mod,'verify_clean_source',source_guard)
    if allowed:
        # Only authorization reached; never infer runtime/observer PASS.
        with pytest.raises(ReachedSourceValidation):mod.main()
    else:
        with pytest.raises(SystemExit) as stop:mod.main()
        assert stop.value.code==2
    assert not (tmp_path/'out').exists()
