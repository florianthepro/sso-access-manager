$ErrorActionPreference = "Stop"
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 "$PSScriptRoot\setup.py"; exit $LASTEXITCODE }
if (Get-Command python -ErrorAction SilentlyContinue) { & python "$PSScriptRoot\setup.py"; exit $LASTEXITCODE }
throw "Python 3.11 oder neuer wurde nicht gefunden."
