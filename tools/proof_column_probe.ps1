# Proof probe: extended column cases (incl. anusvara) + visual lines.
param([string]$OutFile = 'F:\project\siyam-rupali-mono\build\proof\probe_results.txt')
$ErrorActionPreference = 'Continue'
$ka = [string][char]0x0995
$cases = [ordered]@{
    'ka'       = $ka
    'kaa'      = ($ka + [char]0x09BE)
    'ki'       = ($ka + [char]0x09BF)
    'kang'     = ($ka + [char]0x0982)
    'king'     = ($ka + [char]0x09BF + [char]0x0982)
    'ko'       = ($ka + [char]0x09CB)
    'kou'      = ($ka + [char]0x09CC)
    'kssa'     = ($ka + [char]0x09CD + [char]0x09B7)
    'korto'    = ($ka + [char]0x09B0 + [char]0x09CD + [char]0x09A4)
    'kortobbo' = ($ka + [char]0x09B0 + [char]0x09CD + [char]0x09A4 + [char]0x09AC + [char]0x09CD + [char]0x09AF)
    'bimurho'  = ([string][char]0x09AC + [char]0x09BF + [char]0x09AE + [char]0x09C1 + [char]0x09A2 + [char]0x09BC)
    'iuke'     = ([string][char]0x0987 + [char]0x0989 + $ka + [char]0x09C7)
}
$full = ([string]$cases['king'] + $cases['korto'] + $cases['kortobbo'] + $cases['bimurho'] + ' ' + $cases['ki'] + ' ' + $cases['ki'])
Clear-Host
Write-Host "RULER: abcdefghijklmnop 0123456789"
Write-Host "TEST : $(($cases.Values -join ' '))"
Write-Host "FULL : $full"
Write-Host ""
$results = @()
$results += "term=$env:TERMINAL_TAG"
foreach ($k in $cases.Keys) {
    $s = [string]$cases[$k]
    $x0 = $Host.UI.RawUI.CursorPosition.X
    Write-Host -NoNewline $s
    $x1 = $Host.UI.RawUI.CursorPosition.X
    $results += ("{0}={1}" -f $k, ($x1 - $x0))
    Write-Host "   <- $k"
}
$x0 = $Host.UI.RawUI.CursorPosition.X
Write-Host -NoNewline $full
$x1 = $Host.UI.RawUI.CursorPosition.X
$results += ("full={0}" -f ($x1 - $x0))
Write-Host "   <- full"
$results | Out-File -Encoding utf8 $OutFile
Write-Host "PROBE DONE"
Start-Sleep -Seconds 40
