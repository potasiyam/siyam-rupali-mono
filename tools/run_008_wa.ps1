$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Cap5 {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
function Capture([string]$procName, [string]$png) {
    Start-Sleep -Seconds 4
    $p = Get-Process $procName -ErrorAction SilentlyContinue |
         Where-Object { $_.MainWindowHandle -ne 0 } |
         Sort-Object StartTime -Descending | Select-Object -First 1
    if (-not $p) { Write-Host "$procName : NO WINDOW"; return }
    [Cap5]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 600
    $rect = New-Object Cap5+RECT
    [Cap5]::GetWindowRect($p.MainWindowHandle, [ref]$rect) | Out-Null
    $bmp = New-Object System.Drawing.Bitmap(($rect.R-$rect.L), ($rect.B-$rect.T))
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [Cap5]::PrintWindow($p.MainWindowHandle, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "$procName captured"
}

$env:TERMINAL_TAG = 'wezterm'
Start-Process 'C:\Program Files\WezTerm\wezterm.exe' -ArgumentList 'start','--always-new-process','--','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','F:\project\siyam-rupali-mono\tools\terminal_test.ps1'
Capture 'wezterm-gui' 'F:\project\siyam-rupali-mono\build\cap008_wezterm.png'
Get-Content 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -Encoding utf8 -ErrorAction SilentlyContinue

$env:TERMINAL_TAG = 'alacritty'
Start-Process 'C:\Program Files\Alacritty\alacritty.exe' -ArgumentList '-e','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','F:\project\siyam-rupali-mono\tools\terminal_test.ps1'
Capture 'alacritty' 'F:\project\siyam-rupali-mono\build\cap008_alacritty.png'
Get-Content 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -Encoding utf8 -ErrorAction SilentlyContinue
Write-Host "DONE"
