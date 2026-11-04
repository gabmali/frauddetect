$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Instale as dependências seguindo o README.' }
$taskNode = (Get-Command node -ErrorAction Stop).Source
if ([int]((& $taskNode -p 'process.versions.node.split(".")[0]')) -lt 24) {
    $taskBundledNode=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
    if (Test-Path -LiteralPath $taskBundledNode) { $taskNode=$taskBundledNode }
    else { throw 'Use Node.js 24 ou superior.' }
}
$taskFrontend = Join-Path $taskRoot 'frontend'
$taskBackendProcess = Start-Process -FilePath $taskPython -ArgumentList '-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRoot 'data/backend.log') -RedirectStandardError (Join-Path $taskRoot 'data/backend-error.log')
$taskFrontendProcess = Start-Process -FilePath $taskNode -ArgumentList 'node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5173','--strictPort' -WorkingDirectory $taskFrontend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRoot 'data/frontend.log') -RedirectStandardError (Join-Path $taskRoot 'data/frontend-error.log')
try {
    Write-Host 'FraudDetect: http://127.0.0.1:5173 — Ctrl+C para encerrar. Logs em data/.'
    while (-not $taskBackendProcess.HasExited -and -not $taskFrontendProcess.HasExited) { Start-Sleep -Seconds 1 }
} finally {
    if (-not $taskBackendProcess.HasExited) { Stop-Process -Id $taskBackendProcess.Id }
    if (-not $taskFrontendProcess.HasExited) { Stop-Process -Id $taskFrontendProcess.Id }
}
