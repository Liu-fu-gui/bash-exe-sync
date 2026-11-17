import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'sync.sh'
BASH = 'C:/Program Files/Git/bin/bash.exe' if os.name == 'nt' else 'bash'


def run(*args, check=True):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=check)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.git'
        self.target = self.root / 'target.git'
        self.work = self.root / 'work'
        for repo in (self.source, self.target):
            run('git', 'init', '--bare', '--initial-branch=main', str(repo))
        run('git', 'init', '--initial-branch=main', str(self.work))
        self.git('config', 'user.name', 'Backup Test')
        self.git('config', 'user.email', 'backup@example.invalid')
        self.git('commit', '--allow-empty', '-m', 'initial')
        self.first = self.git('rev-parse', 'HEAD').stdout.strip()
        self.git('remote', 'add', 'origin', str(self.source))
        self.git('branch', 'feature')
        self.git('tag', '-a', 'v1', '-m', 'annotated tag')
        self.git('push', 'origin', '--all')
        self.git('push', 'origin', '--tags')

    def git(self, *args):
        return run('git', '-C', str(self.work), *args)

    def refs(self, path):
        output = run('git', 'ls-remote', '--refs', str(path)).stdout
        return dict(line.split()[::-1] for line in output.splitlines())

    def sync(self, source=None, check=True):
        return run(BASH, SCRIPT.as_posix(), Path(source or self.source).as_posix(),
                   self.target.as_posix(), check=check)

    def test_copies_all_refs_history_and_skips_no_change(self):
        self.sync()
        self.assertEqual(self.refs(self.source), self.refs(self.target))
        self.git('commit', '--allow-empty', '-m', 'next')
        self.git('push', 'origin', 'main')
        self.sync()
        self.assertEqual(self.refs(self.source), self.refs(self.target))
        self.assertEqual(run('git', '--git-dir', str(self.target),
                             'rev-list', '--count', 'main').stdout.strip(), '2')
        self.assertIn('Already up to date', self.sync().stdout)

    def test_deleted_upstream_refs_remain_in_backup(self):
        self.sync()
        before = self.refs(self.target)
        self.git('push', 'origin', '--delete', 'feature', 'v1')
        self.sync()
        self.assertEqual(before, self.refs(self.target))

    def test_missing_and_empty_upstream_do_not_change_backup(self):
        self.sync()
        before = self.refs(self.target)
        missing = self.sync(self.root / 'missing.git', check=False)
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(before, self.refs(self.target))
        empty = self.root / 'empty.git'
        run('git', 'init', '--bare', str(empty))
        self.assertNotEqual(self.sync(empty, check=False).returncode, 0)
        self.assertEqual(before, self.refs(self.target))

    def test_force_updates_preserve_previous_objects(self):
        self.git('commit', '--allow-empty', '-m', 'old tip')
        old_tip = self.git('rev-parse', 'HEAD').stdout.strip()
        self.git('push', 'origin', 'main')
        self.sync()
        old_tag = self.refs(self.target)['refs/tags/v1']
        self.git('reset', '--hard', self.first)
        self.git('commit', '--allow-empty', '-m', 'replacement')
        self.git('tag', '-f', '-a', 'v1', '-m', 'moved tag')
        self.git('push', '--force', 'origin', 'main', 'v1')
        self.sync()
        target = self.refs(self.target)
        for ref, sha in self.refs(self.source).items():
            self.assertEqual(sha, target[ref])
        self.assertEqual(old_tip, target['refs/tags/__backup_history/' + old_tip])
        self.assertEqual(old_tag, target['refs/tags/__backup_history/' + old_tag])

    def test_reserved_archive_namespace_fails_without_changes(self):
        self.sync()
        before = self.refs(self.target)
        self.git('tag', '__backup_history/conflict')
        self.git('push', 'origin', '--tags')
        result = self.sync(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.refs(self.target))


if __name__ == '__main__':
    unittest.main()
