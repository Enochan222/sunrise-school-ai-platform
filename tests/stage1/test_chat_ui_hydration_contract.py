"""Static UI hydration contract; full Firefox race is a separate Mac gate."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
UI=ROOT/'apps/a-vault/ui.js'
HTML=ROOT/'apps/a-vault/templates/admin.html'
BROWSER=ROOT/'scripts/stage1/browser_admin_journey.py'

class Buttons(HTMLParser):
    def __init__(self):
        super().__init__()
        self.buttons={}
    def handle_starttag(self,tag,attrs):
        if tag=='button':
            p=dict(attrs)
            if p.get('id'):self.buttons[p['id']]=p

def test_server_rendered_create_disabled_before_script():
    tags=Buttons()
    tags.feed(HTML.read_text(encoding='utf-8'))
    assert tags.buttons['create-submit']['type']=='submit'
    assert 'disabled' in tags.buttons['create-submit']

def test_ui_writes_disabled_until_session_hydration():
    js=UI.read_text(encoding='utf-8')
    assert 'const blocked = !state.session || state.sessionBusy || state.writing || Boolean(state.mutation);' in js
    assert "$('create-submit').disabled = blocked;" in js
    assert 'if (!canWrite()) return;' in js
    assert 'state.sessionBusy = false;' in js

def test_invalid_school_does_not_publish_a_mutable_session():
    js=UI.read_text(encoding='utf-8')
    assert js.index('!session.available_schools.includes(session.school_id)') < js.index('state.session = session;')
    assert 'clearPrivate();\n      if (error.status !== 401)' in js

def test_actual_browser_waits_for_enabled_create():
    s=BROWSER.read_text(encoding='utf-8')
    assert "document.querySelector('#create-submit')" in s
    assert '!el.disabled' in s
    assert s.index('!el.disabled') < s.index("page.locator('#create-submit').click()")

def test_admin_javascript_is_syntactically_valid_when_node_available():
    if shutil.which('node'):
        subprocess.run(['node','--check',str(UI)],check=True,timeout=15)
