"""Own the prototype processes and workspace. No cluster access or network acquisition."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MARKER = 'delta-desktop-prototype/1'


def event(kind, **values):
    print(json.dumps({'type': kind, **values}), flush=True)


def atomic_text(path, value):
    temporary = path.with_name(path.name + '.new')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def workspace_lock(root):
    # Refuse a foreign or symlinked workspace. This protects the existing deployment.
    if root.is_symlink() or root.absolute() != root.resolve():
        raise RuntimeError('The prototype workspace must not contain symbolic links.')
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    marker = root / 'workspace.json'
    if marker.exists():
        if json.loads(marker.read_text()).get('kind') != MARKER:
            raise RuntimeError('This directory belongs to another application.')
    elif any(root.iterdir()):
        raise RuntimeError('Choose an empty directory for the prototype workspace.')
    root.chmod(0o700)
    lock = (root / '.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise RuntimeError('Another prototype process owns this workspace.') from None
    if not marker.exists():
        atomic_text(marker, json.dumps({'kind': MARKER}) + '\n')
    return lock


def environment(payload, root, component):
    # Never inherit a live database URI, source mounts, Python packages, or provider credentials.
    env = {key: os.environ[key] for key in ('LANG', 'LC_ALL', 'TZ') if key in os.environ}
    env.update({
        'PATH': str(payload / 'postgres/bin') + ':/usr/bin:/bin',
        'HOME': str(root / 'home'),
        'TMPDIR': str(root / 'tmp'),
        'LC_ALL': 'C.UTF-8',
        'PYTHONNOUSERSITE': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONUNBUFFERED': '1',
        'PYTHONHOME': str(payload / 'python'),
        'LD_LIBRARY_PATH': str(payload / 'postgres/lib'),
        'PYTHONPATH': os.pathsep.join([str(payload / f'{component}-packages'),
                                      str(payload / 'components' / ('backend' if component == 'api' else 'workers') / 'src')]),
        'MPLCONFIGDIR': str(root / 'cache/matplotlib'),
        'XDG_CACHE_HOME': str(root / 'cache'),
        'XDG_CONFIG_HOME': str(root / 'home/config'),
        'XDG_DATA_HOME': str(root / 'home/data'),
        'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
    })
    return env


def run_logged(command, env, log, timeout=60):
    with log.open('ab') as output:
        subprocess.run(command, env=env, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=timeout)


def provision(payload, root, url):
    sys.path[:0] = [str(payload / 'api-packages'), str(payload / 'components/backend/src')]
    import psycopg
    from psycopg.rows import dict_row
    from delta_api.auth import PERMISSIONS, create_client, token_sha256

    with psycopg.connect(url.replace('/delta?', '/postgres?'), autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = 'delta'").fetchone():
            conn.execute('CREATE DATABASE delta')
    migration_dir = payload / 'components/database/migrations'
    with psycopg.connect(url, autocommit=True) as conn:
        if conn.execute("SELECT to_regclass('schema_migration')").fetchone()[0]:
            known = {p.stem for p in migration_dir.glob('*.sql')}
            applied = {r[0] for r in conn.execute('SELECT version FROM schema_migration')}
            if not applied <= known:
                raise RuntimeError('This database needs a newer prototype. Automatic downgrade is unavailable.')
    env = environment(payload, root, 'api')
    env.update(DATABASE_URL=url, MIGRATIONS_DIR=str(migration_dir))
    run_logged(['/bin/sh', str(payload / 'components/database/migrate.sh')], env, root / 'logs/migrations.log')
    with psycopg.connect(url, autocommit=True, row_factory=dict_row) as conn:
        owner = conn.execute("SELECT * FROM client WHERE name = 'desktop-owner'").fetchone()
        token_path = root / 'owner.token'
        if owner is None:
            _, token = create_client(conn, name='desktop-owner', kind='person', permissions=list(PERMISSIONS),
                                     created_by='desktop-bootstrap', note='Owner of this isolated desktop workspace.')
            atomic_text(token_path, token + '\n')
        elif not token_path.is_file() or token_sha256(token_path.read_text().strip()) != owner['token_sha256']:
            raise RuntimeError('The desktop credential is missing or does not match this database.')
        if not conn.execute("SELECT 1 FROM client WHERE name = 'desktop-reader'").fetchone():
            create_client(conn, name='desktop-reader', kind='service', permissions=['read'],
                          created_by='desktop-bootstrap', note='Read-only access for the prototype GUI.')


def stop_child(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=12)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)


def serve(payload, root, parent_pid=None):
    if os.geteuid() == 0:
        raise RuntimeError('Run the desktop prototype as an ordinary user.')
    started = time.monotonic()
    lock = workspace_lock(root)
    children, logs = [], []
    postgres_started = False
    stopping = False
    pg = payload / 'postgres/bin'
    env = environment(payload, root, 'api')

    def stop_signal(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGINT, stop_signal)
    try:
        for relative in ('database', 'socket', 'logs', 'tmp', 'cache', 'home/config', 'home/data', 'artifacts', 'raw/tess-spoc-light-curves'):
            directory = root / relative
            if directory.is_symlink():
                raise RuntimeError('The workspace contains a symbolic link in a managed directory.')
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if shutil.disk_usage(root).free < 512 * 1024**2:
            raise RuntimeError('The prototype needs at least 512 MiB of free workspace space.')
        socket_dir = root / 'socket'
        if len(str(socket_dir).encode()) > 85:
            raise RuntimeError('Choose a shorter workspace path for the PostgreSQL socket.')
        data = root / 'database'
        event('stage', message='Starting the separate database.')
        if not (data / 'PG_VERSION').exists():
            if any(data.iterdir()):
                raise RuntimeError('Database initialization is incomplete. Preserve this workspace before repair.')
            run_logged([str(pg / 'initdb'), '-D', str(data), '-U', 'delta', '--encoding=UTF8', '--locale=C',
                        '--auth-local=trust', '--auth-host=reject'], env, root / 'logs/postgres-init.log')
        if (data / 'PG_VERSION').read_text().strip() != '18':
            raise RuntimeError('This prototype requires a separate PostgreSQL 18 workspace.')
        options = shlex.join(['-h', '', '-k', str(socket_dir), '-c', 'shared_buffers=64MB', '-c', 'max_connections=20'])
        # pg_ctl starts only this marked workspace. It never uses a host PostgreSQL service.
        status = subprocess.run([str(pg / 'pg_ctl'), '-D', str(data), 'status'], env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        if status != 0:
            run_logged([str(pg / 'pg_ctl'), '-D', str(data), '-l', str(root / 'logs/postgres.log'),
                        '-w', '-t', '30', '-o', options, 'start'], env, root / 'logs/postgres-control.log')
        postgres_started = True
        url = 'postgresql://delta@/delta?' + urllib.parse.urlencode({'host': str(socket_dir)})
        event('stage', message='Checking the database migrations.')
        provision(payload, root, url)
        shared = {
            'DATABASE_URL': url,
            'DELTA_ARTIFACT_ROOT': str(root / 'artifacts'),
            'DELTA_RAW_ROOT': str(root / 'raw'),
            'DELTA_CATALOG_ROOT': str(payload / 'catalog'),
            'DELTA_DATASETS_ROOT': str(payload / 'catalog/datasets'),
            # Private experiment records and cohort reservations are not packaged.
            # The existing cohort guard therefore refuses observation access by agents.
            'DELTA_EXPERIMENTS_ROOT': str(root / 'unavailable-experiments'),
            'DELTA_COHORTS_PATH': str(root / 'unavailable-experiments/cohorts.json'),
            'DELTA_GUI_READ_CLIENT': 'desktop-reader',
            'DELTA_DATASETS': 'tess-spoc-light-curves',
            'DELTA_POLL_SECONDS': '1',
            'DELTA_WORKER_ID': 'desktop-worker',
            'DELTA_WORKER_VERSION': json.loads((payload / 'sources.json').read_text())['components']['workers']['commit'],
        }
        api_env = {**env, **shared, 'DELTA_CONTRACTS_DIR': str(payload / 'components/backend/vendor/contracts')}
        worker_env = {**environment(payload, root, 'worker'), **shared,
                      'DELTA_CONTRACTS_DIR': str(payload / 'components/workers/vendor/contracts')}
        python = str(payload / 'python/bin/python3.12')
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
        listener.listen(128)
        for name, command, child_env, descriptors in (
            ('api', [python, '-s', '-m', 'uvicorn', 'delta_api.app:app', '--fd', str(listener.fileno()),
                     '--no-access-log', '--log-level', 'warning'], api_env, (listener.fileno(),)),
            ('worker', [python, '-s', '-m', 'delta_worker'], worker_env, ()),
        ):
            output = (root / f'logs/{name}.log').open('ab')
            logs.append(output)
            children.append(subprocess.Popen(command, env=child_env, stdout=output, stderr=subprocess.STDOUT,
                                             pass_fds=descriptors, start_new_session=True, cwd=root))
        listener.close()
        api_url = f'http://127.0.0.1:{port}'
        event('stage', message='Starting the API and scientific worker.')
        deadline = time.monotonic() + 45
        while not stopping:
            if any(child.poll() is not None for child in children):
                raise RuntimeError('A prototype service stopped. Inspect the workspace logs.')
            try:
                with urllib.request.urlopen(api_url + '/api/health', timeout=1) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError('The prototype API did not become ready.')
            time.sleep(0.2)
        if stopping:
            return
        record = {'api_url': api_url, 'supervisor_pid': os.getpid(), 'service_pids': [c.pid for c in children],
                  'startup_seconds': round(time.monotonic() - started, 3), 'workspace': str(root)}
        atomic_text(root / 'runtime.json', json.dumps(record) + '\n')
        event('ready', **record)
        while not stopping:
            if parent_pid is not None and os.getppid() != parent_pid:
                break
            if any(child.poll() is not None for child in children):
                raise RuntimeError('A prototype service stopped. Inspect the workspace logs.')
            time.sleep(0.25)
    finally:
        for child in reversed(children):
            stop_child(child)
        if postgres_started:
            run_logged([str(pg / 'pg_ctl'), '-D', str(root / 'database'), '-w', '-t', '20', '-m', 'fast', 'stop'],
                       env, root / 'logs/postgres-control.log', timeout=30)
        for output in logs:
            output.close()
        (root / 'runtime.json').unlink(missing_ok=True)
        lock.close()
        event('stopped')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--parent-pid', type=int)
    args = parser.parse_args()
    try:
        serve(args.payload.resolve(), args.workspace.absolute(), args.parent_pid)
    except Exception as error:
        event('error', message=str(error))
        sys.exit(1)
