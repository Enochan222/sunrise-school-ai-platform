"""Login synchronization regression; synthetic transport, not live acceptance."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))


def load():
    spec=importlib.util.spec_from_file_location('login_sync',ROOT/'scripts/stage1/browser_admin_journey.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('status,content_type,payload,valid',[
    (200,'application/json; charset=utf-8',{'authenticated':True},True),
    (200,'text/html',{'authenticated':True},False),
    (200,'application/json',{'authenticated':False},False),
    (200,'application/json',{'authenticated':1},False),
    (200,'application/json',[],False),
    (200,'application/json',ValueError('malformed JSON'),False),
    (303,'application/json',{'authenticated':True},False),
    (401,'application/json',{'authenticated':True},False),
])
def test_real_response_buffered_before_click_navigation_without_replay(status,content_type,payload,valid):
    mod=load();order=[];report={};handlers={}
    class Response:
        headers={'content-type':content_type,'set-cookie':'synthetic-cookie'}
        def json(self):
            assert 'navigated' not in order
            order.append('json')
            if isinstance(payload,Exception):raise payload
            return payload
    response=Response();response.status=status
    class Route:
        request=SimpleNamespace(method='POST')
        def fetch(self,**kwargs):
            assert kwargs=={'max_redirects':0,'timeout':30000}
            order.append('fetch');return response
        def fulfill(self,**kwargs):
            assert kwargs=={'response':response}  # exact body, headers, cookies
            assert 'json' in order
            order.append('fulfill')
    class Receipt:
        # Browser response body deliberately unreadable after navigation.
        value=SimpleNamespace(url='https://127.0.0.1:9876/auth/login',status=status)
        def __enter__(self):return self
        def __exit__(self,*args):pass
    class Page:
        def route(self,url,handler):handlers[url]=handler
        def unroute(self,url,handler):
            assert handlers.pop(url)==handler
            order.append('unroute')
        def expect_response(self,predicate,**kwargs):
            assert predicate(SimpleNamespace(url='https://127.0.0.1:9876/auth/login',request=Route.request))
            assert not predicate(SimpleNamespace(url='https://evil.invalid/auth/login',request=Route.request))
            return Receipt()
        def locator(self,selector):
            assert selector=='#login button[type=submit]';return self
        def click(self):
            handlers['https://127.0.0.1:9876/auth/login'](Route())
            order.append('navigated')
    events=SimpleNamespace(http=lambda *args:order.append('http'))
    if valid:
        mod.submit_json_login(Page(),'https://127.0.0.1:9876',events,report)
        assert report=={}
    else:
        with pytest.raises(mod.BrowserContractError,match='JSON login contract mismatch'):
            mod.submit_json_login(Page(),'https://127.0.0.1:9876',events,report)
        assert report['error_category']=='LOGIN_JSON_CONTRACT_MISMATCH'
    assert order==['fetch','json','fulfill','navigated','http','unroute']
    assert not handlers
