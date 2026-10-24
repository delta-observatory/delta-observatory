#!/usr/bin/env python3
"""Bundle pinned Codex and Ubuntu namespace dependencies without a host installation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ubuntu-root',type=Path,required=True);args=parser.parse_args()
    release=Path(__file__).resolve().parents[1];payload=release/'.build/payload';ubuntu=args.ubuntu_root.resolve()
    package=release/'node_modules/@openai/codex-linux-x64'
    if json.loads((package/'package.json').read_text())['version']!='0.164.0-linux-x64':raise SystemExit('The Codex package version differs from the pin.')
    source=package/'vendor/x86_64-unknown-linux-musl/bin/codex'
    (payload/'codex').mkdir(exist_ok=True);shutil.copyfile(source,payload/'codex/codex');(payload/'codex/codex').chmod(0o755)
    (payload/'host-bin').mkdir(exist_ok=True);(payload/'host-lib').mkdir(exist_ok=True)
    deb=ubuntu/'tmp/bubblewrap_0.9.0-1ubuntu0.3_amd64.deb'
    expected=json.loads((release/'runtime-sources.json').read_text())['bubblewrap']['sha256']
    if hashlib.file_digest(deb.open('rb'),'sha256').hexdigest()!=expected:raise SystemExit('The Bubblewrap package checksum differs from the pin.')
    extracted=ubuntu/'tmp/delta-bwrap-package'
    shutil.copyfile(extracted/'usr/bin/bwrap',payload/'host-bin/bwrap');(payload/'host-bin/bwrap').chmod(0o755)
    for library in ('libcap.so.2','libselinux.so.1','libpcre2-8.so.0'):shutil.copyfile(ubuntu/'usr/lib/x86_64-linux-gnu'/library,payload/'host-lib'/library)
    notices=payload/'notices'
    for name in ('Codex-LICENSE','Codex-NOTICE'):shutil.copyfile(release/'resources/notices'/name,notices/name)
    for package_name,docroot in [('bubblewrap',extracted),('libcap2',ubuntu),('libselinux1',ubuntu),('libpcre2-8-0',ubuntu)]:
        shutil.copyfile(docroot/'usr/share/doc'/package_name/'copyright',notices/(package_name+'-copyright'))
    sources=json.loads((release/'runtime-sources.json').read_text())
    (notices/'agent-runtime-sources.json').write_text(json.dumps({key:sources[key] for key in ('bubblewrap','codex-license','codex-notice')},indent=2)+'\n')
    print('Bundled Codex 0.164.0 and Ubuntu 24.04 namespace dependencies.')

if __name__=='__main__':main()
