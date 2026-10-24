#!/usr/bin/env python3
"""Run the package without host files, network access, or system language runtimes."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

OS_COMMANDS = ('dash', 'basename', 'dirname', 'sha256sum', 'cut', 'cat', 'date', 'id', 'uname', 'locale',
               'mkdir', 'rm', 'sleep', 'Xvfb', 'xkbcomp')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rootfs, package, output = args.rootfs.resolve(), args.package.resolve(), args.output.resolve()
    for mountpoint in ('app', 'work', 'home/desktop', 'build', 'tools'):
        (rootfs / mountpoint).mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=False)
    binaries = output / 'os-bin'
    binaries.mkdir()
    for name in OS_COMMANDS:
        shutil.copy2(rootfs / 'usr/bin' / name, binaries / name, follow_symlinks=True)
    (binaries / 'sh').symlink_to('dash')
    home = output / 'home'
    home.mkdir()
    command = [
        'bwrap', '--unshare-all', '--die-with-parent', '--clearenv',
        '--ro-bind', str(rootfs), '/', '--ro-bind', str(binaries), '/usr/bin',
        '--ro-bind', str(package), '/app', '--bind', str(output), '/work',
        '--bind', str(home), '/home/desktop', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
        '--tmpfs', '/run', '--tmpfs', '/root', '--tmpfs', '/build', '--tmpfs', '/tools',
        '--setenv', 'PATH', '/usr/bin:/bin', '--setenv', 'HOME', '/home/desktop',
        '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'XDG_RUNTIME_DIR', '/tmp/runtime',
        '--setenv', 'DISPLAY', ':99', '--chdir', '/work',
        '/app/resources/app/payload/python/bin/python3.12', '-s', '/app/resources/app/checks/clean-inside.py',
    ]
    result = subprocess.run(command)
    if result.returncode:
        raise SystemExit(result.returncode)
    print(json.dumps({'status': 'passed', 'report_directory': str(output)}))


if __name__ == '__main__':
    main()
