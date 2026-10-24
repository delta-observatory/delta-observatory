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
agent_environment = dict(os.environ, PYTHONPATH=str(app/'payload/components/agents'),
                         LD_LIBRARY_PATH=str(app/'payload/host-lib'), PYTHONDONTWRITEBYTECODE='1')
agent_check = subprocess.run([sys.executable, '-s', str(app/'checks/check_managed_isolation.py'),
                             '--runtime', str(app/'payload/codex'), '--bwrap', str(app/'payload/host-bin/bwrap')],
                            env=agent_environment, capture_output=True, text=True, timeout=90)
Path('/work/agent-isolation.log').write_text(agent_check.stdout + agent_check.stderr)
agent_check.check_returncode()
Path('/work/agent-isolation.json').write_text(agent_check.stdout)
claude_check = subprocess.run([sys.executable, '-s', str(app/'checks/check_claude_isolation.py'),
                             '--runtime', str(app/'payload/claude'), '--bwrap', str(app/'payload/host-bin/bwrap')],
                            env=agent_environment, capture_output=True, text=True, timeout=90)
Path('/work/claude-isolation.log').write_text(claude_check.stdout + claude_check.stderr)
claude_check.check_returncode()
Path('/work/claude-isolation.json').write_text(claude_check.stdout)
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
        with open('/work/product-desktop.log', 'wb') as desktop_log:
            subprocess.run(['/app/delta-observatory', '--workspace=/work/runtime-workspace', '--headless',
                            '--product-smoke-output=/work/product-desktop-check'], check=True, stdout=desktop_log,
                           stderr=subprocess.STDOUT, timeout=120)
        product = json.loads(Path('/work/product-desktop-check/product-ui.json').read_text())
        assert product['status'] == 'passed'
    finally:
        display.terminate()
        display.wait(timeout=10)
