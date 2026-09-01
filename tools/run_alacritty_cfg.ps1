$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Cap4 {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
Get-Process alacritty -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 1
Remove-Item 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -ErrorAction SilentlyContinue
$env:TERMINAL_TAG = 'alacritty'
$p = Start-Process 'C:\Program Files\Alacritty\alacritty.exe' -ArgumentList '-vv','-e','powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',"& 'F:\project\siyam-rupali-mono\tools\terminal_test.ps1' -OutFile 'F:\project\siyam-rupali-mono\build\term_probe_results.txt'; Start-Sleep 20",'>','F:\project\siyam-rupali-mono\build\alacritty_vv.log','2>&1' -PassThru -RedirectStandardError 'F:\project\siyam-rupali-mono\build\alacritty_err.log'
Start-Sleep -Seconds 6
$target = Get-Process alacritty -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Sort-Object StartTime -Descending | Select-Object -First 1
if ($target) {
    [Cap4]::SetForegroundWindow($target.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 600
    $rect = New-Object Cap4+RECT
    [Cap4]::GetWindowRect($target.MainWindowHandle, [ref]$rect) | Out-Null
    $bmp = New-Object System.Drawing.Bitmap(($rect.R-$rect.L), ($rect.B-$rect.T))
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [Cap4]::PrintWindow($target.MainWindowHandle, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save('F:\project\siyam-rupali-mono\build\cap_alacritty_cfg.png', [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "captured"
}
Get-Content 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -Encoding utf8 -ErrorAction SilentlyContinue | Select-Object -First 11
Write-Host "--- alacritty -vv log (font lines):"
if (Test-Path 'F:\project\siyam-rupali-mono\build\alacritty_err.log') {
    Get-Content 'F:\project\siyam-rupali-mono\build\alacritty_err.log' -ErrorAction SilentlyContinue | Select-String -Pattern "font|Font|fallback|family" | Select-Object -First 15
}
