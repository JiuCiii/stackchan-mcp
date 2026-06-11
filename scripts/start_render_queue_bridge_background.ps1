$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repo ".venv\Scripts\python.exe"
$logDir = Join-Path $repo ".logs"
$pidFile = Join-Path $logDir "render_queue_bridge.pid"
$stdout = Join-Path $logDir "render_queue_bridge.out.log"
$stderr = Join-Path $logDir "render_queue_bridge.err.log"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python environment not found: $python"
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    $existingPid = [int](Get-Content -LiteralPath $pidFile -Raw)
    if (Get-Process -Id $existingPid -ErrorAction SilentlyContinue) {
        Write-Output "Stack Chan queue bridge already running (PID $existingPid)."
        exit 0
    }
}

$process = Start-Process `
    -FilePath $python `
    -ArgumentList "-m", "mcp_server.render_queue_bridge" `
    -WorkingDirectory $repo `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

Set-Content -LiteralPath $pidFile -Value $process.Id -Encoding Ascii
Start-Sleep -Seconds 3

if ($process.HasExited) {
    throw "Stack Chan queue bridge exited with code $($process.ExitCode). See $stderr"
}

Write-Output "Stack Chan queue bridge started (PID $($process.Id))."
