"""Clone, check, and pin the component repositories that components.json lists.

The entry repository holds components.json. Each public component is a separate
repository. The script clones each one into a directory of the entry repository
with the component name. The entry repository's .gitignore excludes those
directories. Documents and build scripts use this sibling layout. A private
component is cloned only with --private, on its default branch, and only when
it has an address.

  components.py clone [--latest] [--private] [--source DIR]
                                                   clone the public components at their pinned commits
  components.py check                              compare the clones with the pinned commits
  components.py pin                                write the current commits of the clones to the manifest
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r'^[a-z][a-z0-9-]*$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')


class ManifestError(Exception):
    pass


def load(path: Path) -> dict:
    manifest = json.loads(path.read_text())
    if manifest.get('contract') != 'components/1':
        raise ManifestError('contract must be components/1')
    for c in manifest.get('components', []):
        if not NAME.match(c.get('name', '')):
            raise ManifestError(f"invalid component name {c.get('name')!r}")
        if c.get('visibility') == 'public':
            if not c.get('repository') or not COMMIT.match(c.get('commit') or ''):
                raise ManifestError(f"{c['name']}: a public component needs repository and a 40-character commit")
        elif c.get('visibility') != 'private':
            raise ManifestError(f"{c['name']}: visibility must be public or private")
    return manifest


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def state(path: Path) -> tuple[str, bool]:
    """The HEAD commit and whether the working tree has uncommitted changes."""
    return git(path, 'rev-parse', 'HEAD'), bool(git(path, 'status', '--porcelain'))


def public(manifest: dict) -> list[dict]:
    return [c for c in manifest['components'] if c['visibility'] == 'public']


def clone(manifest: dict, dest: Path, source: str | None, latest: bool, private: bool) -> int:
    for c in manifest['components']:
        pinned = c['visibility'] == 'public' and not latest
        if c['visibility'] == 'private' and not (private and c.get('repository')):
            print(f"{c['name']}: private, not cloned")
            continue
        target = dest/c['name']
        if target.exists():
            print(f"{c['name']}: {target} exists. Move it, or use the check command.", file=sys.stderr)
            return 1
        url = f"{source.rstrip('/')}/{c['name']}" if source else c['repository']
        subprocess.run(['git', 'clone', '-q', url, str(target)], check=True)
        if pinned:
            git(target, 'checkout', '-q', '--detach', c['commit'])
        print(f"{c['name']}: {git(target, 'rev-parse', 'HEAD')}{' (pinned)' if pinned else ''}")
    return 0


def check(manifest: dict, dest: Path) -> int:
    failed = False
    for c in public(manifest):
        target = dest/c['name']
        if not (target/'.git').exists():
            print(f"{c['name']}: missing"); failed = True; continue
        head, dirty = state(target)
        problems = ([f"HEAD {head} differs from pinned {c['commit']}"] if head != c['commit'] else []) + \
                   (['uncommitted changes'] if dirty else [])
        print(f"{c['name']}: {'; '.join(problems) if problems else 'matches'}")
        failed = failed or bool(problems)
    return 1 if failed else 0


def pin(manifest: dict, dest: Path, path: Path) -> int:
    commits = {}
    for c in public(manifest):
        head, dirty = state(dest/c['name'])
        if dirty:
            print(f"{c['name']}: uncommitted changes. Commit them before pinning.")
            return 1
        commits[c['name']] = head
    for c in public(manifest):
        c['commit'] = commits[c['name']]
        print(f"{c['name']}: {c['commit']}")
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=['clone', 'check', 'pin'])
    parser.add_argument('--manifest', type=Path, default=ROOT/'components.json')
    parser.add_argument('--dest', type=Path, default=ROOT, help='directory that holds the component directories')
    parser.add_argument('--source', help='clone from <source>/<name> instead of the repository address')
    parser.add_argument('--latest', action='store_true', help='stay on the default branch instead of the pinned commit')
    parser.add_argument('--private', action='store_true', help='also clone the private components that have an address')
    args = parser.parse_args()
    try:
        manifest = load(args.manifest)
    except (ManifestError, ValueError, OSError) as e:
        print(f'components.json: {e}', file=sys.stderr)
        return 2
    if args.command == 'clone':
        return clone(manifest, args.dest, args.source, args.latest, args.private)
    if args.command == 'check':
        return check(manifest, args.dest)
    return pin(manifest, args.dest, args.manifest)


if __name__ == '__main__':
    sys.exit(main())
