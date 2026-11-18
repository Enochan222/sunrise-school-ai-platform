"""Copy the canonical A-owned UI into the standalone deployment bundle."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = ROOT.parent / "a-vault"
destination = ROOT / "vault_assets"
files = {}
for name in ("ui.js", "style.css", "templates/login.html", "templates/admin.html"):
    target = destination / name
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (source / name).read_bytes()
    source_hash = hashlib.sha256(data).hexdigest()
    if name == "ui.js":
        text = data.decode()
        # This Cloud variant completes bounded extraction synchronously. Keep
        # the Native UI untouched and make the deployed receipt truthful.
        replacements = {
            "mode: 'same-origin', credentials: 'same-origin',":
                "mode: 'same-origin', credentials: 'same-origin', referrerPolicy: 'same-origin',",
            "result.state !== 'SUBMITTED_NATIVE_PROCESSING'": "result.state !== 'READY'",
            "'已提交處理。來源 '": "'文字處理完成。來源 '",
            "'。目前未有處理完成確認。'": "'。可搜尋及下載。'",
            "'教材庫已確認上載提交。'": "'教材已儲存，可搜尋及下載。'",
            "PENDING: '已提交處理，尚未確認 Worker 結果。'": "PENDING: '原檔或索引尚待核實，請以原有請求核對。'",
        }
        for old, new in replacements.items():
            if text.count(old) != 1:
                raise RuntimeError("Canonical UI changed; Cloud receipt adaptation needs review")
            text = text.replace(old,new)
        data = text.encode()
    target.write_bytes(data)
    files[name] = {"canonical_sha256":source_hash,"deployed_sha256":hashlib.sha256(data).hexdigest()}
(destination / "manifest.json").write_text(json.dumps(files, indent=2))
print("Prepared4 A UI assets with explicit Cloud READY receipt adaptation; no credentials included")
