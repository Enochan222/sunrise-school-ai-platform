"""Real browser timing regression on a synthetic DOM, not Vault acceptance."""
import importlib.util
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1'))


@pytest.fixture
def browser_page():
    api=pytest.importorskip('playwright.sync_api')
    with api.sync_playwright() as pw:
        if not Path(pw.chromium.executable_path).is_file():
            pytest.skip('Playwright Chromium required for timing regression')
        browser=pw.chromium.launch(headless=True)
        try:yield browser.new_page()
        finally:browser.close()


def load():
    spec=importlib.util.spec_from_file_location('archive_browser_sync',ROOT/'scripts/stage1/browser_admin_journey.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def test_visible_archive_does_not_mean_material_refresh_completed(browser_page):
    page=browser_page
    page.set_content('''<p id="archive-note">Archived</p><ul id="materials"></ul>
        <button id="refresh-materials" disabled>Refresh</button>
        <script>window.refreshPending=true;
        setTimeout(()=>{document.querySelector('#materials').innerHTML='<li>Original</li>';},40);
        setTimeout(()=>{window.refreshPending=false;document.querySelector('#refresh-materials').disabled=false;},120);
        </script>''')
    assert page.locator('#archive-note').is_visible()
    assert page.evaluate('window.refreshPending') is True
    load().wait_for_archive_refresh(page,'Original',timeout=3000)
    # Both rendering AND the final in-flight state must complete before logout.
    assert page.evaluate('window.refreshPending') is False
    assert page.locator('#refresh-materials').is_enabled()


def test_material_visible_with_unfinished_refresh_cannot_pass(browser_page):
    api=pytest.importorskip('playwright.sync_api')
    browser_page.set_content('<ul id="materials"><li>Original</li></ul><button id="refresh-materials" disabled>Refresh</button>')
    with pytest.raises(api.TimeoutError):
        load().wait_for_archive_refresh(browser_page,'Original',timeout=120)
