#!/usr/bin/env python3
"""Keep bounded records from the unchanged native console test's cleanup.

This manual diagnostic never publishes Required credit. The original test owns
its child processes, assertions, ten-second wait and three-second cleanup.
"""

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def capture_records(directory, destination):
    directory = Path(directory)
    destination.mkdir()
    phases = list(itertools.islice((directory / "injector.json.diagnostic").glob("phase-*.json"), 13))
    if len(phases) > 12:
        raise ValueError("phase record count exceeds 12")
    records = []
    for source in [directory / "target-ready.json", directory / "injector.json", *phases]:
        if not source.exists():
            continue
        if source.is_symlink() or not stat.S_ISREG(source.stat().st_mode):
            raise ValueError("diagnostic record is not a regular file")
        with source.open("rb") as stream:
            raw = stream.read(16385)
        if len(raw) > 16384:
            raise ValueError("diagnostic record exceeds 16384 bytes")
        json.loads(raw.decode("utf-8-sig"))
        target = destination / source.name
        with target.open("xb") as stream:
            stream.write(raw)
        records.append({"name": source.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cases", type=int, choices=[1, 4], default=1)
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("native Windows is required; a skipped test is not diagnostic proof")
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        parser.error("source-sha must be a complete lowercase commit SHA")
    root = args.source.resolve()
    control = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2], text=True).strip()
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if actual != args.source_sha:
        parser.error("source checkout does not match the requested commit")
    args.output.mkdir(parents=True, exist_ok=False)
    paths = [root / "scripts/windows_lifecycle" / name for name in
             ["test_console_ctrl_c.py", "send_console_ctrl_c.ps1"]]
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    spec = importlib.util.spec_from_file_location("original_console_injector", paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_temporary = tempfile.TemporaryDirectory
    captures = []
    capture_errors = []
    capture_index = 0

    class RetainedTemporaryDirectory(original_temporary):
        def cleanup(self):
            nonlocal capture_index
            if not getattr(self, "diagnostic_captured", False):
                self.diagnostic_captured = True
                capture_index += 1
                try:
                    captures.append(capture_records(self.name, args.output / f"records-{capture_index}"))
                except (OSError, ValueError, UnicodeError) as error:
                    capture_errors.append(type(error).__name__)
            super().cleanup()

    cases = [module.ConsoleCtrlCInjectorTests(
        "test_target_without_console_cannot_report_a_successful_broadcast") for _ in range(args.cases)]
    with (args.output / "original-test.log").open("x", encoding="utf-8") as stream:
        with patch.object(module, "tempfile", SimpleNamespace(TemporaryDirectory=RetainedTemporaryDirectory)):
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite(cases))
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    unchanged = before == after
    valid = result.testsRun == args.cases and not result.skipped and unchanged and not capture_errors and len(captures) == args.cases
    receipt = {
        "diagnostic_only": True, "required_gate_published": False,
        "diagnostic_control_sha": control,
        "diagnostic_driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_head": actual, "original_source_files": before,
        "source_unchanged_after_test": unchanged, "python": sys.version,
        "original_test_count": result.testsRun, "original_failures": len(result.failures),
        "fixed_case_count": args.cases, "stop_on_first_pass": False,
        "original_errors": len(result.errors), "original_skips": len(result.skipped),
        "original_test_passed": result.wasSuccessful(), "capture_valid": valid,
        "original_injector_wait_seconds": 10, "original_cleanup_wait_seconds": 3,
        "records": captures, "capture_errors": capture_errors,
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if valid and result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
