$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir '.venv\Scripts\python.exe'
$BundledPython = 'C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

if (-not (Test-Path -LiteralPath $VenvPython)) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        & $PythonCommand.Source -m venv (Join-Path $ProjectDir '.venv')
    } elseif (Test-Path -LiteralPath $BundledPython) {
        & $BundledPython -m venv (Join-Path $ProjectDir '.venv')
    } else {
        throw '找不到 Python。請先安裝 Python 3.11 以上版本。'
    }
}

Start-Process 'http://127.0.0.1:8765'
& $VenvPython (Join-Path $ProjectDir 'server.py')
