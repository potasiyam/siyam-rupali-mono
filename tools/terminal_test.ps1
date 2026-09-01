# Cross-terminal probe: prints ASCII ruler + Bengali test line, measures
# cursor deltas (ConPTY model on wezterm/alacritty/WT), writes results, sleeps
# so the driver can capture the window.
param([string]$OutFile = 'F:\project\siyam-rupali-mono\build\term_probe_results.txt')
$ErrorActionPreference = 'Continue'

$ka = [string][char]0x0995
$line2 = (($ka),
          ($ka + [char]0x09BE),
          ($ka + [char]0x09BF),
          ($ka + [char]0x09C0),
          ($ka + [char]0x09C7),
          ($ka + [char]0x09CB),
          ($ka + [char]0x09CD + [char]0x09B7),
          ($ka + [char]0x09CD + [char]0x09B7 + [char]0x09BF),
          ([string][char]0x0987 + [char]0x0989 + $ka + [char]0x09C7)) -join ' '

Clear-Host
Write-Host "RULER: abcdefghijklmnop 0123456789"
Write-Host "TEST : $line2"
Write-Host ""

$results = @()
$results += "term=$env:TERMINAL_TAG"
$cases = [ordered]@{
    'ka'    = $ka
    'kaa'   = ($ka + [char]0x09BE)
    'ki'    = ($ka + [char]0x09BF)
    'kii'   = ($ka + [char]0x09C0)
    'ke'    = ($ka + [char]0x09C7)
    'ko'    = ($ka + [char]0x09CB)
    'kssa'  = ($ka + [char]0x09CD + [char]0x09B7)
    'kssi'  = ($ka + [char]0x09CD + [char]0x09B7 + [char]0x09BF)
    'iuke'  = ([string][char]0x0987 + [char]0x0989 + $ka + [char]0x09C7)
}
foreach ($k in $cases.Keys) {
    $s = [string]$cases[$k]
    $x0 = $Host.UI.RawUI.CursorPosition.X
    Write-Host -NoNewline $s
    $x1 = $Host.UI.RawUI.CursorPosition.X
    $results += ("{0}={1}" -f $k, ($x1 - $x0))
    Write-Host "   <- $k"
}
$results | Out-File -Encoding utf8 $OutFile
Write-Host "PROBE DONE"
Start-Sleep -Seconds 40
