$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskLogs = Join-Path $taskRoot 'data\logs'
New-Item -ItemType Directory -Force -Path $taskLogs | Out-Null
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Install the Python environment first. See README.md.' }
$taskPorts = @(3000,8000)
foreach ($taskPort in $taskPorts) { if (Get-NetTCPConnection -LocalPort $taskPort -State Listen -ErrorAction SilentlyContinue) { throw "Port $taskPort is already in use. Stop the existing service first." } }
$taskApi = Start-Process -FilePath $taskPython -ArgumentList '-m','uvicorn','services.api.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskLogs 'api.log') -RedirectStandardError (Join-Path $taskLogs 'api-error.log')
$taskWorker = Start-Process -FilePath $taskPython -ArgumentList '-u','-m','services.worker.main' -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskLogs 'worker.log') -RedirectStandardError (Join-Path $taskLogs 'worker-error.log')
$taskNode = (Get-Command node).Source
$taskNext = Join-Path $taskRoot 'node_modules\next\dist\bin\next'
$taskWeb = Start-Process -FilePath $taskNode -ArgumentList ('"' + $taskNext + '"'),'dev','--webpack','--hostname','127.0.0.1' -WorkingDirectory (Join-Path $taskRoot 'apps\web') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskLogs 'web.log') -RedirectStandardError (Join-Path $taskLogs 'web-error.log')
@{ api=$taskApi.Id; worker=$taskWorker.Id; web=$taskWeb.Id } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskLogs 'processes.json')
Write-Host 'ClientPulse AI is starting at http://127.0.0.1:3000. Logs: data/logs. Stop with ./stop.ps1.'
