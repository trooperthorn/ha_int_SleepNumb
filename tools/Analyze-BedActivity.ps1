<#
.SYNOPSIS
    Detects likely in-bed activity events (exercise / intimacy) from SleepNumber
    cloud history JSON exports and reports duration, frequency, and gap metrics.

.DESCRIPTION
    Expects a history folder containing one subfolder per sleeper, named
    "<Name>_<sleeperId>", each holding monthly JSON files (e.g. 2020-03.json)
    in the SleepIQ sleepData format.

    Formula:
      Baseline HR   = median avgHeartRate of that sleeper's long sessions (> 4 h)
      Solo event    = session <= MaxEventMinutes AND
                      avgHeartRate >= baseline + HrMargin AND
                      restless/total >= RestlessFraction
      Tier A (joint)= short sessions of two sleepers overlapping in time (any HR)
      Tier B        = Tier A where at least one sleeper meets the solo-event HR/restless bar
      Tier C        = Tier A where BOTH sleepers meet it

.EXAMPLE
    .\Analyze-BedActivity.ps1 -HistoryPath "C:\Users\sean.LAB\Desktop\Claude\sleepiq\history"
#>
param(
    [string]$HistoryPath      = "C:\Users\sean.LAB\Desktop\Claude\sleepiq\history",
    [int]   $MaxEventMinutes  = 90,
    [int]   $HrMargin         = 12,
    [double]$RestlessFraction = 0.5
)

$ErrorActionPreference = 'Stop'

function Get-Median {
    param([double[]]$Values)
    $s = @($Values | Sort-Object)
    $n = $s.Count
    if ($n -eq 0) { return $null }
    if ($n % 2 -eq 1) { return $s[($n - 1) / 2] }
    return ($s[$n / 2 - 1] + $s[$n / 2]) / 2
}

# ---------------------------------------------------------------- load sessions
$sleepers = @{}   # name -> list of session objects
foreach ($dir in Get-ChildItem -Path $HistoryPath -Directory) {
    $name = ($dir.Name -split '_')[0]
    $list = New-Object System.Collections.Generic.List[object]
    foreach ($file in Get-ChildItem -Path $dir.FullName -Filter '*.json') {
        $doc = Get-Content -Raw -Path $file.FullName | ConvertFrom-Json
        foreach ($day in $doc.sleepData) {
            foreach ($s in $day.sessions) {
                if ($s.isHidden) { continue }
                $tot = [int]$s.totalSleepSessionTime
                if ($tot -le 0) { continue }
                $list.Add([pscustomobject]@{
                    Sleeper  = $name
                    Start    = [datetime]$s.startDate
                    End      = [datetime]$s.endDate
                    TotalSec = $tot
                    Hr       = [int]$s.avgHeartRate
                    Restless = [int]$s.restless
                })
            }
        }
    }
    $sleepers[$name] = @($list | Sort-Object Start)
    Write-Host ("Loaded {0}: {1} sessions ({2:d} files)" -f $name, $list.Count,
        (Get-ChildItem -Path $dir.FullName -Filter '*.json').Count)
}

# ---------------------------------------------------------------- baselines
$baseline = @{}
foreach ($name in $sleepers.Keys) {
    $hrs = @($sleepers[$name] | Where-Object { $_.TotalSec -gt 14400 -and $_.Hr -gt 0 } |
              ForEach-Object { [double]$_.Hr })
    $baseline[$name] = Get-Median $hrs
    Write-Host ("Baseline HR {0}: {1}" -f $name, $baseline[$name])
}

$maxSec = $MaxEventMinutes * 60

function Test-Elevated {
    param($Session)
    $base = $baseline[$Session.Sleeper]
    return ($Session.Hr -gt 0 -and
            $Session.Hr -ge ($base + $HrMargin) -and
            ($Session.Restless / $Session.TotalSec) -ge $RestlessFraction)
}

