# Install the two canonical families, retire the variant zoo.
# Poison-lesson discipline (WORKLOG 2026-09-01): never leave a family
# pointing at more than one file; fresh filenames per build; registry
# values removed before the new install; WM_FONTCHANGE broadcasts.
$ErrorActionPreference = 'Stop'
$reg = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$fdir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
$root = 'I:\projects\siyam-rupali-mono\build'

Write-Output '== uninstall: every Siyam Rupali Mono* variant value'
$props = Get-ItemProperty -Path $reg
$names = $props.PSObject.Properties.Name | Where-Object { $_ -like 'Siyam Rupali Mono*' }
foreach ($n in $names) {
    $file = $props.$n
    Remove-ItemProperty -Path $reg -Name $n
    Write-Output ("   removed: {0}  ->  {1}" -f $n, $file)
    if ($file -and (Test-Path $file)) {
        try { Remove-Item $file -Force; Write-Output '     file deleted' }
        catch { Write-Output '     file locked/left in place (harmless orphan)' }
    }
}
if (-not $names) { Write-Output '   (none found)' }

Write-Output '== install: canonical families'
$installs = @(
    @{ family = 'Siyam Rupali Mono'; src = "$root\SiyamRupaliMono-0100.ttf" },
    @{ family = 'Siyam Rupali Duo';  src = "$root\SiyamRupaliDuo-0100.ttf" }
)
foreach ($i in $installs) {
    $dst = Join-Path $fdir (Split-Path $i.src -Leaf)
    Copy-Item $i.src $dst -Force
    $val = '{0} (TrueType)' -f $i.family
    New-ItemProperty -Path $reg -Name $val -Value $dst -PropertyType String -Force | Out-Null
    Write-Output ("   registered: {0}  ->  {1}" -f $val, $dst)
}

Write-Output '== broadcast WM_FONTCHANGE'
$sig = '[DllImport("user32.dll")] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);'
$t = Add-Type -MemberDefinition $sig -Name 'SendMsg' -Namespace Win32 -PassThru
[IntPtr]$res = [IntPtr]::Zero
[Win32.SendMsg]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [IntPtr]::Zero, $null, 2, 1000, [ref]$res) | Out-Null
Write-Output '   done'

Write-Output '== patch Windows Terminal profile faces'
$wt = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if (Test-Path $wt) {
    Copy-Item $wt "$wt.bak-canonical" -Force
    $json = Get-Content $wt -Raw -Encoding UTF8
    # JSONC-safe regex: any "Siyam Rupali Mono <suffix>" face -> canonical
    $patched = [regex]::Replace($json, '"(Siyam Rupali Mono[^"]*)"', '"Siyam Rupali Mono"')
    Set-Content -Path $wt -Value $patched -Encoding UTF8 -NoNewline
    $changed = ([regex]::Matches($json, '"Siyam Rupali Mono[^"]*"')).Count
    Write-Output "   face references rewritten: $changed (backup: settings.json.bak-canonical)"
} else {
    Write-Output '   settings.json not found - skipped'
}
Write-Output 'OK'
