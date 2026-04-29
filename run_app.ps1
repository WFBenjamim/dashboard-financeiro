$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherLogPath = Join-Path $projectRoot 'dashboard_launcher.log'

$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    throw 'Nao foi possivel localizar a .venv local do projeto. Crie a virtualenv dentro da pasta do projeto antes de executar.'
}

Set-Location $projectRoot

function Write-LauncherLog {
    param([string]$Message)

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $launcherLogPath -Value "[$timestamp] $Message"
}

foreach ($envName in @('PYTHONHOME', 'PYTHONPATH', 'VIRTUAL_ENV')) {
    if (Test-Path "Env:$envName") {
        Remove-Item "Env:$envName" -ErrorAction SilentlyContinue
    }
}

$pythonCheck = & $pythonExe -c "import sys; import numpy; import pandas; print(sys.executable); print(numpy.__version__); print(pandas.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    $message = "Falha ao validar o ambiente Python em $pythonExe.\n\n$pythonCheck"
    Write-LauncherLog $message
    throw $message
}

Write-LauncherLog "Python validado: $pythonCheck"
& $pythonExe -m streamlit run app.py
exit $LASTEXITCODE