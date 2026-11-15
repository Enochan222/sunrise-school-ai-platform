"""Execute the Native workflow's caller-side image identity contract in Bash."""
from pathlib import Path
import os
import subprocess
import shlex
import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/stage1-native-integration.yml'
KEYS = ('A_SURREAL_IMAGE_UID', 'A_SURREAL_IMAGE_GID',
        'ON_SURREAL_IMAGE_UID', 'ON_SURREAL_IMAGE_GID')


def caller_identity(text):
    before_bootstrap = text.split('          bash scripts/stage1/native_runtime_prepare.sh', 1)[0]
    marker = '          # Resolve the verified image identity in the caller shell.'
    assert marker in before_bootstrap, 'Native workflow loses child-shell UID/GID before relay checks'
    return '\n'.join(line[10:] for line in before_bootstrap.split(marker, 1)[1].splitlines())


@pytest.mark.parametrize('result,status,accepted', [
    ('12345:23456', 0, True),  # primary GID must not be guessed equal to UID
    ('12345:23456', 1, False),
    ('0:23456', 0, False), ('12345:0', 0, False),
    ('65535:23456', 0, False), ('12345:65535', 0, False),
    ('12345', 0, False), ('12345:23456\nextra', 0, False),
    ('root:root', 0, False), ('', 0, False),
])
def test_verified_identity_reaches_parent_compose_consumers(tmp_path, result, status, accepted):
    script = caller_identity(WORKFLOW.read_text())
    tools = tmp_path / 'bin'; tools.mkdir()
    # Execute real Bash exports/validation and child-shell inheritance. Only
    # image introspection is replaced; no Docker/runtime is claimed here.
    docker = tools / 'docker'
    docker.write_text('#!/bin/sh\nprintf "sha256:%064d\\n" 1\n')
    python = tools / 'python'
    python.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$PROBE_ARGS"\nprintf "%s" "$PROBE_IDENTITY"\nexit "$PROBE_EXIT"\n')
    docker.chmod(0o755); python.chmod(0o755)
    env = os.environ.copy()
    env.update(PATH=str(tools)+':'+env['PATH'], PROBE_IDENTITY=result,
               PROBE_EXIT=str(status), PROBE_ARGS=str(tmp_path/'args'), VAULT_DOCKER_CONTEXT='synthetic-test',
               VAULT_SURREAL_IMAGE_DIGEST='sha256:'+'a'*64)
    for key in KEYS: env[key] = '99'  # inherited stale values must not survive
    child = "\n".join('test "$'+key+'" = "'+value+'" || exit 91'
                      for key, value in zip(KEYS, ('12345','23456','12345','23456')))
    proc = subprocess.run(['bash', '-c', 'set -Eeuo pipefail\n'+script+
                           '\nbash -c '+shlex.quote(child)],
                          cwd=ROOT, env=env, capture_output=True, text=True)
    assert (proc.returncode == 0) is accepted, proc.stderr

    args = (tmp_path / 'args').read_text().splitlines()
    assert args == ['scripts/stage1/verify_surreal_image_user.py',
                    '--context', 'synthetic-test', '--image', 'sha256:'+f'{1:064d}',
                    '--digest', 'sha256:'+'a'*64]
