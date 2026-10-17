# Costruisce dist\VibeFit\VibeFit.exe (cartella autonoma, senza bisogno di Python installato).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m PyInstaller --noconfirm --windowed --name VibeFit `
    --collect-all panda3d --collect-submodules direct `
    --distpath dist --workpath build app.py

if (Test-Path dist\VibeFit\VibeFit.exe) {
    $mb = [math]::Round((Get-ChildItem dist\VibeFit -Recurse | Measure-Object Length -Sum).Sum / 1MB)
    Write-Host "Pronto: dist\VibeFit\VibeFit.exe ($mb MB)"
} else {
    throw "Build fallita"
}
