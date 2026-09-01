# Backup WT settings, point the PowerShell profile at original Siyam Rupali,
# launch the probe in a new WT tab, wait for results, capture the window,
# restore settings.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$s = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
$bak = "$s.reviewbak"
Copy-Item $s $bak -Force

$json = Get-Content $s -Raw | ConvertFrom-Json
foreach ($p in $json.profiles.list) {
    if ($p.name -eq 'Windows PowerShell') {
        $p | Add-Member -NotePropertyName font -NotePropertyValue @{} -Force
        $p.font.face = 'Siyam Rupali'
        $p.font.size = 20
    }
}
$json | ConvertTo-Json -Depth 10 | Set-Content $s -Encoding utf8
Write-Host "settings patched"

Remove-Item 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt' -ErrorAction SilentlyContinue
Start-Process wt.exe -ArgumentList '-w', 'new', 'nt', '--profile', 'Windows PowerShell', 'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'F:\project\siyam-rupali-mono\build\myprobe.ps1'

# wait for results
$deadline = (Get-Date).AddSeconds(40)
while ((Get-Date) -lt $deadline -and -not (Test-Path 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt')) {
    Start-Sleep -Milliseconds 500
}
Start-Sleep -Seconds 3   # let paint settle

# capture the newest WindowsTerminal window via PrintWindow
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
$procs = Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Sort-Object StartTime -Descending
$target = $procs | Select-Object -First 1
if ($target) {
    $rect = New-Object Win32+RECT
    [Win32]::GetWindowRect($target.MainWindowHandle, [ref]$rect) | Out-Null
    $w = $rect.R - $rect.L; $h = $rect.B - $rect.T
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [Win32]::PrintWindow($target.MainWindowHandle, $hdc, 2) | Out-Null   # 2 = PW_RENDERFULLCONTENT
    $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save('F:\project\siyam-rupali-mono\build\wt_capture.png', [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "captured ${w}x${h}"
} else {
    Write-Host "no WT window found"
}

# restore settings (WT hot-reloads)
Copy-Item $bak $s -Force
Remove-Item $bak
Write-Host "settings restored"
if (Test-Path 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt') {
    Get-Content 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt' -Encoding utf8
} else {
    Write-Host "NO RESULTS FILE"
}
