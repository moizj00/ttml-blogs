# TTML keep-awake: launch Claude if needed, then hold the PC awake
# through the blog pipeline window (harvest 6pm -> write -> publish).
$ErrorActionPreference = 'SilentlyContinue'

# 1. Launch the Claude desktop app if it is not already running.
if (-not (Get-Process -Name 'claude')) {
    $bases = @(
        (Join-Path $env:LOCALAPPDATA 'AnthropicClaude'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Claude'),
        (Join-Path $env:PROGRAMFILES  'Claude')
    )
    foreach ($b in $bases) {
        if (Test-Path $b) {
            $exe = Get-ChildItem -Path $b -Recurse -Filter 'claude.exe' |
                   Select-Object -First 1 -ExpandProperty FullName
            if ($exe) { Start-Process $exe; break }
        }
    }
}

# 2. Keep the system + display awake until 20:45 local time.
$sig = @'
using System;
using System.Runtime.InteropServices;
public static class Power {
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern uint SetThreadExecutionState(uint esFlags);
}
'@
Add-Type -TypeDefinition $sig
$ES_CONTINUOUS       = [uint32]2147483648
$ES_SYSTEM_REQUIRED  = [uint32]1
$ES_DISPLAY_REQUIRED = [uint32]2
$keep = [uint32]($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED)
[void][Power]::SetThreadExecutionState($keep)

$until = (Get-Date).Date.AddHours(20).AddMinutes(45)
while ((Get-Date) -lt $until) { Start-Sleep -Seconds 60 }

# 3. Release the lock so normal sleep resumes.
[void][Power]::SetThreadExecutionState($ES_CONTINUOUS)
