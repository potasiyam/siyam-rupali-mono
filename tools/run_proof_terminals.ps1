# Proof driver: WPF resolution check, then WT + WezTerm + Alacritty
# column probes and captures with the PROOF family; restores all configs.
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class CapP {
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
    [CapP]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 600
    $rect = New-Object CapP+RECT
    [CapP]::GetWindowRect($p.MainWindowHandle, [ref]$rect) | Out-Null
    $bmp = New-Object System.Drawing.Bitmap(($rect.R-$rect.L), ($rect.B-$rect.T))
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [CapP]::PrintWindow($p.MainWindowHandle, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "$procName captured"
}
$probe = 'F:\project\siyam-rupali-mono\tools\proof_column_probe.ps1'
$dir = 'F:\project\siyam-rupali-mono\build\proof'

# --- Windows Terminal ---
$s = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
$bak = "$s.proofbak"
Copy-Item $s $bak -Force
$json = Get-Content $s -Raw | ConvertFrom-Json
foreach ($p in $json.profiles.list) {
    if ($p.name -eq 'Windows PowerShell') {
        $p | Add-Member -NotePropertyName font -NotePropertyValue @{} -Force
        $p.font.face = 'Siyam Rupali Mono Proof'
        $p.font.size = 16
    }
}
$json | ConvertTo-Json -Depth 10 | Set-Content $s -Encoding utf8
Remove-Item "$dir\wt.txt" -ErrorAction SilentlyContinue
$env:TERMINAL_TAG = 'wt'
Start-Process wt.exe -ArgumentList '-w','new','nt','--profile','Windows PowerShell','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',$probe,'-OutFile',"$dir\wt.txt"
Capture 'WindowsTerminal' "$dir\cap_proof_wt.png"
Get-Content "$dir\wt.txt" -Encoding utf8 -ErrorAction SilentlyContinue
Copy-Item $bak $s -Force; Remove-Item $bak

# --- WezTerm ---
$wz = 'C:\Users\Siyam\.wezterm.lua'
$wzbak = "$wz.proofbak"
Copy-Item $wz $wzbak -Force
Set-Content -Path $wz -Encoding utf8 -Value "-- WezTerm proof config`nlocal wezterm = require 'wezterm'`nlocal config = {}`nconfig.font = wezterm.font('Siyam Rupali Mono Proof')`nconfig.font_size = 16`nreturn config`n"
Remove-Item "$dir\wezterm.txt" -ErrorAction SilentlyContinue
$env:TERMINAL_TAG = 'wezterm'
Start-Process 'C:\Program Files\WezTerm\wezterm.exe' -ArgumentList 'start','--always-new-process','--','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',$probe,'-OutFile',"$dir\wezterm.txt"
Capture 'wezterm-gui' "$dir\cap_proof_wezterm.png"
Get-Content "$dir\wezterm.txt" -Encoding utf8 -ErrorAction SilentlyContinue
Copy-Item $wzbak $wz -Force; Remove-Item $wzbak

# --- Alacritty ---
$al = "$env:APPDATA\alacritty\alacritty.toml"
$albak = "$al.proofbak"
Copy-Item $al $albak -Force
Set-Content -Path $al -Encoding utf8 -Value "[font]`nsize = 16`n`n[font.normal]`nfamily = `"Siyam Rupali Mono Proof`"`n"
Get-Process alacritty -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 1
Remove-Item "$dir\alacritty.txt" -ErrorAction SilentlyContinue
$env:TERMINAL_TAG = 'alacritty'
Start-Process 'C:\Program Files\Alacritty\alacritty.exe' -ArgumentList '-e','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',$probe,'-OutFile',"$dir\alacritty.txt"
Capture 'alacritty' "$dir\cap_proof_alacritty.png"
Get-Content "$dir\alacritty.txt" -Encoding utf8 -ErrorAction SilentlyContinue
Copy-Item $albak $al -Force; Remove-Item $albak
Write-Host "ALL DONE"
