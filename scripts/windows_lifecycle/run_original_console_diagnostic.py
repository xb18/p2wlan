#!/usr/bin/env python3
"""Diagnostic only: run unchanged Windows console controls on an exact candidate."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest import mock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--dispatcher-sha', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise RuntimeError('native Windows is required')
    candidate = args.candidate.resolve()
    out = args.out.resolve()
    out.mkdir(exist_ok=False)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=candidate, text=True).strip()
    if actual != args.expected_sha or subprocess.check_output(['git', 'status', '--porcelain'], cwd=candidate):
        raise RuntimeError('candidate is not the exact clean source')
    files = [candidate / 'scripts/windows_lifecycle' / name for name in (
        'send_console_ctrl_c.ps1', 'test_console_ctrl_c.py',
        'test_aggregate_evidence.py', 'aggregate_evidence.py', 'windows_lifecycle_acceptance.ps1')]
    hashes = {str(path.relative_to(candidate)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    original_which = shutil.which
    core = original_which('pwsh')
    desktop = original_which('powershell.exe')
    if not core or not desktop:
        raise RuntimeError('both original Core and supplemental Desktop interpreters required')
    os.chdir(candidate)
    sys.path.insert(0, str(candidate / 'scripts/windows_lifecycle'))
    import test_console_ctrl_c as controls
    original = controls._injector_diagnostic
    label = 'core'
    captured = {}

    def capture(*values, **keywords):
        details = original(*values, **keywords)
        if details['target_ready'].get('native_pid') is not None:
            if label in captured:
                raise RuntimeError('more than one native control in one interpreter')
            raw = json.dumps(details, sort_keys=True, indent=2).encode()
            if len(raw) > 65536:
                raise RuntimeError('actual native diagnostic exceeded fixed capture bound')
            (out / ('original-native-' + label + '.json')).write_bytes(raw)
            captured[label] = details
        return details

    controls._injector_diagnostic = capture
    suite = unittest.defaultTestLoader.discover(str(candidate / 'scripts/windows_lifecycle'), pattern='test_*.py')
    if suite.countTestCases() != 18:
        raise RuntimeError('original suite must remain the same 18 cases')
    outcomes = {}

    def execute(name, selected):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = unittest.TextTestRunner(verbosity=2).run(selected)
        for suffix, value in [('stdout', stdout.getvalue()), ('stderr', stderr.getvalue())]:
            if len(value.encode()) > 262144:
                raise RuntimeError('unit output exceeded fixed bound')
            (out / (name + '.' + suffix + '.log')).write_text(value)
        outcomes[name] = {'executed': result.testsRun, 'failed': len(result.failures),
                          'errors': len(result.errors), 'skipped': len(result.skipped),
                          'successful': result.wasSuccessful()}

    execute('original-core18', suite)
    label = 'desktop'
    # Python inherits Core's module paths. Desktop must construct its own paths;
    # restrict this environment correction to this owned supplemental variant.
    desktop_env = {key: value for key, value in os.environ.items() if key.upper() != 'PSMODULEPATH'}
    with mock.patch.dict(os.environ, desktop_env, clear=True), mock.patch.object(
            controls.shutil, 'which', side_effect=lambda name: desktop if name == 'pwsh' else original_which(name)):
        execute('supplemental-desktop-original-negative', unittest.TestSuite([
            controls.ConsoleCtrlCInjectorTests('test_target_without_console_cannot_report_a_successful_broadcast')]))
    inspector = Path(__file__).with_name('inspect_console_helper_abi.ps1').resolve()
    abi = {}
    for name, executable in [('core', core), ('desktop', desktop)]:
        output = out / ('native-abi-' + name + '.json')
        process = subprocess.run([executable, '-NoLogo', '-NoProfile', '-NonInteractive',
                                  '-ExecutionPolicy', 'Bypass', '-File', str(inspector),
                                  '-InjectorPath', str(files[0]), '-OutputPath', str(output)],
                                 capture_output=True, timeout=30,
                                 env=desktop_env if name == 'desktop' else None)
        (out / ('abi-' + name + '.stdout.log')).write_bytes(process.stdout)
        (out / ('abi-' + name + '.stderr.log')).write_bytes(process.stderr)
        abi[name] = process.returncode == 0 and output.exists()
    # Observe the real Desktop ACL command identity before deciding which
    # module-location invariant is valid for the GUI's owned child process.
    module_script = r"""
$ErrorActionPreference = 'Stop'
$command = Get-Command Get-Acl -ErrorAction Stop
[ordered]@{
    edition = $PSVersionTable.PSEdition
    version = $PSVersionTable.PSVersion.ToString()
    ps_home = $PSHOME
    command_type = $command.CommandType.ToString()
    module_name = $command.ModuleName
    module_base = $command.Module.ModuleBase
    module_path = $command.Module.Path
    assembly_name = $command.ImplementingType.Assembly.FullName
    assembly_location = $command.ImplementingType.Assembly.Location
    assembly_runtime = $command.ImplementingType.Assembly.ImageRuntimeVersion
    expected_manifest_directory = Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security'
} | ConvertTo-Json -Depth 4
"""
    module = subprocess.run([desktop, '-NoLogo', '-NoProfile', '-NonInteractive',
                             '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass',
                             '-Command', module_script], capture_output=True,
                            env=desktop_env, timeout=10)
    if len(module.stdout) + len(module.stderr) > 65536:
        raise RuntimeError('ACL module identity exceeded fixed capture bound')
    (out / 'desktop-acl-module.stdout.json').write_bytes(module.stdout)
    (out / 'desktop-acl-module.stderr.log').write_bytes(module.stderr)
    if hashes != {str(path.relative_to(candidate)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}:
        raise RuntimeError('candidate controls changed during execution')
    success = (all(value['successful'] and value['skipped'] == 0 for value in outcomes.values())
               and set(captured) == {'core', 'desktop'} and all(abi.values())
               and all(value['injector_record']['native_error_code'] == 6 for value in captured.values()))
    report = {'schema_version': 1, 'source_head_sha': actual, 'dispatcher_sha': args.dispatcher_sha,
              'python': sys.version, 'platform': sys.platform, 'source_files': hashes,
              'original_core_cases': 18, 'supplemental_desktop_same_native_case': 1,
              'outcomes': outcomes, 'native_detail_interpreters': sorted(captured),
              'actual_abi_verified': abi, 'diagnostic_only_no_Required_credit': True,
              'supplemental_desktop_child_PSModulePath_removed': True,
              'supplemental_desktop_ACL_identity_returncode': module.returncode,
              'original10_second_deadline_and_all_assertions_unchanged': True,
              'result': 'pass' if success else 'fail'}
    (out / 'manifest.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
