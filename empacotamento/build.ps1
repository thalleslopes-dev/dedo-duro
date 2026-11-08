# Gera o instalador do Dedo-Duro:
#   1) PyInstaller -> dist\DedoDuro\DedoDuro.exe (Python embutido)
#   2) Inno Setup  -> dist\DedoDuro-Setup-<versão>.exe (assistente "Avançar > Avançar")
#
# Uso (na raiz do projeto):  powershell -ExecutionPolicy Bypass -File empacotamento\build.ps1
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$versao = & $python -c "import dedo_duro; print(dedo_duro.__version__)"
Write-Host "==> Dedo-Duro $versao"

Write-Host "==> PyInstaller"
& $python -m PyInstaller --noconfirm --clean --windowed `
    --name DedoDuro `
    --icon "$raiz\src\dedo_duro\recursos\icone.ico" `
    --collect-all mediapipe `
    --collect-data dedo_duro `
    --hidden-import pystray._win32 `
    --distpath dist --workpath build\pyinstaller --specpath build `
    "$raiz\empacotamento\entrada.py"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou" }

Write-Host "==> Inno Setup"
$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup não encontrado. Instale com: winget install JRSoftware.InnoSetup" }
& $iscc "/DAppVersion=$versao" "empacotamento\instalador.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup falhou" }

Write-Host "==> Pronto: dist\DedoDuro-Setup-$versao.exe"
