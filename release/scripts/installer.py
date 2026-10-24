#!/usr/bin/env python3
"""Create an Ubuntu desktop installer. This command does not install or publish it."""
import argparse
import io
import importlib.util
from pathlib import Path
import re
import shutil
import tarfile
import tempfile

PROFILE='''# Per-application user namespaces for the Chromium and agent sandboxes.
abi <abi/4.0>,
include <tunables/global>
profile delta-observatory /opt/delta-observatory/delta-observatory flags=(unconfined) {
  userns,
}
profile delta-observatory-agent /opt/delta-observatory/resources/app/payload/host-bin/bwrap flags=(unconfined) {
  userns,
}
'''
POSTINST='''#!/bin/sh
set -e
if command -v apparmor_parser >/dev/null 2>&1 && [ -d /sys/kernel/security/apparmor ]; then
  apparmor_parser -r /etc/apparmor.d/delta-observatory
fi
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database -q; fi
'''
PRERM='''#!/bin/sh
set -e
if [ "$1" = remove ] && command -v apparmor_parser >/dev/null 2>&1 && [ -d /sys/kernel/security/apparmor ]; then
  apparmor_parser -R /etc/apparmor.d/delta-observatory || true
fi
'''
DESKTOP='''[Desktop Entry]
Type=Application
Name=Delta Observatory
Comment=Explore TESS observations and preserve scientific evidence
Exec=/opt/delta-observatory/delta-observatory
Icon=delta-observatory
Terminal=false
Categories=Education;Science;Astronomy;
StartupWMClass=Delta Observatory
'''
ICON='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" rx="26" fill="#080c14"/><path d="M64 24 104 100H24Z" fill="none" stroke="#70c8ff" stroke-width="8"/><circle cx="64" cy="77" r="8" fill="#f6c55c"/><path d="M20 49h88" stroke="#bdcbdf" stroke-width="2"/></svg>'''


def add_text(archive,name,text,mode=0o644):
    data=text.encode();info=tarfile.TarInfo(name);info.size=len(data);info.mode=mode;info.uid=info.gid=0;info.mtime=0
    archive.addfile(info,io.BytesIO(data))


def normalized(info):
    info.uid=info.gid=0;info.uname=info.gname='root';info.mtime=0
    return info


def ar_member(out,name,path):
    size=path.stat().st_size
    header=f'{name+"/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{size:<10}`\n'
    out.write(header.encode())
    with path.open('rb') as source:shutil.copyfileobj(source,out,1024**2)
    if size%2:out.write(b'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--version',default='0.2.0~preview1');args=parser.parse_args()
    if not re.fullmatch(r'[0-9][A-Za-z0-9.+:~_-]*',args.version):raise SystemExit('Invalid Debian package version.')
    if not (args.package/'BUILD.json').exists():raise SystemExit('Select a checked application directory.')
    spec=importlib.util.spec_from_file_location('verify_package',Path(__file__).with_name('verify-package.py'))
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    verifier.verify(args.package)
    if args.output.exists():raise SystemExit('The installer output already exists.')
    installed=sum(p.stat().st_size for p in args.package.rglob('*') if p.is_file())//1024
    control=f'''Package: delta-observatory
Version: {args.version}
Section: science
Priority: optional
Architecture: amd64
Maintainer: Delta Observatory <delta-observatory@users.noreply.github.com>
Installed-Size: {installed}
Depends: libc6 (>= 2.39), libgtk-3-0t64, libnss3, libasound2t64, libgbm1, libatk-bridge2.0-0t64, libxss1, libsecret-1-0
Recommends: apparmor, desktop-file-utils
Homepage: https://github.com/delta-observatory/delta-observatory
Description: Local exploratory TESS investigations
 Includes the database, scientific worker, API, interface, and optional agent.
 This preview does not establish detection performance or planet confirmation.
'''
    with tempfile.TemporaryDirectory(prefix='.delta-installer-',dir=args.output.parent) as temporary:
        root=Path(temporary);(root/'debian-binary').write_bytes(b'2.0\n')
        with tarfile.open(root/'control.tar.gz','w:gz') as archive:
            add_text(archive,'control',control);add_text(archive,'postinst',POSTINST,0o755);add_text(archive,'prerm',PRERM,0o755)
        with tarfile.open(root/'data.tar.gz','w:gz',compresslevel=3) as archive:
            archive.add(args.package,arcname='opt/delta-observatory',filter=normalized)
            add_text(archive,'etc/apparmor.d/delta-observatory',PROFILE)
            add_text(archive,'usr/share/applications/delta-observatory.desktop',DESKTOP)
            add_text(archive,'usr/share/icons/hicolor/scalable/apps/delta-observatory.svg',ICON)
        with args.output.open('xb') as out:
            out.write(b'!<arch>\n')
            for name in ('debian-binary','control.tar.gz','data.tar.gz'):ar_member(out,name,root/name)
    print(str(args.output))

if __name__=='__main__':main()
