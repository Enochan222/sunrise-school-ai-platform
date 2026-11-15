"""AT06 Native endpoint must match an independently re-inspected live relay.

These are isolated contract tests; they are NOT real Docker or lost-ACK tests.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/stage1"))
import executed_runtime_provenance as provenance


def _identity(tmp_path):
    services = {}
    for role, port in (("a_db", 46001), ("on_db", 46002), ("native", 46003)):
        services[role] = {
            "container_id": role + "-container",
            "network_id": role + "-network",
            "image_id": "sha256:" + "a" * 64,
            "persistent_volume": role + "-volume",
            "host_relay": {"port": port, "relay_id": role + "-relay"},
            "published_ports": [{"container_port": "5055/tcp" if role == "native" else "8000/tcp", "host_ip": "127.0.0.1", "host_port": port}],
        }
    doc = {"context": "desktop-linux", "project": "sunrise-s1-exclusive123",
           "services": services, "source_commit": "a" * 40, "source_tree": "b" * 40}
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return doc, path


def test_verified_dynamic_native_endpoint(monkeypatch, tmp_path):
    doc, path = _identity(tmp_path)
    monkeypatch.setattr(provenance, "inspect", lambda *a: "c" * 64)
    monkeypatch.setattr(provenance, "load_live_services", lambda context, project: doc["services"])
    assert provenance.resolve_native_endpoint(ROOT, path, "a" * 40, "b" * 40,
                                              "c" * 64) == "http://127.0.0.1:46003"


@pytest.mark.parametrize("tamper", [
    lambda doc: doc["services"]["native"]["published_ports"][0].update(host_port=5055),
    lambda doc: doc["services"]["native"]["host_relay"].update(relay_id="foreign-relay"),
    lambda doc: doc["services"]["native"].update(container_id="wrong-container"),
    lambda doc: doc["services"]["native"].update(network_id="wrong-network"),
    lambda doc: doc["services"]["on_db"].update(persistent_volume="wrong-volume"),
    lambda doc: doc["services"]["native"].update(image_id="sha256:"+"b"*64),
    lambda doc: doc.update(project="sunrise-s1-wrongproject"),
])
def test_wrong_endpoint_or_identity_fails_closed(monkeypatch, tmp_path, tamper):
    doc, path = _identity(tmp_path)
    original = json.loads(json.dumps(doc))
    tamper(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")
    if doc["project"] != original["project"]:
        live_project = original["project"]
    else:
        live_project = doc["project"]
    monkeypatch.setattr(provenance, "inspect", lambda *a: "c" * 64)
    def live(context, project):
        if project != live_project:
            raise RuntimeError("wrong project")
        return original["services"]
    monkeypatch.setattr(provenance, "load_live_services", live)
    with pytest.raises(RuntimeError):
        provenance.resolve_native_endpoint(ROOT, path, "a" * 40, "b" * 40, "c" * 64)


def test_stale_identity_hash_fails_closed(monkeypatch, tmp_path):
    _, path = _identity(tmp_path)
    monkeypatch.setattr(provenance, "inspect", lambda *a: "d" * 64)
    with pytest.raises(RuntimeError):
        provenance.resolve_native_endpoint(ROOT, path, "a" * 40, "b" * 40, "c" * 64)


def test_no_implicit_native_port_fallback():
    root = ROOT / "scripts/stage1"
    names = ["surreal_journal_smoke.py", "wp03_races.py", "native_ack_loss_probe.py"]
    for name in names:
        content = (root / name).read_text(encoding="utf-8")
        assert "http://127.0.0.1:5055" not in content, name
    journal = (root / names[0]).read_text(encoding="utf-8")
    assert "resolve_native_endpoint(" in journal
    assert "VAULT_VERIFIED_NATIVE_ENDPOINT" in journal
    assert "native_lost_ack(configuration,actor,secret,native_endpoint)" in journal
