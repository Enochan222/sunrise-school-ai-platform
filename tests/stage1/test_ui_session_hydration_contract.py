"""Source-contract regression for the Admin session-hydration race.

These tests do not constitute an executed Firefox/HTTPS acceptance test. They
ensure the visible Admin create control cannot become actionable while the
client intentionally refuses writes during async session/list initialization.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "apps/a-vault/ui.js"


def _section(source: str, begin: str, end: str) -> str:
    assert source.count(begin) == 1, f"Ambiguous source contract anchor: {begin}"
    return source.split(begin, 1)[1].split(end, 1)[0]


def test_admin_create_disabled_until_session_hydration_finishes():
    source = UI.read_text(encoding="utf-8")
    controls = _section(source, "  function syncControls() {", "\n  function renderList() {")
    assert (
        "const blocked = !state.session || state.sessionBusy || "
        "state.writing || Boolean(state.mutation);"
    ) in controls
    assert "$('create-submit').disabled = blocked;" in controls
    assert "$('upload-submit').disabled = blocked || !state.shell" in controls
    assert "$('switch-school-submit').disabled = blocked || state.sessionBusy;" in controls
    assert "$('search-submit').disabled = state.sessionBusy || " in controls


def test_session_request_locks_actions_before_await_and_unblocks_in_finally():
    source = UI.read_text(encoding="utf-8")
    check = _section(source, "  async function checkSession() {", "\n  $('switch-school').addEventListener")
    before_network = check.split("const session = await api.session();", 1)[0]
    assert "state.sessionBusy = true;" in before_network
    assert "syncControls();" in before_network
    assert "state.session = session;" in check
    assert "await refreshShells();" in check
    assert "state.sessionBusy = false;" in check
    assert check.index("state.sessionBusy = false;") > check.index("await refreshShells();")
    assert "state.sessionBusy = false;\n      $('retry-session').disabled = false;\n      syncControls();" in check


def test_create_handler_and_dispatch_keep_the_same_fail_closed_guard():
    source = UI.read_text(encoding="utf-8")
    guard = _section(source, "  function canWrite() {", "\n  async function sendMutation")
    assert "state.session && !state.sessionBusy && !state.writing && !state.mutation" in guard
    create = _section(
        source, "  $('create').addEventListener('submit', (event) => {",
        "\n  $('upload').addEventListener",
    )
    assert "if (!canWrite()) return;" in create
    assert "key: makeKey()" in create
    dispatch = _section(source, "  async function sendMutation(operation, reconcile = false) {", "\n  $('create').addEventListener")
    assert "state.sessionBusy || state.writing || state.mutation !== operation" in dispatch
