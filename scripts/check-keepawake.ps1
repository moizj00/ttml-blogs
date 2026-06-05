$e=$null; $t=$null
[void][System.Management.Automation.Language.Parser]::ParseFile('C:\Users\Tesla Laptops\Obsidian\root\scripts\ttml-keep-awake.ps1',[ref]$t,[ref]$e)
if ($e -and $e.Count) { $e | ForEach-Object { 'PARSE_ERR: ' + $_.Message } } else { 'PARSE_OK' }
if (Get-Process -Name claude -ErrorAction SilentlyContinue) { 'CLAUDE_RUNNING_YES' } else { 'CLAUDE_RUNNING_NO' }