# ---------------------------------------------------------------- metrics
function Show-Metrics {
    param([string]$Label, [object[]]$Events)
    Write-Host ""
    if (-not $Events -or $Events.Count -eq 0) {
        Write-Host ("{0}: no events detected" -f $Label)
        return
    }
    $ev    = @($Events | Sort-Object Start)
    $durs  = @($ev | ForEach-Object { $_.TotalSec / 60.0 })
    $dates = @($ev | ForEach-Object { $_.Start })
    $spanDays = [math]::Max(($dates[-1] - $dates[0]).TotalDays, 1)

    $peak7 = 0
    foreach ($d in $dates) {
        $cnt = @($dates | Where-Object { $_ -ge $d -and $_ -lt $d.AddDays(7) }).Count
        if ($cnt -gt $peak7) { $peak7 = $cnt }
    }
    $busiest = $dates | Group-Object { $_.ToString('yyyy-MM') } |
               Sort-Object Count -Descending | Select-Object -First 1

    $maxGap = $null; $gapFrom = $null; $gapTo = $null
    for ($i = 0; $i -lt $dates.Count - 1; $i++) {
        $g = $dates[$i + 1] - $dates[$i]
        if ($null -eq $maxGap -or $g -gt $maxGap) {
            $maxGap = $g; $gapFrom = $dates[$i]; $gapTo = $dates[$i + 1]
        }
    }

    $avgDur = ($durs | Measure-Object -Average).Average
    $hrAvg  = ($ev | Where-Object { $_.Hr -gt 0 } | Measure-Object -Property Hr -Average).Average

    Write-Host ("{0}: {1} events, {2:yyyy-MM-dd} .. {3:yyyy-MM-dd}" -f $Label, $ev.Count, $dates[0], $dates[-1])
    Write-Host ("  Avg duration : {0:n1} min (median {1:n1}, range {2:n0}-{3:n0})" -f
        $avgDur, (Get-Median $durs), ($durs | Measure-Object -Minimum).Minimum, ($durs | Measure-Object -Maximum).Maximum)
    Write-Host ("  Avg frequency: {0:n2}/month ({1:n2}/week)" -f
        ($ev.Count / ($spanDays / 30.44)), ($ev.Count / ($spanDays / 7)))
    Write-Host ("  Peak         : {0} in a 7-day window; busiest month {1} ({2} events)" -f
        $peak7, $busiest.Name, $busiest.Count)
    if ($maxGap) {
        Write-Host ("  Longest gap  : {0} days ({1:yyyy-MM-dd} -> {2:yyyy-MM-dd})" -f
            [int]$maxGap.TotalDays, $gapFrom, $gapTo)
    }
    if ($hrAvg) { Write-Host ("  Avg event HR : {0:n0} bpm" -f $hrAvg) }
}

# ---------------------------------------------------------------- solo events
foreach ($name in $sleepers.Keys) {
    $solo = @($sleepers[$name] | Where-Object { $_.TotalSec -le $maxSec -and (Test-Elevated $_) })
    Show-Metrics ("SOLO candidate events - {0}" -f $name) $solo
}

# ---------------------------------------------------------------- joint tiers
$names = @($sleepers.Keys)
if ($names.Count -ge 2) {
    $a = @($sleepers[$names[0]] | Where-Object { $_.TotalSec -le $maxSec })
    $b = @($sleepers[$names[1]] | Where-Object { $_.TotalSec -le $maxSec })

    $tierA = New-Object System.Collections.Generic.List[object]
    $tierB = New-Object System.Collections.Generic.List[object]
    $tierC = New-Object System.Collections.Generic.List[object]
    foreach ($sa in $a) {
        foreach ($sb in $b) {
            if ($sa.Start -lt $sb.End -and $sb.Start -lt $sa.End) {
                $tierA.Add($sa)
                $eA = Test-Elevated $sa
                $eB = Test-Elevated $sb
                if ($eA -or  $eB) { $tierB.Add($sa) }
                if ($eA -and $eB) { $tierC.Add($sa) }
                break
            }
        }
    }
    Show-Metrics ("TIER A - both in bed together, short sessions (any HR) [{0} + {1}]" -f $names[0], $names[1]) $tierA
    Show-Metrics  "TIER B - elevated HR/restlessness in at least one sleeper" $tierB
    Show-Metrics  "TIER C - elevated HR/restlessness in BOTH sleepers" $tierC
}
else {
    Write-Host "`nOnly one sleeper folder found - joint (Tier A/B/C) analysis skipped."
}
