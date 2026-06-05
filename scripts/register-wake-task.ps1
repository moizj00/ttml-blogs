# Registers a daily wake timer that wakes the PC at 5:55 PM and runs the
# keep-awake script (which launches Claude + holds the PC awake to 8:45 PM).
$ErrorActionPreference = 'Stop'
$script = 'C:\Users\Tesla Laptops\Obsidian\root\scripts\ttml-keep-awake.ps1'

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $script)

$trigger = New-ScheduledTaskTrigger -Daily -At '5:55PM'

$settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Register-ScheduledTask -TaskName 'TTML-Wake-And-KeepAwake' `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description 'Wakes the PC before the 6 PM TTML harvest, launches Claude, and keeps the machine awake through the blog write/publish window.' `
    -Force | Out-Null

# Best-effort: allow wake timers on the active power plan (needs admin).
try {
    $g = 'BD3B718A-0680-4D9D-8AB2-E1D2B4AC806D'
    powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP $g 1 2>$null
    powercfg -SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP $g 1 2>$null
    powercfg -S SCHEME_CURRENT 2>$null
    Write-Output 'WAKE_TIMERS: enabled (or already on)'
} catch { Write-Output 'WAKE_TIMERS: could not change (needs admin) — enable manually' }

$t = Get-ScheduledTask -TaskName 'TTML-Wake-And-KeepAwake'
Write-Output ('TASK_STATE: ' + $t.State)
$nt = (Get-ScheduledTaskInfo -TaskName 'TTML-Wake-And-KeepAwake').NextRunTime
Write-Output ('NEXT_RUN: ' + $nt)
