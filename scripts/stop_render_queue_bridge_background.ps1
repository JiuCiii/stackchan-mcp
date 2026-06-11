$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pidFile = Join-Path $repo ".logs\render_queue_bridge.pid"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Output "Stack Chan queue bridge is not running."
    exit 0
}

$bridgePid = [int](Get-Content -LiteralPath $pidFile -Raw)
Stop-Process -Id $bridgePid -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
Write-Output "Stack Chan queue bridge stopped."
