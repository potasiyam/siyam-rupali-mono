# Install probe font per-user, point WT at it, run the probe, capture, uninstall.
$ErrorActionPreference = 'Stop'
$fontSrc = 'F:\project\siyam-rupali-mono\build\wtprobe-zero.ttf'
$fontDst = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\wtprobe-zero.ttf"
$s = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
$bak = "$s.reviewbak2"

# install per-user
Copy-Item $fontSrc $fontDst -Force
New-Item -Path "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts" -ErrorAction SilentlyContinue | Out-Null
New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "WT Probe ZeroAdv (TrueType)" -Value $fontDst -PropertyType String -Force | Out-Null
Add-Type -Name Native -Namespace Win32 -MemberDefinition '[DllImport("gdi32.dll")] public static extern int AddFontResource(string lpFilename); [DllImport("user32.dll")] public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);'
[Win32.Native]::AddFontResource($fontDst) | Out-Null
[Win32.Native]::SendMessage(0xffff, 0x001D, 0, 0) | Out-Null   # WM_FONTCHANGE
Write-Host "probe font installed"

# point WT PowerShell profile at it
Copy-Item $s $bak -Force
$json = Get-Content $s -Raw | ConvertFrom-Json
foreach ($p in $json.profiles.list) {
    if ($p.name -eq 'Windows PowerShell') {
        $p | Add-Member -NotePropertyName font -NotePropertyValue @{} -Force
        $p.font.face = 'WT Probe ZeroAdv'
        $p.font.size = 20
    }
}
$json | ConvertTo-Json -Depth 10 | Set-Content $s -Encoding utf8

Remove-Item 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt' -ErrorAction SilentlyContinue
Start-Process wt.exe -ArgumentList '-w', 'new', 'nt', '--profile', 'Windows PowerShell', 'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'F:\project\siyam-rupali-mono\build\myprobe.ps1'
$deadline = (Get-Date).AddSeconds(40)
while ((Get-Date) -lt $deadline -and -not (Test-Path 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt')) {
    Start-Sleep -Milliseconds 500
}
Start-Sleep -Seconds 3

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32b {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
$target = Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Sort-Object StartTime -Descending | Select-Object -First 1
if ($target) {
    $rect = New-Object Win32b+RECT
    [Win32b]::GetWindowRect($target.MainWindowHandle, [ref]$rect) | Out-Null
    $bmp = New-Object System.Drawing.Bitmap(($rect.R-$rect.L), ($rect.B-$rect.T))
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [Win32b]::PrintWindow($target.MainWindowHandle, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save('F:\project\siyam-rupali-mono\build\wt_capture_zero.png', [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

# restore settings, uninstall probe font
Copy-Item $bak $s -Force
Remove-Item $bak
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "WT Probe ZeroAdv (TrueType)" -ErrorAction SilentlyContinue
Remove-Item $fontDst -Force -ErrorAction SilentlyContinue
[Win32.Native]::SendMessage(0xffff, 0x001D, 0, 0) | Out-Null
Write-Host "restored + probe font uninstalled"
if (Test-Path 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt') {
    Get-Content 'F:\project\siyam-rupali-mono\build\wt_probe_mine.txt' -Encoding utf8
} else { Write-Host "NO RESULTS" }
