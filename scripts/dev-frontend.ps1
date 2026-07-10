param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,
    [Parameter(Mandatory = $true)]
    [int]$BackendPort,
    [Parameter(Mandatory = $true)]
    [int]$Port
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectDir
$env:VITE_API_PROXY_TARGET = "http://127.0.0.1:$BackendPort"

$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($npm) {
    npm install
    npm run dev -- --host 0.0.0.0 --port $Port
    exit
}

$node = Get-Command node -ErrorAction SilentlyContinue
$nodePath = if ($node) { $node.Source } else { "C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\node.exe" }
$vitePath = Join-Path $ProjectDir "node_modules\vite\bin\vite.js"

if (!(Test-Path -LiteralPath $nodePath)) {
    throw "node was not found. Install Node.js or add node.exe to PATH."
}

if (!(Test-Path -LiteralPath $vitePath)) {
    throw "npm was not found and Vite was not found at $vitePath. Run npm install in this frontend directory first."
}

& $nodePath $vitePath --host 0.0.0.0 --port $Port
