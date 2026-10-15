[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InjectorPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $InjectorPath, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw 'injector source did not parse' }
$factory = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Initialize-CtrlCNativeMethods'
}, $true)
if ($null -eq $factory) { throw 'candidate native import factory missing' }
# Execute only the import definitions, never the injector or its target action.
& $factory.Body.GetScriptBlock()
$native = 'P2WlanCtrlCInjector' -as [Type]
if ($null -eq $native) { throw 'native import type was not created' }
$expected = @{
    AttachConsole = @('System.UInt32')
    FreeConsole = @()
    GenerateConsoleCtrlEvent = @('System.UInt32', 'System.UInt32')
    SetConsoleCtrlHandler = @('System.IntPtr', 'System.Boolean')
}
$records = @()
foreach ($name in @('AttachConsole', 'FreeConsole', 'GenerateConsoleCtrlEvent', 'SetConsoleCtrlHandler')) {
    $method = $native.GetMethod($name)
    if ($null -eq $method) { throw "native method absent: $name" }
    $imports = @($method.GetCustomAttributes([System.Runtime.InteropServices.DllImportAttribute], $false))
    if ($imports.Count -ne 1) { throw "native import identity missing: $name" }
    $import = $imports[0]
    $parameters = @($method.GetParameters() | ForEach-Object { $_.ParameterType.FullName })
    if ($import.Value -cne 'kernel32.dll' -or $import.EntryPoint -cne $name -or
        -not $import.SetLastError -or -not $import.PreserveSig -or
        $import.CallingConvention -ne [System.Runtime.InteropServices.CallingConvention]::Winapi -or
        $method.ReturnType -ne [bool] -or
        (($parameters -join ',') -cne ($expected[$name] -join ','))) {
        throw "native ABI changed: $name"
    }
    $records += [ordered]@{
        method = $name; dll = $import.Value; entry_point = $import.EntryPoint
        set_last_error = $import.SetLastError; preserve_sig = $import.PreserveSig
        calling_convention = $import.CallingConvention.ToString()
        return_type = $method.ReturnType.FullName; parameters = $parameters
    }
}
[ordered]@{
    schema_version = 1; powershell = $PSVersionTable.PSVersion.ToString()
    edition = $PSVersionTable.PSEdition; source_sha256 = (Get-FileHash $InjectorPath -Algorithm SHA256).Hash.ToLowerInvariant()
    executed_target_action = $false; methods = $records
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
