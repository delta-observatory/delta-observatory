"""Check link context for immutable document copies."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_workspace import markdown_source


class SnapshotLinksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.experiments = self.root/'experiments'
        self.record = self.experiments/'pilot'
        self.record.mkdir(parents=True)
        self.source = self.experiments/'PROCEDURE.md'
        self.source.write_text('# Procedure\n\n[Plan](PLAN.md)\n')
        self.copy = self.record/'procedure-snapshot.md'
        self.copy.write_bytes(self.source.read_bytes())
        self.mapping = self.record/'copied-sources.json'
        self.freeze = self.record/'freeze.json'
        self.save_mapping(self.source)

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def save_mapping(self, source):
        self.mapping.write_text(json.dumps({self.copy.name: {
            'source': str(source), 'sha256': self.digest(self.copy),
        }}))
        self.freeze.write_text(json.dumps({'files': {
            self.copy.name: self.digest(self.copy),
            'copied-sources.json': self.digest(self.mapping),
        }}))

    def test_verified_copy_uses_original_directory(self):
        self.assertEqual(markdown_source(self.copy, self.root), self.source)
        self.assertEqual(self.copy.read_bytes(), self.source.read_bytes())

    def test_current_source_can_change_after_freeze(self):
        self.source.write_text('# Current procedure\n')
        self.assertEqual(markdown_source(self.copy, self.root), self.source)
        self.assertIn('[Plan](PLAN.md)', self.copy.read_text())

    def test_changed_copy_is_rejected(self):
        self.copy.write_text('Changed frozen content\n')
        with self.assertRaisesRegex(ValueError, 'inconsistent hashes'):
            markdown_source(self.copy, self.root)

    def test_changed_mapping_is_rejected(self):
        self.mapping.write_text(self.mapping.read_text()+'\n')
        with self.assertRaisesRegex(ValueError, 'inconsistent hashes'):
            markdown_source(self.copy, self.root)

    def test_unfrozen_mapping_is_rejected(self):
        self.freeze.write_text(json.dumps({'files': {self.copy.name: self.digest(self.copy)}}))
        with self.assertRaisesRegex(ValueError, 'inconsistent hashes'):
            markdown_source(self.copy, self.root)

    def test_invalid_mapping_shape_is_rejected(self):
        self.mapping.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'must be an object'):
            markdown_source(self.copy, self.root)

    def test_external_source_keeps_local_context(self):
        self.save_mapping(self.root.parent/'external-source.md')
        self.assertEqual(markdown_source(self.copy, self.root), self.copy)

    def test_missing_workspace_source_is_rejected(self):
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, 'source path is unavailable'):
            markdown_source(self.copy, self.root)

    def test_unmapped_document_keeps_local_context(self):
        other = self.record/'README.md'
        other.write_text('[Result](result.json)\n')
        self.assertEqual(markdown_source(other, self.root), other)


if __name__ == '__main__':
    unittest.main()
