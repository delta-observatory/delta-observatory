#!/usr/bin/env python3
"""Export only the pinned public sources. Never read private repositories or live state."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

COMPONENTS = ('database', 'backend', 'workers', 'frontend', 'agents')


def prepare(workspace, destination):
    if destination.exists():
        raise SystemExit('The source destination must not exist.')
    pins = json.loads((workspace / 'components.json').read_text())
    selected = {c['name']: c for c in pins['components'] if c['name'] in COMPONENTS}
    if set(selected) != set(COMPONENTS) or any(c['visibility'] != 'public' for c in selected.values()):
        raise SystemExit('The component manifest must identify five public runtime components.')
    destination.mkdir(parents=True)
    for name, component in selected.items():
        archive = subprocess.check_output(['git', '-C', str(workspace / name), 'archive', component['commit']])
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            source.extractall(destination / name, filter='data')
    vendored_sources = {}
    for name in ('backend', 'workers'):
        vendored_sources[name] = (destination / name / 'vendor/contracts/SOURCE').read_text().strip()
        # Documentation can differ between releases. Every executable contract must match.
        for path in (destination / 'database/contracts').rglob('*.json'):
            relative = path.relative_to(destination / 'database/contracts')
            if path.read_bytes() != (destination / name / 'vendor/contracts' / relative).read_bytes():
                raise SystemExit(f'{name} contract mismatch: {relative}')
        for path in (destination / 'database/migrations').glob('*.sql'):
            if path.read_bytes() != (destination / name / 'vendor/migrations' / path.name).read_bytes():
                raise SystemExit(f'{name} migration mismatch: {path.name}')
    shutil.copyfile(workspace / 'components.json', destination / 'components.json')
    (destination / 'sources.json').write_text(json.dumps({
        'components': selected,
        'vendored_contract_sources': vendored_sources,
        'component_manifest_sha256': hashlib.sha256((workspace / 'components.json').read_bytes()).hexdigest(),
        'private_repositories': [],
    }, indent=2) + '\n')
    print(f'Prepared five public components in {destination}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.workspace.resolve(), args.output.resolve())
