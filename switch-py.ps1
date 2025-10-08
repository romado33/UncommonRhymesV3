param(
  [string]$PythonVersion = "3.11",
  [switch]$BuildWords,     # build data/dev/words_index.sqlite
  [switch]$RunApp,         # launch python app.py at the end
  [switch]$ForceClean      # delete existing .venv without asking
)

# ---- helpers
function Die($msg) { Write-Error $msg; exit 1 }
function Have($cmd) { !!(Get-Command $cmd -ErrorAction SilentlyContinue) }

$repo = Get-Location
if (-not (Test-Path "$repo\app.py")) { Die "Run this from the UncommonRhymesV3 repo root." }

# ---- confirm Python <version> exists (py launcher is best on Windows)
if (-not (Have "py")) { Die "Python launcher 'py' not found. Install from https://www.python.org/downloads/windows/ and check 'py launcher'." }
$pyList = & py -0p
if ($pyList -notmatch $PythonVersion) {
  Write-Host "Installed Pythons:`n$pyList"
  Die "Python $PythonVersion not found. Install it (e.g., 'Python 3.11.x (64-bit)') and re-run."
}

# ---- remove old venv
$venvPath = "$repo\.venv"
if (Test-Path $venvPath) {
  if ($ForceClean) {
    Write-Host "Removing existing .venv ..."
    Remove-Item -Recurse -Force $venvPath
  } else {
    $ans = Read-Host "Delete existing .venv and recreate with Python $PythonVersion? (y/N)"
    if ($ans -notin @("y","Y","yes","YES")) { Die "Cancelled." }
    Remove-Item -Recurse -Force $venvPath
  }
}

# ---- create new venv on requested Python
Write-Host "Creating new .venv with Python $PythonVersion ..."
& py -$PythonVersion -m venv .venv | Out-Null
if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) { Die "Failed to create .venv. Check Python $PythonVersion install." }

# ---- activate venv
. "$venvPath\Scripts\Activate.ps1"
Write-Host "Using Python:" (Get-Command python).Source

# ---- upgrade pip & basics
python -m pip install -U pip setuptools wheel

# ---- normalize requirements.txt (optional safety)
$reqPath = "$repo\requirements.txt"
if (-not (Test-Path $reqPath)) { Die "requirements.txt not found." }
$req = Get-Content $reqPath -Raw

# remove problematic pins if present
$changed = $false
if ($req -match "(?m)^\s*regex\s*==") {
  $req = ($req -split "`r?`n" | Where-Object { $_ -notmatch "(?m)^\s*regex\s*==" }) -join "`r`n"
  $changed = $true
}

# ensure numpy markers exist (1.26.x for <3.12; 2.x for >=3.12)
if ($req -notmatch 'numpy==1\.26\.4') { $req += "`nnumpy==1.26.4 ; python_version < `"3.12`""; $changed = $true }
if ($req -notmatch 'numpy==2\.1\.2')  { $req += "`nnumpy==2.1.2  ; python_version >= `"3.12`""; $changed = $true }

# ensure openai present
if ($req -notmatch "(?m)^\s*openai\s*>=") { $req += "`nopenai>=1.52.0"; $changed = $true }

if ($changed) { Set-Content -Path $reqPath -Value $req -Encoding UTF8 }

# ---- install deps
pip install -r requirements.txt

# ---- cmudict for builder
pip install cmudict

# ---- set env (if you use the project helper)
if (Test-Path "$repo\scripts\set-env.ps1") {
  . "$repo\scripts\set-env.ps1"
}

# ---- build words index (optional switch)
if ($BuildWords) {
  if (-not (Test-Path "$repo\scripts\build_words_index.py")) {
    Die "scripts/build_words_index.py not found."
  }
  python "$repo\scripts\build_words_index.py"
}

Write-Host ""
Write-Host "✅ Venv ready on Python $PythonVersion"
Write-Host "python ->" (Get-Command python).Source
Write-Host "pip    ->" (Get-Command pip).Source

# ---- run app (optional switch)
if ($RunApp) {
  Write-Host "`nLaunching app.py ..."
  python "$repo\app.py"
}
