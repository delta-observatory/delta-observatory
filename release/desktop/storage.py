"""Desktop storage configuration shared by native file operations."""
import json
from pathlib import Path
import shutil
from jsonschema import Draft202012Validator


def settings(payload,root):
    schema=json.loads((payload/'components/backend/vendor/contracts/records/desktop-storage/v1.schema.json').read_text())
    path=root/'storage.json'
    default={key:value.get('const',value.get('default')) for key,value in schema['properties'].items()}
    document=json.loads(path.read_text()) if path.exists() else default
    Draft202012Validator(schema).validate(document)
    return document


def usage(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())


def check(payload,root,additional=0):
    policy=settings(payload,root)
    if usage(root)+additional>policy['maximum_bytes']:raise ValueError('The operation exceeds the workspace storage limit.')
    if shutil.disk_usage(root).free-additional<policy['reserve_bytes']:raise ValueError('The operation exceeds the free-space reserve.')
    return policy
