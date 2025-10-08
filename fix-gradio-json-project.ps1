# fix-gradio-json-project.ps1
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Backup-File($p) {
  if (Test-Path $p) { Copy-Item $p "$p.bak.grjson" -Force }
}

# 1) Replace gr.JSON(...) everywhere with read-only Textbox
$pyFiles = Get-ChildItem -Recurse -Include *.py
$pattern = 'gr\.JSON\s*\((?<args>[^)]*)\)'

foreach ($f in $pyFiles) {
  $src = Get-Content $f.FullName -Raw
  if ($src -notmatch $pattern) { continue }
  Backup-File $f.FullName

  $new = [regex]::Replace($src, $pattern, {
    param($m)
    $args  = $m.Groups['args'].Value
    $label = '"Debug JSON"'
    if ($args -match "label\s*=\s*([`"'][^`"']*[`"'])") { $label = $Matches[1] }
    "gr.Textbox(label=$label, lines=14, interactive=False)"
  })
  Set-Content -Path $f.FullName -Value $new -Encoding UTF8
  Write-Host "Patched gr.JSON → Textbox in $($f.FullName)"
}

# 2) Ensure 'import json' exists in app.py
$app = ".\app.py"
if (Test-Path $app) {
  $src = Get-Content $app -Raw
  if ($src -notmatch "(?m)^\s*import\s+json\b") {
    if ($src -match "(?ms)^(?<head>(?:\s*from\s+\S+\s+import.*\r?\n|\s*import\s+\S+.*\r?\n)+)") {
      $head = $Matches['head']; $src = $src.Replace($head, $head + "import json`r`n")
    } else { $src = "import json`r`n" + $src }
    Backup-File $app
    Set-Content -Path $app -Value $src -Encoding UTF8
    Write-Host "Ensured 'import json' in app.py"
  }
}

# 3) Force share=False and local server_name to skip frpc
if (Test-Path $app) {
  $src = Get-Content $app -Raw
  if ($src -match "demo\.launch\s*\(") {
    Backup-File $app
    $src2 = [regex]::Replace($src, "demo\.launch\s*\(.*?\)\s*$", "",
      [System.Text.RegularExpressions.RegexOptions]::Singleline)

    $safeLaunch = @"
    
if __name__ == "__main__":
    # Avoid share=True to skip frpc download on Windows
    demo.launch(share=False, server_name="127.0.0.1")
"@
    Set-Content -Path $app -Value ($src2.TrimEnd() + "`r`n" + $safeLaunch) -Encoding UTF8
    Write-Host "Rewrote demo.launch(...) to share=False, server_name='127.0.0.1'"
  }
}

Write-Host "✅ Finished patching. Backups saved as *.bak.grjson where changes were made."
