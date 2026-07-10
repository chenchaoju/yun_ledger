param(
    [int[]]$Ports = @(8024, 5173, 8023)
)

$ErrorActionPreference = "Stop"

foreach ($port in $Ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $processId = $connection.OwningProcess
        if ($processId -and $processId -ne 0) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped process $processId on port $port"
        }
    }
}

