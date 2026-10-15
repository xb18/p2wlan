param([Parameter(Mandatory = $true)][string]$OutputPath)
$ErrorActionPreference = 'Stop'

# Readback diagnostics on owned loopback sockets only. No machine settings,
# production socket, Required gate or performance result is changed here.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class P2WlanProbeOptions {
    [DllImport("Ws2_32.dll")]
    public static extern int setsockopt(IntPtr socket, int level, int name, ref int value, int length);
    [DllImport("Ws2_32.dll")]
    public static extern int getsockopt(IntPtr socket, int level, int name, out int value, ref int length);
    [DllImport("Ws2_32.dll")]
    public static extern int WSAGetLastError();
}
'@

function Read-ProbeOption($Socket, [int]$Level, [int]$Name) {
    [int]$value = 0
    [int]$length = 4
    $result = [P2WlanProbeOptions]::getsockopt($Socket.Handle, $Level, $Name, [ref]$value, [ref]$length)
    $errorCode = if ($result -eq 0) { 0 } else { [P2WlanProbeOptions]::WSAGetLastError() }
    return [ordered]@{ result = $result; error = $errorCode; value = $value; length = $length }
}

$rows = [System.Collections.Generic.List[object]]::new()
$sequences = [ordered]@{
    dontfrag_then_probe = @(@{ name = 14; value = 1 }, @{ name = 71; value = 3 })
    probe_then_dontfrag_then_do = @(@{ name = 71; value = 3 }, @{ name = 14; value = 1 }, @{ name = 71; value = 1 })
    probe_only = @(@{ name = 71; value = 3 })
}
foreach ($family in @('InterNetwork', 'InterNetworkV6')) {
    $isV6 = $family -eq 'InterNetworkV6'
    $level = if ($isV6) { 41 } else { 0 }
    $address = if ($isV6) { [System.Net.IPAddress]::IPv6Loopback } else { [System.Net.IPAddress]::Loopback }
    foreach ($sequence in $sequences.GetEnumerator()) {
        $socket = [System.Net.Sockets.Socket]::new(
            [System.Net.Sockets.AddressFamily]::$family,
            [System.Net.Sockets.SocketType]::Dgram,
            [System.Net.Sockets.ProtocolType]::Udp)
        try {
            if ($isV6) { $socket.DualMode = $false }
            $socket.Bind([System.Net.IPEndPoint]::new($address, 0))
            $rows.Add([ordered]@{
                family = $family; sequence = $sequence.Key; stage = 'initial';
                dontfrag = (Read-ProbeOption $socket $level 14);
                mtu_discover = (Read-ProbeOption $socket $level 71)
            })
            foreach ($operation in $sequence.Value) {
                [int]$name = $operation.name
                [int]$value = $operation.value
                $result = [P2WlanProbeOptions]::setsockopt($socket.Handle, $level, $name, [ref]$value, 4)
                $errorCode = if ($result -eq 0) { 0 } else { [P2WlanProbeOptions]::WSAGetLastError() }
                $rows.Add([ordered]@{
                    family = $family; sequence = $sequence.Key; stage = 'after_set';
                    option = $name; requested = $value; set_result = $result; set_error = $errorCode;
                    dontfrag = (Read-ProbeOption $socket $level 14);
                    mtu_discover = (Read-ProbeOption $socket $level 71)
                })
            }
        } finally {
            $socket.Dispose()
        }
    }
}
$record = [ordered]@{
    schema_version = 1; scope = 'isolated_owned_Windows_socket_option_readback';
    source_head = (git rev-parse HEAD).Trim(); os = [System.Environment]::OSVersion.VersionString;
    production_gate_credit = $false; real_network_or_PMTU_cache_reproduction = $false;
    option_numbers = [ordered]@{ dontfrag = 14; mtu_discover = 71; do = 1; probe = 3 };
    all_owned_sockets_disposed = $true; observations = $rows.ToArray()
}
$record | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 $OutputPath
Write-Output 'Completed owned Windows socket option observations; no product gate credit.'
