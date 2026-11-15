"""Only the three PR24 handoff artefacts may extend AT13 release scope.

Do not allow unrelated docs/stage1 or repo governance through this exception.
"""
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/stage1/acceptance'))
import release_manifest as release


@pytest.mark.parametrize('path', [
    'docs/stage1/CHAT_ENGINEERING_COMPLETION_REPORT.md',
    'docs/stage1/PORTABLE_STAGE1_TEST_HANDOFF.md',
    'docs/stage1/WORK_OR_LOCAL_RUNTIME_HANDOFF_PROMPT.md',
    'apps/a-vault/ui.js',
    'scripts/stage1/acceptance/http_boundaries.py',
    'tests/stage1/test_chat_at14_ui_regression_contract.py',
])
def test_expected_release_scope_path_allowed(path):
    assert release.allowed_stage1_change(path)


@pytest.mark.parametrize('path', [
    'docs/stage1/IMPLEMENTATION_PLAN.md',
    'docs/stage1/SOMETHING_ELSE.md',
    'docs/stage1/PORTABLE_STAGE1_TEST_HANDOFF.md/secret',
    'docs/stage0/OWNER_APPROVAL.md',
    '.github/workflows/ci.yml',
    'apps/other-app/main.py',
    'docs/stage1/CHAT_ENGINEERING_COMPLETION_REPORT.md.bak',
])
def test_unapproved_release_scope_path_denied(path):
    assert release.allowed_stage1_change(path) is False


@pytest.fixture
def manifest_repo(tmp_path):
    import hashlib
    import subprocess
    repo=tmp_path/'repo';repo.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
    git('init','-q');git('config','user.name','Synthetic Scope Test')
    git('config','user.email','scope@example.invalid')
    entries={}
    for path in ('apps/a-vault/app.py','README.md','.github/workflows/test.yml'):
        p=repo/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('baseline\n')
        entries[path]=hashlib.sha256(p.read_bytes()).hexdigest()
    def commit(entries):
        (repo/'FILE_MANIFEST.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in entries.items()))
        git('add','.');git('commit','-qm','synthetic scope fixture')
        return git('rev-parse','HEAD')
    base=commit(entries)
    return repo,base,entries,commit


def test_owner_evidence_manifest_delta_is_verified(manifest_repo):
    import hashlib
    repo,base,entries,commit=manifest_repo
    path='docs/stage1/evidence/synthetic.json';p=repo/path
    p.parent.mkdir(parents=True);p.write_text('{"fixture":"synthetic"}\n')
    entries[path]=hashlib.sha256(p.read_bytes()).hexdigest();head=commit(entries)
    assert set(release.verify_stage1_changes(repo,base,head))=={'FILE_MANIFEST.sha256',path}
    # The manifest is never an unconditionally allowed runtime path.
    assert release.allowed_stage1_change('FILE_MANIFEST.sha256') is False


@pytest.mark.parametrize('mutation',[
    'wrong_hash','duplicate','traversal','symlink','drop_existing_a',
    'non_a_add','non_a_hash','non_a_remove','actual_workflow_change'])
def test_packaging_manifest_cannot_weaken_scope(manifest_repo,mutation):
    import hashlib
    repo,base,entries,commit=manifest_repo
    if mutation=='wrong_hash':entries['apps/a-vault/app.py']='0'*64
    elif mutation=='duplicate':
        head=base
        p=repo/'FILE_MANIFEST.sha256';p.write_text(p.read_text()+p.read_text().splitlines()[0]+'\n')
        import subprocess
        subprocess.run(['git','-C',str(repo),'add','.'],check=True)
        subprocess.run(['git','-C',str(repo),'commit','-qm','duplicate'],check=True)
        head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    elif mutation=='traversal':entries['apps/a-vault/../../README.md']='0'*64
    elif mutation=='symlink':
        p=repo/'apps/a-vault/link';p.symlink_to('../../README.md')
        entries['apps/a-vault/link']=hashlib.sha256(b'baseline\n').hexdigest()
    elif mutation=='drop_existing_a':entries.pop('apps/a-vault/app.py')
    elif mutation=='non_a_add':
        (repo/'docs/other').mkdir(parents=True);(repo/'docs/other/policy.md').write_text('changed\n')
        entries['docs/other/policy.md']=hashlib.sha256(b'changed\n').hexdigest()
    elif mutation=='non_a_hash':entries['README.md']='0'*64
    elif mutation=='non_a_remove':entries.pop('README.md')
    else:
        (repo/'.github/workflows/test.yml').write_text('changed\n')
        entries['.github/workflows/test.yml']=hashlib.sha256(b'changed\n').hexdigest()
    if mutation!='duplicate':head=commit(entries)
    with pytest.raises(RuntimeError):release.verify_stage1_changes(repo,base,head)
