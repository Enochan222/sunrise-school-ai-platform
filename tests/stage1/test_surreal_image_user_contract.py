"""Non-Native image UID-only/primary GID and digest isolation regressions.

These tests do NOT claim Docker, pinned image, DB or restore runtime PASS.
"""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'scripts/stage1/verify_surreal_image_user.py'


def load():
    spec=importlib.util.spec_from_file_location('stage1_image_user',SOURCE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PASSWD=b"root:x:0:0:root:/root:/bin/sh\nnonroot:x:65532:65532:nonroot:/:/sbin/nologin\n"
GROUP=b"root:x:0:\nnonroot:x:65532:\n"


@pytest.mark.parametrize('declared,expected',[
    ('65532',(65532,65532)), # actual observed UID-only image configuration
    ('65532:65532',(65532,65532)),
    ('nonroot',(65532,65532)),
])
def test_image_account_verified_against_passwd_and_group(declared,expected):
    assert load().parse_identity(declared,PASSWD,GROUP)==expected


@pytest.mark.parametrize('declared',[
    '', '0','0:0','65532:0','0:65532',
    '65532:65531','65532:','65532:garbage','-1',
    '65532:65532:65532','65532/65532','1000',
    'nonexistent','root','65532\n0','65532 :65532',
])
def test_root_missing_malformed_or_unverified_uid_gid_fail_closed(declared):
    with pytest.raises(ValueError):
        load().parse_identity(declared,PASSWD,GROUP)


@pytest.mark.parametrize('passwd,group',[
    (b"root:x:0:0:root:/root:/bin/sh\n",GROUP),
    (PASSWD,b"root:x:0:\n"),
    (PASSWD+b"duplicate:x:65532:65532::/:/bin/false\n",GROUP),
    (PASSWD,b"nonroot:x:65532:\nnonroot2:x:65532:\n"),
    (b"nonroot:x:65532:0::/:/bin/false\n",GROUP),
    (PASSWD+b"malformed:x:one:65532::/:/bin/false\n",GROUP),
    (PASSWD,b"nonroot:x:invalid:\n"),
])
def test_missing_ambiguous_corrupt_or_root_image_account_records_rejected(passwd,group):
    with pytest.raises(ValueError):
        load().parse_identity('65532',passwd,group)


def test_immutable_image_id_and_registry_digest_required_before_container_creation(monkeypatch):
    mod=load()
    invoked=[]
    def deny(*args,**kwargs):
        invoked.append(args)
        raise AssertionError('Docker MUST NOT be invoked for invalid identity')
    monkeypatch.setattr(mod,'run',deny)
    for image,digest in [
        ('surrealdb/surrealdb:v2.3.10','sha256:'+'a'*64),
        ('sha256:'+'a'*64,'latest'),
        ('sha256:'+'a'*63,'sha256:'+'b'*64),
        ('sha256:'+'a'*64,'sha256:'+'b'*63),
    ]:
        with pytest.raises(ValueError):
            mod.verify('default',image,digest)
    assert invoked==[]


def test_wrong_image_registry_digest_refuses_to_create_container(monkeypatch):
    mod=load()
    immutable='sha256:'+'a'*64
    expected='sha256:'+'b'*64
    created=[]
    def controlled(*args,**kwargs):
        if args[3:5]==('image','inspect'):
            return __import__('json').dumps([{
                'Id':immutable,'RepoDigests':['surrealdb/surrealdb@sha256:'+'c'*64],
                'Config':{'User':'65532'}}])
        created.append(args)
        raise AssertionError('No container should be created for wrong digest')
    monkeypatch.setattr(mod,'run',controlled)
    with pytest.raises(ValueError,match='registry digest'):
        mod.verify('default',immutable,expected)
    assert created==[]
