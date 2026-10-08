$taskPidPath = Join-Path $PSScriptRoot 'data\logs\processes.json'
if (-not (Test-Path -LiteralPath $taskPidPath)) { Write-Host 'No saved Evidence.ai processes.'; exit }
$taskSaved = Get-Content -LiteralPath $taskPidPath | ConvertFrom-Json
foreach ($taskProperty in $taskSaved.PSObject.Properties) {
    $taskPid = [int]$taskProperty.Value
    $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $taskPid" -ErrorAction SilentlyContinue
    if ($taskProcess -and $taskProcess.CommandLine -and ($taskProcess.CommandLine -match 'services\.api\.main|services\.worker\.main|next\\dist\\bin\\next')) { Stop-Process -Id $taskPid -ErrorAction SilentlyContinue }
}
Remove-Item -LiteralPath $taskPidPath
Write-Host 'Stopped the saved Evidence.ai processes.'
