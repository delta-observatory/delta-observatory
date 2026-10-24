#!/usr/bin/env python3
"""Exercise only an isolated prototype with synthetic input. No scientific performance claim."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile


def start(app, workspace, public_exploration=False):
    payload = app / 'payload'
    process = subprocess.Popen([str(payload / 'python/bin/python3.12'), '-s', str(app / 'supervisor.py'),
                                '--payload', str(payload), '--workspace', str(workspace), *(['--public-exploration'] if public_exploration else [])],
                               env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + 90
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('Startup failed: ' + process.stdout.read() + process.stderr.read())
            if not selector.select(timeout=0.2):
                continue
            event = json.loads(process.stdout.readline())
            if event['type'] == 'error':
                raise RuntimeError(event['message'])
            if event['type'] == 'ready':
                return process, event
        raise RuntimeError('Startup timed out.')
    except BaseException:
        process.terminate()
        process.wait(timeout=40)
        raise
    finally:
        selector.close()


def stop(process, workspace):
    process.terminate()
    process.communicate(timeout=40)
    assert process.returncode == 0, f'Shutdown failed: {process.returncode}'
    assert not (workspace / 'runtime.json').exists(), 'The runtime record remains after shutdown.'
    assert not (workspace / 'database/postmaster.pid').exists(), 'PostgreSQL remains running after shutdown.'


def request(base, route, token=None, body=None, method=None, raw=False, expected=200):
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if body is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(base + route, data=json.dumps(body).encode() if body is not None else None,
                                 method=method, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        payload = response.read()
        assert response.status == expected, f'{route}: HTTP {response.status}, expected {expected}'
        return payload if raw else json.loads(payload)


def wait_for(callback, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = callback()
        if value:
            return value
        time.sleep(0.25)
    raise RuntimeError('The integration check timed out.')


def exercise(app, workspace, output):
    if workspace.exists():
        raise RuntimeError('The smoke check requires a new workspace.')
    output.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Engineering integration with synthetic input. No scientific validation.', 'checks': {}}
    process = None
    try:
        process, ready = start(app, workspace)
        report['startup_seconds'] = ready['startup_seconds']
        base = ready['api_url']
        token = (workspace / 'owner.token').read_text().strip()
        assert request(base, '/api/observations', token)['total'] == 0
        report['checks']['empty_new_database'] = True
        request(base, '/api/observations', expected=401)
        request(base, '/gui-api/runs', method='POST', body={}, expected=403)
        report['checks']['authentication_and_read_only_gui'] = True
        catalog = request(base, '/api/catalog', token)
        assert catalog['datasets']['available'] and len(catalog['datasets']['items']) == 1
        assert not catalog['experiments']['available']
        report['checks']['public_catalog_without_private_reports'] = True
        methods = request(base, '/api/methods', token)
        assert len(methods) == 2
        report['checks']['public_method_contracts'] = True

        # A second owner of the same workspace must fail without stopping its services.
        duplicate = subprocess.run([str(app / 'payload/python/bin/python3.12'), '-s', str(app / 'supervisor.py'),
                                    '--payload', str(app / 'payload'), '--workspace', str(workspace)],
                                   env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True, timeout=15)
        assert duplicate.returncode != 0 and 'owns this workspace' in duplicate.stdout
        assert request(base, '/api/health')['status'] == 'ok'
        report['checks']['exclusive_workspace_ownership'] = True

        fixture = app / 'checks/fixture.py'
        fixture_env = {'PATH': '/usr/bin:/bin', 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                       'PYTHONPATH': str(app / 'payload/worker-packages'), 'HOME': str(workspace / 'home')}
        subprocess.run([str(app / 'payload/python/bin/python3.12'), '-s', str(fixture),
                        str(workspace / 'raw/tess-spoc-light-curves')], env=fixture_env, check=True, timeout=30)
        request(base, '/api/datasets/tess-spoc-light-curves/index', token, method='POST', expected=202)
        observations = wait_for(lambda: (items if (items := request(base, '/api/observations?state=ready', token)['items']) else None))
        assert len(observations) == 1 and observations[0]['target_id'] == 'TIC:0'
        observation_id = observations[0]['id']
        report['checks']['synthetic_fits_index'] = True
        run = request(base, '/api/runs', token, body={'method': {'id': 'tess-bls', 'version': 1},
                      'observation_ids': [observation_id], 'label': 'Synthetic desktop integration check'}, expected=201)
        run_id = run['id']

        def finished():
            result = request(base, '/api/runs/' + run_id, token)
            return result if all(j['state'] not in ('queued', 'running') for j in result['jobs']) else None

        result = wait_for(finished)
        assert result['jobs'][0]['state'] == 'complete', result['jobs']
        report['checks']['worker_bls_execution'] = True
        results = request(base, '/api/runs/' + run_id + '/results', token)
        report['worker_resources'] = results['jobs'][0]['resources']
        exported = request(base, '/api/runs/' + run_id + '/export?artifacts=all', token, raw=True)
        with zipfile.ZipFile(io.BytesIO(exported)) as archive:
            manifest = json.loads(archive.read('manifest.json'))
            for item in manifest['files']:
                data = archive.read(item['path'])
                assert len(data) == item['bytes']
                assert hashlib.sha256(data).hexdigest() == item['sha256']
            assert set(archive.namelist()) == {'manifest.json'} | {f['path'] for f in manifest['files']}
        assert request(base, '/api/runs/' + run_id + '/export?artifacts=all', token, raw=True) == exported
        report['checks']['evidence_export_hashes_and_repeatability'] = True

        campaign_document = {'name': 'desktop-guard-check', 'title': 'Engineering guard check',
                             'question': 'Does a missing cohort register block agent observation reads?'}
        campaign = request(base, '/api/campaigns', token, body=campaign_document, expected=201)
        request(base, '/api/campaigns/' + campaign['id'] + '/approve', token,
                body={'campaign_file_sha256': hashlib.sha256(json.dumps(campaign_document).encode()).hexdigest()})
        agent = request(base, '/api/clients', token, body={'name': 'desktop-check-agent', 'kind': 'agent',
                        'permissions': ['read'], 'campaign_id': campaign['id']}, expected=201)
        request(base, '/api/observations', agent['token'], expected=503)
        report['checks']['missing_cohort_register_blocks_agents'] = True
        stop(process, workspace)
        process = None
        report['checks']['clean_shutdown'] = True

        process, restarted = start(app, workspace)
        base = restarted['api_url']
        assert request(base, '/api/observations', token)['items'][0]['id'] == observation_id
        assert request(base, '/api/runs/' + run_id, token)['jobs'][0]['state'] == 'complete'
        wait_for(lambda: any(d['last_indexed_at'] for d in request(base, '/api/datasets', token)))
        assert request(base, '/api/observations', token)['total'] == 1
        assert request(base, '/api/runs/' + run_id + '/export?artifacts=all', token, raw=True) == exported
        report['checks']['restart_preserves_observations_results_and_export'] = True
        report['status'] = 'passed'
    except Exception as error:
        report.update(status='failed', error=str(error))
        raise
    finally:
        if process is not None:
            try:
                stop(process, workspace)
            except Exception as error:
                report.update(status='failed', shutdown_error=str(error))
        (output / 'runtime.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    if report.get('status') != 'passed':
        raise RuntimeError('The runtime checks failed. Inspect the report.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    exercise(args.app.resolve(), args.workspace.absolute(), args.output.resolve())
