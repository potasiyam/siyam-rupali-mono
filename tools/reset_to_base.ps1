# RESET — remove everything this project installed; return the system to
# the base-font state. Author verdict 2026-09-05: "Delete all. this is
# not gonna work. Work on reset to base font again."
# The original Siyam Rupali (family "Siyam Rupali") stays untouched in
# Avro's HKLM registration. Repo sources/history are not touched.
$ErrorActionPreference = 'Stop'
$reg = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'

Write-Output '== uninstall: Siyam Rupali Mono / Duo (this project)'
$props = Get-ItemProperty -Path $reg
$names = $props.PSObject.Properties.Name |
    Where-Object { $_ -like 'Siyam Rupali Mono*' -or $_ -like 'Siyam Rupali Duo*' }
foreach ($n in $names) {
    $file = $props.$n
    Remove-ItemProperty -Path $reg -Name $n
    Write-Output ("   removed: {0}  ->  {1}" -f $n, $file)
    if ($file -and (Test-Path $file)) {
        try { Remove-Item $file -Force; Write-Output '     file deleted' }
        catch { Write-Output '     file locked/left in place' }
    }
}
if (-not $names) { Write-Output '   (none found)' }

Write-Output '== broadcast WM_FONTCHANGE'
$sig = '[DllImport("user32.dll")] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);'
$t = Add-Type -MemberDefinition $sig -Name 'SendMsg' -Namespace Win32 -PassThru
[IntPtr]$res = [IntPtr]::Zero
[Win32.SendMsg]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [IntPtr]::Zero, $null, 2, 1000, [ref]$res) | Out-Null
Write-Output '   done'

Write-Output '== restore Windows Terminal faces to the default (Cascadia Mono)'
$wt = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if (Test-Path $wt) {
    Copy-Item $wt "$wt.bak-reset" -Force
    $json = Get-Content $wt -Raw -Encoding UTF8
    $patched = [regex]::Replace($json, '"face":\s*"Siyam Rupali Mono[^"]*"', '"face": "Cascadia Mono"')
    Set-Content -Path $wt -Value $patched -Encoding UTF8 -NoNewline
    $n = ([regex]::Matches($json, '"Siyam Rupali Mono[^"]*"')).Count
    Write-Output "   faces restored: $n (backup: settings.json.bak-reset)"
}
Write-Output 'OK — system is back to the base font (original Siyam Rupali via Avro)'
