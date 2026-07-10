param(
    [int]$BackendPort = 8024,
    [int]$PcPort = 5173,
    [int]$MobilePort = 8023
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Pc = Join-Path $Root "pc"
$Mobile = Join-Path $Root "mobile"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (!(Test-Path $Python)) {
    py -3 -m venv (Join-Path $Backend ".venv")
}

if (!(Test-Path (Join-Path $Backend ".env")) -and (Test-Path (Join-Path $Backend ".env.example"))) {
    Copy-Item (Join-Path $Backend ".env.example") (Join-Path $Backend ".env")
}

& $Python -m pip install -r (Join-Path $Backend "requirements.txt")
Push-Location $Backend
& $Python -m alembic upgrade head
Pop-Location

$commands = @(
    @{
        Title = "Yun Accounting Backend"
        Path = $Backend
        Command = "`"$Python`" -m uvicorn app.main:app --reload --host 127.0.0.1 --port $BackendPort"
    },
    @{
        Title = "Yun Accounting"
        Path = $Pc
        Command = "powershell -ExecutionPolicy Bypass -File '$Root\scripts\dev-frontend.ps1' -ProjectDir '$Pc' -BackendPort $BackendPort -Port $PcPort"
    },
    @{
        Title = "Yun Accounting"
        Path = $Mobile
        Command = "powershell -ExecutionPolicy Bypass -File '$Root\scripts\dev-frontend.ps1' -ProjectDir '$Mobile' -BackendPort $BackendPort -Port $MobilePort"
    }
)

foreach ($item in $commands) {
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle='$($item.Title)'; Set-Location '$($item.Path)'; $($item.Command)"
    )
}

Write-Host "Yun Accounting started:"
Write-Host "PC:       http://127.0.0.1:$PcPort/"
Write-Host "Mobile:   http://127.0.0.1:$MobilePort/mobile/"
Write-Host "Backend:  http://127.0.0.1:$BackendPort/docs"
