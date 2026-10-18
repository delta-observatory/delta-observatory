"""Tests for scripts/components.py. Run: python3 -m unittest scripts/test_components.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('components.py')


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def make_repo(path, files):
    path.mkdir(parents=True)
    git(path, 'init', '-q', '-b', 'main')
    git(path, 'config', 'user.email', 'test@example.invalid')
    git(path, 'config', 'user.name', 'Test')
    commits = []
    for name, text in files:
        (path/name).write_text(text)
        git(path, 'add', name)
        git(path, 'commit', '-q', '-m', f'add {name}')
        commits.append(git(path, 'rev-parse', 'HEAD'))
    return commits


def run(*args):
    return subprocess.run([sys.executable, '-I', str(SCRIPT), *args], capture_output=True, text=True)


class ComponentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.source = self.tmp/'source'
        self.alpha = make_repo(self.source/'alpha', [('a.txt', '1'), ('a.txt', '2')])
        self.beta = make_repo(self.source/'beta', [('b.txt', '1')])
        self.gamma = make_repo(self.source/'gamma', [('g.txt', '1'), ('g.txt', '2')])
        self.manifest = self.tmp/'components.json'
        self.manifest.write_text(json.dumps({
            'contract': 'components/1',
            'organization': 'example',
            'components': [
                {'name': 'alpha', 'visibility': 'public', 'repository': 'https://github.com/example/alpha.git', 'commit': self.alpha[0]},
                {'name': 'beta', 'visibility': 'public', 'repository': 'https://github.com/example/beta.git', 'commit': self.beta[0]},
                {'name': 'gamma', 'visibility': 'private', 'repository': 'https://github.com/example/gamma.git'},
                {'name': 'delta', 'visibility': 'private'},
            ]}))
        self.dest = self.tmp/'checkout'
        self.dest.mkdir()

    def test_clone_checks_out_pinned_commits_and_skips_private(self):
        r = run('clone', '--manifest', str(self.manifest), '--dest', str(self.dest), '--source', str(self.source))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(git(self.dest/'alpha', 'rev-parse', 'HEAD'), self.alpha[0])
        self.assertEqual((self.dest/'alpha'/'a.txt').read_text(), '1')
        self.assertEqual(git(self.dest/'beta', 'rev-parse', 'HEAD'), self.beta[0])
        self.assertFalse((self.dest/'gamma').exists())
        self.assertIn('gamma', r.stdout)

    def test_clone_private_takes_the_default_branch_of_private_components(self):
        r = run('clone', '--manifest', str(self.manifest), '--dest', str(self.dest), '--source', str(self.source), '--private')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(git(self.dest/'gamma', 'rev-parse', 'HEAD'), self.gamma[1])
        self.assertEqual(git(self.dest/'gamma', 'branch', '--show-current'), 'main')
        self.assertEqual(git(self.dest/'alpha', 'rev-parse', 'HEAD'), self.alpha[0])
        self.assertFalse((self.dest/'delta').exists())
        self.assertIn('delta', r.stdout)

    def test_check_ignores_private_components(self):
        run('clone', '--manifest', str(self.manifest), '--dest', str(self.dest), '--source', str(self.source))
        self.assertEqual(run('check', '--manifest', str(self.manifest), '--dest', str(self.dest)).returncode, 0)

    def test_clone_latest_stays_on_main(self):
        r = run('clone', '--manifest', str(self.manifest), '--dest', str(self.dest), '--source', str(self.source), '--latest')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(git(self.dest/'alpha', 'rev-parse', 'HEAD'), self.alpha[1])
        self.assertEqual(git(self.dest/'alpha', 'branch', '--show-current'), 'main')

    def test_clone_does_not_touch_an_existing_directory(self):
        (self.dest/'alpha').mkdir()
        (self.dest/'alpha'/'keep.txt').write_text('mine')
        r = run('clone', '--manifest', str(self.manifest), '--dest', str(self.dest), '--source', str(self.source))
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.dest/'alpha'/'keep.txt').read_text(), 'mine')

    def test_check_reports_a_commit_that_differs(self):
        run('clone', '--manifest', str(self.manifest), '--dest', str(self.dest), '--source', str(self.source))
        self.assertEqual(run('check', '--manifest', str(self.manifest), '--dest', str(self.dest)).returncode, 0)
        git(self.dest/'alpha', 'checkout', '-q', self.alpha[1])
        r = run('check', '--manifest', str(self.manifest), '--dest', str(self.dest))
        self.assertEqual(r.returncode, 1)
        self.assertIn('alpha', r.stdout)

    def test_check_reports_uncommitted_changes(self):
        run('clone', '--manifest', str(self.manifest), '--dest', str(self.dest), '--source', str(self.source))
        (self.dest/'beta'/'b.txt').write_text('changed')
        r = run('check', '--manifest', str(self.manifest), '--dest', str(self.dest))
        self.assertEqual(r.returncode, 1)
        self.assertIn('uncommitted', r.stdout)

    def test_pin_writes_the_current_commits(self):
        r = run('pin', '--manifest', str(self.manifest), '--dest', str(self.source))
        self.assertEqual(r.returncode, 0, r.stderr)
        pinned = {c['name']: c.get('commit') for c in json.loads(self.manifest.read_text())['components']}
        self.assertEqual(pinned, {'alpha': self.alpha[1], 'beta': self.beta[0], 'gamma': None, 'delta': None})

    def test_pin_refuses_a_repository_with_uncommitted_changes(self):
        (self.source/'alpha'/'a.txt').write_text('dirty')
        before = self.manifest.read_text()
        r = run('pin', '--manifest', str(self.manifest), '--dest', str(self.source))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.manifest.read_text(), before)

    def test_invalid_manifest_is_refused(self):
        self.manifest.write_text(json.dumps({'contract': 'components/1', 'organization': 'example',
                                             'components': [{'name': '../escape', 'visibility': 'public',
                                                             'repository': 'https://x/y.git', 'commit': 'a'*40}]}))
        r = run('check', '--manifest', str(self.manifest), '--dest', str(self.dest))
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
