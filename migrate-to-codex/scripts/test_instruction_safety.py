import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from cli import convert_instructions, write_artifact
from migrate.common import ScopePaths, PlannedArtifact, SourceSymlink, GeneratedText

class InstructionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def convert(self):
        return convert_instructions(ScopePaths(self.root, False))
    def link(self, source, target):
        try:
            source.symlink_to(target)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account cannot create real symlinks')
            raise
    def test_existing_shared_link_preserved_on_repeat(self):
        agents = self.root / "AGENTS.md"
        agents.write_text("Shared instructions", encoding="utf-8")
        claude = self.root / "CLAUDE.md"
        self.link(claude, "AGENTS.md")
        for _ in range(2):
            self.assertFalse(self.convert().artifacts)
            self.assertTrue(claude.is_symlink())
            self.assertFalse(agents.is_symlink())
            self.assertEqual(agents.read_text(), "Shared instructions")
    def test_distinct_instructions_preserved_for_merge(self):
        (self.root / "AGENTS.md").write_text("Codex instructions")
        (self.root / "CLAUDE.md").write_text("Additional Claude instructions")
        result = self.convert()
        self.assertFalse(result.artifacts)
        self.assertEqual(result.report_items[0].status, "manual_fix_required")
        self.assertEqual((self.root / "AGENTS.md").read_text(), "Codex instructions")
    def test_normal_conversion_and_repeat(self):
        (self.root / "CLAUDE.md").write_text("Shared instructions")
        for artifact in self.convert().artifacts:
            write_artifact(artifact, self.root)
        self.assertEqual((self.root / "AGENTS.md").read_text(), "Shared instructions")
        self.assertFalse(self.convert().artifacts)
    def test_broken_link(self):
        self.link(self.root / "CLAUDE.md", "missing.md")
        with self.assertRaises(ValueError):
            self.convert()
        self.assertTrue((self.root / "CLAUDE.md").is_symlink())
    def test_circular_links(self):
        self.link(self.root / "CLAUDE.md", "AGENTS.md")
        self.link(self.root / "AGENTS.md", "CLAUDE.md")
        with self.assertRaises(ValueError):
            self.convert()
    def test_writer_does_not_reverse_alias(self):
        agents = self.root / "AGENTS.md"
        agents.write_text("Canonical")
        claude = self.root / "CLAUDE.md"
        self.link(claude, "AGENTS.md")
        write_artifact(PlannedArtifact(relative_path=Path("AGENTS.md"), payload=SourceSymlink(claude)), self.root)
        self.assertFalse(agents.is_symlink())
        self.assertEqual(agents.read_text(), "Canonical")
    def test_writer_refuses_overwrite(self):
        (self.root / "AGENTS.md").write_text("Existing")
        artifact = PlannedArtifact(relative_path=Path("AGENTS.md"), payload=GeneratedText("Replacement"))
        with self.assertRaises(ValueError):
            write_artifact(artifact, self.root)
        self.assertEqual((self.root / "AGENTS.md").read_text(), "Existing")

    def test_same_file_alias_preserved(self):
        agents = self.root / "AGENTS.md"
        agents.write_text("Canonical")
        claude = self.root / "CLAUDE.md"
        claude.hardlink_to(agents)
        for _ in range(2):
            self.assertFalse(self.convert().artifacts)
            write_artifact(PlannedArtifact(relative_path=Path("AGENTS.md"), payload=SourceSymlink(claude)), self.root)
            self.assertTrue(agents.samefile(claude))
            self.assertEqual(agents.read_text(), "Canonical")

    def test_invalid_link_detection_with_simulated_filesystem(self):
        for failure in (FileNotFoundError(), RuntimeError('Symlink loop')):
            with patch.object(Path, 'is_symlink', return_value=True), patch.object(Path, 'resolve', side_effect=failure):
                with self.assertRaises(ValueError):
                    self.convert()

if __name__ == "__main__":
    unittest.main()
