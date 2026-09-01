# Independent WT column-charging probe (review session, written from scratch)
# Measures cursor X delta in cells for fixed strings, writes results file,
# then keeps the tab open 30s for screen capture.
$ErrorActionPreference = 'Continue'
$outFile = 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt'
Remove-Item $outFile -ErrorAction SilentlyContinue

# Bengali test strings built from codepoints (no encoding dependency)
$ka   = [string][char]0x0995
$cases = [ordered]@{
    'ascii_ab' = 'ab'
    'ka'       = $ka
    'ki'       = ($ka + [char]0x09BF)                    # i-kar,   font adv 541, Unicode Mn
    'ku'       = ($ka + [char]0x09C1)                    # u-kar,   font adv 0,   Unicode Mn
    'kang'     = ($ka + [char]0x0982)                    # anusvara,adv 810, Unicode Mn
    'kssa'     = ($ka + [char]0x09CD + [char]0x09B7)     # ka+vir+ssa
    'ke'       = ($ka + [char]0x09C7)                    # e-kar,   font adv 703, Unicode Mn
    'iuke'     = ([char]0x0987, [char]0x0989, $ka + [char]0x09C7) -join ''
    'hasanta'  = ($ka + [char]0x09CD)                    # virama,  font adv 3,   Unicode Mn
    'nukta'    = ($ka + [char]0x09BC)                    # nukta,   font adv 63,  Unicode Mn
}

$results = @()
foreach ($k in $cases.Keys) {
    $s = $cases[$k]
    $x0 = $Host.UI.RawUI.CursorPosition.X
    Write-Host -NoNewline $s
    $x1 = $Host.UI.RawUI.CursorPosition.X
    $results += ("{0}={1}" -f $k, ($x1 - $x0))
    Write-Host ""
}
$results += ("fontface=see-settings")
$results | Out-File -Encoding utf8 $outFile
Write-Host "PROBE DONE"
Start-Sleep -Seconds 30
