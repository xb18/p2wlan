"""Offline bounds checks; these do not exercise native Windows APIs."""

import hashlib
from pathlib import Path
import tempfile
import unittest

from diagnose_console_injector import capture_records


class CaptureBoundsTests(unittest.TestCase):
    def test_retains_exact_bytes_without_modifying_original_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            raw = b'{"native_pid": 123}\n'
            (source / "target-ready.json").write_bytes(raw)
            records = capture_records(source, root / "output")
            self.assertEqual(records, [{"name": "target-ready.json", "bytes": len(raw),
                                        "sha256": hashlib.sha256(raw).hexdigest()}])
            self.assertEqual((source / "target-ready.json").read_bytes(), raw)
            self.assertEqual((root / "output/target-ready.json").read_bytes(), raw)

    def test_record_size_boundary_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "injector.json").write_bytes(b"{}" + b" " * 16382)
            self.assertEqual(capture_records(source, root / "accepted")[0]["bytes"], 16384)
            (source / "injector.json").write_bytes(b"{}" + b" " * 16383)
            with self.assertRaisesRegex(ValueError, "exceeds 16384"):
                capture_records(source, root / "rejected")
            self.assertFalse((root / "rejected/injector.json").exists())

    def test_excess_phase_records_are_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            phases = source / "injector.json.diagnostic"
            phases.mkdir(parents=True)
            for number in range(13):
                (phases / f"phase-{number:02}.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "count exceeds 12"):
                capture_records(source, root / "output")
            self.assertEqual(list((root / "output").iterdir()), [])

    def test_directory_cannot_be_copied_as_a_native_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            (source / "injector.json").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                capture_records(source, root / "output")
            self.assertFalse((root / "output/injector.json").exists())


if __name__ == "__main__":
    unittest.main()
