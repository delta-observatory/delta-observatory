#!/usr/bin/env python3
"""Assemble the Linux directory from the checked public build outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def bundle_fonts(release, frontend, notices):
    directory = frontend / 'fonts'
    directory.mkdir()
    rules = []
    for family, name in (('IBM Plex Mono', 'ibm-plex-mono'), ('IBM Plex Sans', 'ibm-plex-sans')):
        source = release / 'node_modules/@fontsource' / name
        shutil.copyfile(source / 'LICENSE', notices / f'{name}-LICENSE')
        for weight in (400, 500, 600):
            filename = f'{name}-latin-{weight}-normal.woff2'
            shutil.copyfile(source / 'files' / filename, directory / filename)
            rules.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
                         f"font-display:swap;src:url('/fonts/{filename}') format('woff2');}}")
    (frontend / 'fonts.css').write_text('\n'.join(rules) + '\n')
    index = frontend / 'index.html'
    html = re.sub(r'    <link[^>]+https://fonts\.(?:googleapis|gstatic)\.com[^>]*>\n', '', index.read_text())
    if 'https://fonts.' in html:
        raise SystemExit('An unexpected remote font reference remains.')
    html = html.replace('</head>', '  <link rel="stylesheet" href="/fonts.css">\n  </head>')
    index.write_text(html)


def package(release, output):
    if output.exists():
        raise SystemExit('The package destination must not exist.')
    payload = release / '.build/payload'
    for required in ('python/bin/python3.12', 'postgres/bin/postgres', 'sources.json', 'codex/codex', 'host-bin/bwrap'):
        if not (payload / required).is_file():
            raise SystemExit(f'Missing runtime: {required}')
    frontend = release / '.build/sources/frontend/dist'
    if not (frontend / 'index.html').is_file():
        raise SystemExit('Build the pinned frontend first.')
    shutil.copytree(release / 'node_modules/electron/dist', output, symlinks=True)
    (output / 'electron').rename(output / 'delta-observatory')
    app = output / 'resources/app'
    shutil.copytree(release / 'desktop', app, ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(payload, app / 'payload', symlinks=True)
    shutil.copytree(frontend, app / 'payload/frontend')
    shutil.copyfile(release / '.build/sources/frontend/LICENSE', app / 'payload/notices/frontend-LICENSE')
    bundle_fonts(release, app / 'payload/frontend', app / 'payload/notices')
    checks = app / 'checks'
    checks.mkdir()
    shutil.copyfile(release / 'scripts/smoke.py', checks / 'smoke.py')
    shutil.copyfile(release / 'tests/fixture.py', checks / 'fixture.py')
    shutil.copyfile(release / 'tests/clean-inside.py', checks / 'clean-inside.py')
    shutil.copyfile(release / 'tests/product-ui.cjs', checks / 'product-ui.cjs')
    shutil.copyfile(release / 'scripts/product-check.py', checks / 'product-check.py')
    shutil.copyfile(release / '.build/sources/agents/scripts/check_managed_isolation.py', checks / 'check_managed_isolation.py')
    shutil.copyfile(release.parent / 'LICENSE', output / 'DELTA-LICENSE')
    launcher = output / 'Delta Observatory.sh'
    launcher.write_text('#!/bin/sh\nset -eu\napp_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd)\n'
                        'exec "$app_dir/delta-observatory" "$@"\n')
    launcher.chmod(0o755)
    manifest = {'platform': 'linux-x64', 'baseline': 'Ubuntu 24.04, glibc 2.39',
                'python': '3.12.14', 'postgresql': '18.6', 'electron': '45.0.0', 'codex':'0.164.0', 'managed_model':'gpt-5.4', 'bubblewrap':'0.9.0-1ubuntu0.3',
                'fonts': {'@fontsource/ibm-plex-mono': '5.3.0', '@fontsource/ibm-plex-sans': '5.3.0'},
                'sources': json.loads((payload / 'sources.json').read_text()), 'files': {}}
    for path in sorted(output.rglob('*')):
        if path.is_symlink():
            if not path.resolve().is_relative_to(output.resolve()):
                raise SystemExit(f'The package contains an external symbolic link: {path}')
        elif path.is_file():
            manifest['files'][path.relative_to(output).as_posix()] = {
                'bytes': path.stat().st_size,
                'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest(),
            }
    (output / 'BUILD.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'directory': str(output), 'files': len(manifest['files']),
                      'bytes': sum(f['bytes'] for f in manifest['files'].values())}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(Path(__file__).resolve().parents[1], args.output.resolve())
