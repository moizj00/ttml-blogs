'=== BITLOCKER (C:) ==='
try {
  $b = Get-BitLockerVolume -MountPoint 'C:' -ErrorAction Stop
  ('ProtectionStatus={0} | VolumeStatus={1}' -f $b.ProtectionStatus, $b.VolumeStatus)
} catch { 'BitLocker: could not query (' + $_.Exception.Message + ')' }

'=== AUTO SIGN-IN (registry) ==='
$w = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
$p = Get-ItemProperty -Path $w -ErrorAction SilentlyContinue
('AutoAdminLogon={0} | DefaultUserName={1}' -f $p.AutoAdminLogon, $p.DefaultUserName)

'=== CURRENT USER / LOGON ==='
('User=' + $env:USERNAME)
