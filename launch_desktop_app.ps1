$ErrorActionPreference = "Stop"

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $AppDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    $PythonCommand = $null
    $PythonArgs = @()
    foreach ($Candidate in @(
        @{ Command = "py"; Args = @("-3") },
        @{ Command = "python"; Args = @() },
        @{ Command = "python3"; Args = @() }
    )) {
        if (Get-Command $Candidate.Command -ErrorAction SilentlyContinue) {
            $PythonCommand = $Candidate.Command
            $PythonArgs = $Candidate.Args
            break
        }
    }

    if (-not $PythonCommand) {
        throw "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/windows/ (enable 'Add python.exe to PATH'), then reopen PowerShell and run this script again."
    }

    & $PythonCommand @PythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.10 or newer is required. Install a current version from https://www.python.org/downloads/windows/, then reopen PowerShell and run this script again."
    }

    & $PythonCommand @PythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the app's Python environment. Check the Python installation and try again."
    }
    & ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Could not upgrade pip in the app's Python environment."
    }
    & ".venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install the desktop app dependencies."
    }
}

& ".venv\Scripts\python.exe" desktop_app.py
