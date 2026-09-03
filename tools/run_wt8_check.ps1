# WT-only check: Siyam Rupali Mono WT8 (no ligatures, verbatim matras).
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class CapW8 {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
$probe = 'F:\project\siyam-rupali-mono\tools\proof_column_probe.ps1'
$dir = 'F:\project\siyam-rupali-mono\build\proof'
$s = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
$bak = "$s.wt8bak2"
Copy-Item $s $bak -Force
$json = Get-Content $s -Raw | ConvertFrom-Json
foreach ($p in $json.profiles.list) {
    if ($p.name -eq 'Windows PowerShell') {
        $p | Add-Member -NotePropertyName font -NotePropertyValue @{} -Force
        $p.font.face = 'Siyam Rupali Mono WT8'
        $p.font.size = 16
    }
}
$json | ConvertTo-Json -Depth 10 | Set-Content $s -Encoding utf8
Remove-Item "$dir\wt8.txt" -ErrorAction SilentlyContinue
$env:TERMINAL_TAG = 'wt8'
Start-Process wt.exe -ArgumentList '-w','new','nt','--profile','Windows PowerShell','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',$probe,'-OutFile',"$dir\wt8.txt"
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline -and -not (Test-Path "$dir\wt8.txt")) { Start-Sleep -Milliseconds 500 }
Start-Sleep -Seconds 4
$p = Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Sort-Object StartTime -Descending | Select-Object -First 1
if ($p) {
    [CapW8]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 600
    $rect = New-Object CapW8+RECT
    [CapW8]::GetWindowRect($p.MainWindowHandle, [ref]$rect) | Out-Null
    $bmp = New-Object System.Drawing.Bitmap(($rect.R-$rect.L), ($rect.B-$rect.T))
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [CapW8]::PrintWindow($p.MainWindowHandle, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save("$dir\cap_wt8.png", [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "captured"
} else {
    Write-Host "no WT window"
}
Copy-Item $bak $s -Force; Remove-Item $bak
Get-Content "$dir\wt8.txt" -Encoding utf8 -ErrorAction SilentlyContinue
Write-Host "DONE"
