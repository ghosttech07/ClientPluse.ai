$taskRoot = $PSScriptRoot
$taskPidPath = Join-Path $taskRoot 'data\logs\processes.json'
# Python environment launchers can spawn child interpreters; stop verified project commands too.
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($taskRoot) -and $_.CommandLine -match '-m (uvicorn services\.api\.main:app|services\.worker\.main)|next\\dist\\bin\\next' } | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
if (Test-Path -LiteralPath $taskPidPath) { Remove-Item -LiteralPath $taskPidPath }
Write-Host 'Stopped ClientPulse project services.'
