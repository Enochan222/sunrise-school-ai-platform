import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location(
    'restore_network_verifier',
    Path(__file__).resolve().parents[3] / 'scripts/stage1/restore/isolated_restore.py',
)
restore = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(Path(spec.origin).parent))
spec.loader.exec_module(restore)


@pytest.fixture
def target(monkeypatch):
    project = 'sunrise-s1-restore-synthetic'
    args = SimpleNamespace(context='desktop-linux', project=project)
    env = {
        'A_DB_RESTORE_IMAGE': 'image-a', 'ON_DB_RESTORE_IMAGE': 'image-on',
        'ON_RESTORE_IMAGE': 'image-native', 'A_RESTORE_UID': '1000',
        'A_RESTORE_GID': '1000', 'ON_RESTORE_UID': '1000', 'ON_RESTORE_GID': '1000',
    }
    networks = {}
    for leaf, digit in [('a_db_private', '1'), ('on_db_private', '2')]:
        name = f'{project}_{leaf}'
        networks[name] = {
            'Name': name, 'Id': digit * 64, 'Internal': True, 'Driver': 'bridge',
            'Labels': {'com.docker.compose.project': project, 'com.docker.compose.network': leaf},
        }
    containers = {}
    for service, leaf, image, mount in [
        ('a_db', 'a_db_private', 'image-a', '/mydata'),
        ('on_db', 'on_db_private', 'image-on', '/mydata'),
        ('native', 'on_db_private', 'image-native', '/app/data'),
    ]:
        containers[service] = {
            'Id': service, 'Image': image,
            'Config': {'Labels': {'com.docker.compose.project': project}, 'User': '1000:1000'},
            'State': {'Status': 'created', 'Running': False},
            'Mounts': [{'Type': 'volume', 'Name': f'{project}_{service}_data', 'Destination': mount}],
            'NetworkSettings': {'Networks': {f'{project}_{leaf}': {'NetworkID': ''}}},
        }
    monkeypatch.setattr(restore, 'container_id', lambda args, service, env: service)
    monkeypatch.setattr(restore, 'docker', lambda context, *cmd: json.dumps([
        networks[cmd[-1]] if cmd[0] == 'network' else containers[cmd[-1]]
    ]))
    return args, env, networks, containers


def test_created_network_objects_match_live_attachments(target):
    args, env, networks, containers = target
    created = restore.inspect_isolation(args, env, running=set())
    for service in ('a_db', 'on_db', 'native'):
        container = containers[service]
        container['State'] = {'Status': 'running', 'Running': True}
        for name, endpoint in container['NetworkSettings']['Networks'].items():
            endpoint['NetworkID'] = networks[name]['Id']
        running = {k for k, v in containers.items() if v['State']['Running']}
        assert restore.inspect_isolation(args, env, running=running) == created


@pytest.mark.parametrize('bad', ['', 'f' * 64])
def test_running_endpoint_requires_exact_id(target, bad):
    args, env, _, containers = target
    container = containers['a_db']
    container['State'] = {'Status': 'running', 'Running': True}
    next(iter(container['NetworkSettings']['Networks'].values()))['NetworkID'] = bad
    with pytest.raises(restore.BackupInvalid, match='attachment'):
        restore.inspect_isolation(args, env, running={'a_db'})


@pytest.mark.parametrize('case', ['foreign', 'external', 'collision', 'extra_attachment'])
def test_created_target_network_checks_fail_closed(target, case):
    args, env, networks, containers = target
    first, second = list(networks.values())
    if case == 'foreign':
        first['Labels']['com.docker.compose.project'] = 'foreign'
    elif case == 'external':
        first['Internal'] = False
    elif case == 'collision':
        first['Id'] = second['Id']
    else:
        containers['a_db']['NetworkSettings']['Networks'][second['Name']] = {'NetworkID': ''}
    with pytest.raises(restore.BackupInvalid):
        restore.inspect_isolation(args, env, running=set())


def test_restore_ownership_caps_are_limited_to_networkless_root_helper(target, monkeypatch, tmp_path):
    args, env, _, _ = target
    args.workdir = tmp_path
    volume = args.project + '_a_db_data'
    calls = []

    def docker(context, *cmd):
        if cmd[:2] == ('volume', 'inspect'):
            return json.dumps([{'Name': volume, 'Labels': {
                'com.docker.compose.project': args.project,
                'com.docker.compose.volume': 'a_db_data',
            }}])
        calls.append(cmd)
        return ''

    monkeypatch.setattr(restore, 'docker', docker)
    restore.restore_new_target_db_owner(args, env, 'a_db', {})
    root, nonroot = calls
    for cmd in calls:
        assert cmd[cmd.index('--network') + 1] == 'none'
        assert cmd[cmd.index('--cap-drop') + 1] == 'ALL'
    assert root[root.index('--user') + 1] == '0:0'
    assert {root[i + 1] for i, x in enumerate(root) if x == '--cap-add'} == {
        'CHOWN', 'DAC_OVERRIDE',
    }
    assert nonroot[nonroot.index('--user') + 1] == '1000:1000'
    assert '--cap-add' not in nonroot
