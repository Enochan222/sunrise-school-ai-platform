"""Firefox strict TLS NSS profile regression. NO live browser/Gateway acceptance."""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/'scripts/stage1/browser_admin_journey.py'
sys.path.insert(0,str(ROOT/'scripts/stage1'))


def load():
    spec=importlib.util.spec_from_file_location('stage1_firefox_browser_journey',MODULE)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize('engine',('chromium','firefox'))
def test_browser_engine_explicit_cli_and_preflight_fails_without_network(tmp_path,monkeypatch,engine):
    mod=load()
    outfile=tmp_path/'preflight.json'
    argv=['browser_admin_journey.py','--browser-engine',engine,
          '--gateway','http://127.0.0.1:8765','--gateway-ca-file',
          str(tmp_path/'missing.pem'),'--runtime-identity',str(tmp_path/'missing.json'),
          '--context','desktop-linux','--project','sunrise-s1-test-only',
          '--source-sha','a'*40,'--source-tree','b'*40,'--out',str(outfile)]
    monkeypatch.setattr(sys,'argv',argv)
    with pytest.raises(SystemExit) as stop:
        mod.main()
    assert stop.value.code==1
    report=json.loads(outfile.read_text())
    assert report['status']=='FAIL'
    assert report['browser_engine']==engine
    assert report['browser_version'] is None
    assert report['failure_stage']=='S1B-STARTUP'
    assert report['error_category']
    assert not any(name in outfile.read_text() for name in ('cookie','password','private-key'))


@pytest.mark.parametrize('case',('ok','no-certutil','bad-nss-trust','wrong-version','wrong-playwright'))
def test_private_nss_firefox_strict_launch_provenance_and_cleanup(tmp_path,monkeypatch,case):
    mod=load()
    ca=tmp_path/'synthetic-ca.pem'
    ca.write_text('synthetic CA data (not a real certificate)')
    executable=tmp_path/'firefox'
    executable.write_bytes(b'firefox executable fixture')
    calls=[]
    seen={}
    class Context:
        closed=False
        browser=SimpleNamespace(version='158.0' if case=='wrong-version' else '159.0')
        def close(self):
            self.closed=True
    context=Context()
    class BrowserType:
        executable_path=str(executable)
        def launch_persistent_context(self,**kwargs):
            seen.update(kwargs)
            return context
    pw=SimpleNamespace(firefox=BrowserType())
    def nss_command(args,**kwargs):
        calls.append(tuple(args))
        if args[1]=='-L':
            listing='Sunrise-Synthetic-Gateway-CA  u,u,u\n' if case=='bad-nss-trust' else (
                'Certificate Nickname   Trust Attributes\n'
                'Sunrise-Synthetic-Gateway-CA  C,,\n')
            return SimpleNamespace(returncode=0,stdout=listing)
        return SimpleNamespace(returncode=0,stdout='')
    monkeypatch.setattr(mod.shutil,'which',lambda _:None if case=='no-certutil' else '/bin/sh')
    monkeypatch.setattr(mod.subprocess,'run',nss_command)
    report={'playwright_package_version':'1.64.0' if case=='wrong-playwright' else '1.65.1'}
    with ExitStack() as stack:
        if case=='ok':
            result,profile=mod.firefox_context(pw,ca,stack,report)
            assert result is context
            assert seen['headless'] is True
            assert seen['ignore_https_errors'] is False
            assert seen['accept_downloads'] is True
            assert seen['firefox_user_prefs']['security.enterprise_roots.enabled'] is False
            assert Path(seen['user_data_dir'])==profile/'profile'
            assert Path(seen['user_data_dir']).is_dir()
            assert profile.is_dir()
            assert report['firefox_version']=='159.0'
            assert report['browser_version']=='159.0'
            assert report['firefox_nss_ca_trust']=='C,,'
            assert report['firefox_nss_profile']=='ISOLATED_PERSISTENT'
            assert 'synthetic-ca.pem' not in str(report)
            assert any('-N' in args and '--empty-password' in args for args in calls)
            assert any('-A' in args and 'C,,' in args for args in calls)
            assert any('-L' in args for args in calls)
        else:
            with pytest.raises(mod.BrowserContractError):
                mod.firefox_context(pw,ca,stack,report)
    assert context.closed is (case in ('ok','wrong-version'))
    if 'user_data_dir' in seen:
        assert not Path(seen['user_data_dir']).exists()
