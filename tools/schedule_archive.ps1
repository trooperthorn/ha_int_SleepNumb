# Registers the nightly SleepIQ history archive task; see docs/operations.md.

param(
    [string]$Time = "03:30",
    [string]$TaskName = "SleepNumber History Archive"
)

$ErrorActionPreference = "Stop"
$wrapper = Join-Path $PSScriptRoot "archive_nightly.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$wrapper`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Nightly local backup of SleepIQ sleep history" `
    -Force | Out-Null

Write-Output "Registered '$TaskName' to run daily at $Time."
Write-Output "Create a .siq_env file (see tools\archive_nightly.ps1) to enable it."
