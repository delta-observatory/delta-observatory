#!/usr/bin/env python3
"""Check automatic backup and recovery from the previous desktop schema."""
import argparse
import importlib.util
import json
from pathlib import Path
import zipfile
from smoke import start, stop, request
spec = importlib.util.spec_from_file_location('product_check', Path(__file__).with_name('product-check.py'))
product = importlib.util.module_from_spec(spec)
spec.loader.exec_module(product)


def exercise(previous, app, output):
    output.mkdir(parents=True, exist_ok=False)
    workspace, restored = output/'previous-workspace', output/'restored'
    process = None
    current_root = workspace
    report = {'scope':'Engineering migration and data-only recovery. No scientific validation.', 'checks':{}}
    try:
        process, ready = start(previous, workspace)
        token = (workspace/'owner.token').read_text().strip()
        original = request(ready['api_url'], '/api/me', token)
        stop(process, workspace)
        process = None
        process, ready = start(app, workspace, True)
        assert request(ready['api_url'], '/api/me', token) == original
        backups = list((workspace/'backups').glob('before-migration-*.zip'))
        assert len(backups) == 1
        with zipfile.ZipFile(backups[0]) as archive:
            manifest = json.loads(archive.read('backup.json'))
            assert len(manifest['migrations']) == len(list((previous/'payload/components/database/migrations').glob('*.sql')))
        assert request(ready['api_url'], '/api/investigations', token)['items'] == []
        report['checks']['backup_precedes_new_migrations'] = True
        report['checks']['existing_owner_remains_valid'] = True
        product.utility(app, workspace, 'recovery.py', 'restore', '--path', str(backups[0]), '--destination', str(restored))
        stop(process, workspace)
        process = None
        current_root = restored
        process, ready = start(app, restored, True)
        restored_token = (restored/'owner.token').read_text().strip()
        assert restored_token != token
        request(ready['api_url'], '/api/me', token, expected=401)
        assert request(ready['api_url'], '/api/investigations', restored_token)['items'] == []
        report['checks']['previous_schema_restore_and_forward_migration'] = True
        report['checks']['restored_credentials_rotated'] = True
        report['status'] = 'passed'
    except Exception as error:
        report.update(status='failed',error=str(error))
        raise
    finally:
        if process is not None:
            stop(process,current_root)
        (output/'migration.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-app',type=Path,required=True)
    parser.add_argument('--app',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    exercise(args.previous_app.resolve(),args.app.resolve(),args.output.resolve())
