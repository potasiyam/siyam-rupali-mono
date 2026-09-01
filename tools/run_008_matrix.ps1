# Install universal 0.0.4 (new file name, same family), then run the
# column probe + capture in WT, WezTerm, and Alacritty.
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Cap3 {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("gdi32.dll")] public static extern int AddFontResource(string f);
    [DllImport("user32.dll")] public static extern int SendMessage(int h, int m, int w, int l);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
function Capture([string]$procName, [string]$png) {
    Start-Sleep -Seconds 4
    $p = Get-Process $procName -ErrorAction SilentlyContinue |
         Where-Object { $_.MainWindowHandle -ne 0 } |
         Sort-Object StartTime -Descending | Select-Object -First 1
    if (-not $p) { Write-Host "$procName : NO WINDOW"; return }
    [Cap3]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 600
    $rect = New-Object Cap3+RECT
    [Cap3]::GetWindowRect($p.MainWindowHandle, [ref]$rect) | Out-Null
    $bmp = New-Object System.Drawing.Bitmap(($rect.R-$rect.L), ($rect.B-$rect.T))
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [Cap3]::PrintWindow($p.MainWindowHandle, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc); $g.Dispose()
    $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "$procName captured"
}

# --- install 0.0.4 under the same family, new file ---
$fontDst = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\SiyamRupaliMono-008.ttf"
Copy-Item 'F:\project\siyam-rupali-mono\build\SiyamRupaliMono-008.ttf' $fontDst -Force
New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "Siyam Rupali Mono (TrueType)" -Value $fontDst -PropertyType String -Force | Out-Null
[Cap3]::AddFontResource($fontDst) | Out-Null
[Cap3]::SendMessage(0xffff, 0x001D, 0, 0) | Out-Null
Write-Host "0.0.4 installed"

$s = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
$bak = "$s.reviewbak8"

# --- Windows Terminal ---
Copy-Item $s $bak -Force
$json = Get-Content $s -Raw | ConvertFrom-Json
foreach ($p in $json.profiles.list) {
    if ($p.name -eq 'Windows PowerShell') {
        $p | Add-Member -NotePropertyName font -NotePropertyValue @{} -Force
        $p.font.face = 'Siyam Rupali Mono'
        $p.font.size = 16
    }
}
$json | ConvertTo-Json -Depth 10 | Set-Content $s -Encoding utf8
Remove-Item 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -ErrorAction SilentlyContinue
$env:TERMINAL_TAG = 'wt'
Start-Process wt.exe -ArgumentList '-w','new','nt','--profile','Windows PowerShell','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','F:\project\siyam-rupali-mono\tools\terminal_test.ps1'
Capture 'WindowsTerminal' 'F:\project\siyam-rupali-mono\build\cap008_wt.png'
Get-Content 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -Encoding utf8 -ErrorAction SilentlyContinue | Select-Object -First 11
Move-Item 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' 'F:\project\siyam-rupali-mono\build\results008_wt.txt' -Force -ErrorAction SilentlyContinue
Copy-Item $bak $s -Force; Remove-Item $bak

# --- WezTerm ---
$env:TERMINAL_TAG = 'wezterm'
Start-Process 'C:\Program Files\WezTerm\wezterm.exe' -ArgumentList 'start','--always-new-process','--','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','F:\project\siyam-rupali-mono\tools\terminal_test.ps1'
Capture 'wezterm-gui' 'F:\project\siyam-rupali-mono\build\cap008_wezterm.png'
Get-Content 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -Encoding utf8 -ErrorAction SilentlyContinue | Select-Object -First 11
Move-Item 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' 'F:\project\siyam-rupali-mono\build\results008_wezterm.txt' -Force -ErrorAction SilentlyContinue

# --- Alacritty ---
$env:TERMINAL_TAG = 'alacritty'
Start-Process 'C:\Program Files\Alacritty\alacritty.exe' -ArgumentList '-o','font.size=16','-o','font.normal.family="Siyam Rupali Mono"','-e','powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','F:\project\siyam-rupali-mono\tools\terminal_test.ps1'
Capture 'alacritty' 'F:\project\siyam-rupali-mono\build\cap008_alacritty.png'
Get-Content 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' -Encoding utf8 -ErrorAction SilentlyContinue | Select-Object -First 11
Move-Item 'F:\project\siyam-rupali-mono\build\term_probe_results.txt' 'F:\project\siyam-rupali-mono\build\results008_alacritty.txt' -Force -ErrorAction SilentlyContinue
Write-Host "ALL DONE"


