'=== SUPPORTED SLEEP/POWER STATES ==='
powercfg /a

'=== NETWORK ADAPTERS ==='
Get-NetAdapter | Sort-Object Status | Format-Table Name, Status, MacAddress, LinkSpeed, MediaType -AutoSize | Out-String

'=== WAKE-ON-MAGIC-PACKET (per active adapter) ==='
Get-NetAdapter | Where-Object Status -eq 'Up' | ForEach-Object {
    $pm = Get-NetAdapterPowerManagement -Name $_.Name -ErrorAction SilentlyContinue
    if ($pm) { ('{0} | WakeOnMagicPacket={1} | WakeOnPattern={2}' -f $_.Name, $pm.WakeOnMagicPacket, $pm.WakeOnPattern) }
}

'=== DEVICES CURRENTLY ARMED TO WAKE ==='
powercfg -devicequery wake_armed

'=== DEVICES THAT CAN WAKE (wake_programmable) ==='
powercfg -devicequery wake_programmable
