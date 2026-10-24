#!/usr/bin/env python3
"""Check the packaged file list, checksums, and symbolic-link boundary."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root):
    root=root.resolve()
    manifest=json.loads((root/'BUILD.json').read_text())
    files={p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and p!=root/'BUILD.json'}
    if set(files)!=set(manifest['files']):raise ValueError('The package file list differs from BUILD.json.')
    for name,path in files.items():
        with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if manifest['files'][name]!={'bytes':path.stat().st_size,'sha256':sha}:raise ValueError('The package file changed: '+name)
    for path in root.rglob('*'):
        if path.is_symlink() and (not path.exists() or not path.resolve().is_relative_to(root)):
            raise ValueError('The package contains an invalid symbolic link: '+path.relative_to(root).as_posix())
    return {'status':'passed','files':len(files),'bytes':sum(p.stat().st_size for p in files.values())}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('package',type=Path);args=parser.parse_args()
    print(json.dumps(verify(args.package)))
