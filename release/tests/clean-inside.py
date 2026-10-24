"""Execute within the clean filesystem. No repository paths are accessible here."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

app = Path('/app/resources/app')
report = {'system_runtimes': {name: Path('/usr/bin', name).exists() for name in ('python3', 'node', 'psql', 'postgres', 'docker', 'kubectl')},
          'host_home_visible': Path('/home/richardtidwell').exists(), 'private_repositories_visible': Path('/build/sources/datasets').exists()}
assert not any(report['system_runtimes'].values())
assert not report['host_home_visible'] and not report['private_repositories_visible']
Path('/tmp/runtime').mkdir(mode=0o700)
Path('/work/environment.json').write_text(json.dumps(report, indent=2) + '\n')
subprocess.run([sys.executable, '-s', str(app / 'checks/smoke.py'), '--app', str(app),
                '--workspace', '/work/runtime-workspace', '--output', '/work/runtime-check'], check=True)
with open('/work/xvfb.log', 'wb') as log:
    display = subprocess.Popen(['/usr/bin/Xvfb', ':99', '-screen', '0', '1440x1000x24', '-nolisten', 'tcp'],
                               stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 10
        while not Path('/tmp/.X11-unix/X99').exists():
            if time.monotonic() > deadline or display.poll() is not None:
                raise RuntimeError('The isolated display did not start.')
            time.sleep(0.1)
        with open('/work/desktop.log', 'wb') as desktop_log:
            subprocess.run(['/app/delta-observatory', '--workspace=/work/runtime-workspace', '--headless',
                            '--smoke-output=/work/desktop-check'], check=True, stdout=desktop_log,
                           stderr=subprocess.STDOUT, timeout=90)
        desktop = json.loads(Path('/work/desktop-check/desktop.json').read_text())
        assert desktop['ready'] and desktop['sandbox'] and desktop['fontsReady'] and desktop['plotsReady'] and not desktop['consoleErrors']
    finally:
        display.terminate()
        display.wait(timeout=10)
