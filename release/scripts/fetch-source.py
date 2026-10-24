#!/usr/bin/env python3
"""Download one recorded build source and check its SHA-256 before use."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

release = Path(__file__).resolve().parents[1]
sources = json.loads((release / 'runtime-sources.json').read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', choices=sources)
args = parser.parse_args()
source = sources[args.source]
destination = release / '.cache' / source['filename']
destination.parent.mkdir(parents=True, exist_ok=True)
if not destination.exists():
    temporary = destination.with_suffix(destination.suffix + '.partial')
    try:
        with urllib.request.urlopen(source['url'], timeout=60) as response, temporary.open('xb') as output:
            shutil.copyfileobj(response, output)
        with temporary.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != source['sha256']:
                raise SystemExit('The source checksum differs. Review the source before changing its recorded hash.')
        temporary.rename(destination)
    finally:
        temporary.unlink(missing_ok=True)
with destination.open('rb') as stream:
    if hashlib.file_digest(stream, 'sha256').hexdigest() != source['sha256']:
        raise SystemExit('The cached source checksum differs.')
print(destination)
