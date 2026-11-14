"""Reject incompatible QA/app pins using actual installed package metadata."""
from importlib.metadata import requires
from pathlib import Path
from packaging.requirements import Requirement


def test_qa_pins_satisfy_runtime_dependency_requirements():
    root = Path(__file__).resolve().parents[2]
    pins = {}
    for path in ('requirements-qa.txt', 'apps/a-vault/requirements.txt'):
        for line in (root/path).read_text().splitlines():
            line = line.split('#', 1)[0].strip()
            if line:
                requirement = Requirement(line)
                pins[requirement.name.lower().replace('_', '-')] = requirement
    for name in pins:
        for value in requires(name) or []:
            dependency = Requirement(value)
            if dependency.marker and not dependency.marker.evaluate():
                continue
            pin = pins.get(dependency.name.lower().replace('_', '-'))
            if pin:
                for spec in pin.specifier:
                    if spec.operator == '==':
                        assert spec.version in dependency.specifier, (
                            f'{name} requires {dependency}; conflicting pin: {pin}')
