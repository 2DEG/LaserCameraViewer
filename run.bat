@echo off
setlocal enabledelayedexpansion

:: ============================================================
:: LaserCameraViewer Launcher
:: Activates local .venv and runs main.py.
:: If .venv does not exist, creates it automatically.
::
:: Requires: Python 3.10 or newer (recommended: 3.12)
:: ============================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "VMBPY_WHL="
set "MIN_MAJOR=3"
set "MIN_MINOR=10"

:: ----------------------------------------------------------
:: 1. If .venv already exists and has python, just run
:: ----------------------------------------------------------
if exist "%VENV_PYTHON%" (
    echo [OK] Virtual environment found.
    goto :run
)

echo [INFO] No virtual environment found. Setting one up...
echo.

:: ----------------------------------------------------------
:: 2. Find a Python interpreter (conda, miniconda, or system)
:: ----------------------------------------------------------
set "PYTHON_EXE="

:: 2a. Check conda / miniconda
where conda >nul 2>&1
if !errorlevel! equ 0 (
    echo [INFO] Found conda installation.
    for /f "tokens=*" %%i in ('conda info --base 2^>nul') do set "CONDA_BASE=%%i"
    if exist "!CONDA_BASE!\python.exe" (
        set "PYTHON_EXE=!CONDA_BASE!\python.exe"
        goto :found_python
    )
)

:: 2b. Check common Miniconda/Anaconda paths
if not defined PYTHON_EXE (
    for %%P in (
        "%USERPROFILE%\miniconda3\python.exe"
        "%USERPROFILE%\Miniconda3\python.exe"
        "%USERPROFILE%\anaconda3\python.exe"
        "%USERPROFILE%\Anaconda3\python.exe"
        "C:\ProgramData\miniconda3\python.exe"
        "C:\ProgramData\Miniconda3\python.exe"
        "C:\ProgramData\anaconda3\python.exe"
        "C:\ProgramData\Anaconda3\python.exe"
    ) do (
        if exist %%~P (
            set "PYTHON_EXE=%%~P"
            echo [INFO] Found Python at: %%~P
            goto :found_python
        )
    )
)

:: 2c. Check system Python via PATH
if not defined PYTHON_EXE (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%i in ('where python') do (
            :: Skip Windows Store stub (WindowsApps)
            echo %%i | findstr /i "WindowsApps" >nul
            if !errorlevel! neq 0 (
                set "PYTHON_EXE=%%i"
                goto :found_python
            )
        )
    )
)

:: 2d. Check common system Python install paths (newest first)
if not defined PYTHON_EXE (
    for /d %%D in ("C:\Python314" "C:\Python313" "C:\Python312" "C:\Python311" "C:\Python310") do (
        if exist "%%~D\python.exe" (
            set "PYTHON_EXE=%%~D\python.exe"
            goto :found_python
        )
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] Could not find Python, conda, or miniconda.
    echo         Please install Python 3.10+ from https://www.python.org/downloads/
    echo         Recommended version: Python 3.12
    pause
    exit /b 1
)

:found_python
echo [INFO] Using Python: %PYTHON_EXE%

:: ----------------------------------------------------------
:: 3. Validate Python version (>= 3.10)
:: ----------------------------------------------------------
for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do set "PY_VER=%%v"
echo [INFO] Python version: %PY_VER%

for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)

if !PY_MAJOR! lss %MIN_MAJOR% goto :version_too_old
if !PY_MAJOR! equ %MIN_MAJOR% if !PY_MINOR! lss %MIN_MINOR% goto :version_too_old
goto :version_ok

:version_too_old
echo [ERROR] Python %PY_VER% is too old. Minimum required: %MIN_MAJOR%.%MIN_MINOR%
echo         Please install Python 3.10+ from https://www.python.org/downloads/
echo         Recommended version: Python 3.12
pause
exit /b 1

:version_ok

:: ----------------------------------------------------------
:: 4. Create virtual environment
:: ----------------------------------------------------------
echo [INFO] Creating virtual environment in .venv ...
"%PYTHON_EXE%" -m venv "%VENV_DIR%"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to create virtual environment.
    echo         Make sure the 'venv' module is available (python -m ensurepip).
    pause
    exit /b 1
)
echo [OK] Virtual environment created.

:: ----------------------------------------------------------
:: 5. Install dependencies from requirements.txt
:: ----------------------------------------------------------
echo [INFO] Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip >nul 2>&1

echo [INFO] Installing dependencies from requirements.txt ...
"%VENV_PIP%" install -r "%SCRIPT_DIR%requirements.txt"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo         Check the output above for details.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

:: ----------------------------------------------------------
:: 6. Install VmbPy from VimbaX SDK (if available)
:: ----------------------------------------------------------
echo [INFO] Looking for VmbPy wheel from VimbaX SDK...

:: Check standard VimbaX install locations for the wheel
for /r "C:\Program Files\Allied Vision\Vimba X\api\python" %%f in (vmbpy-*.whl) do (
    set "VMBPY_WHL=%%f"
)

if defined VMBPY_WHL (
    echo [INFO] Found VmbPy wheel: !VMBPY_WHL!
    "%VENV_PIP%" install "!VMBPY_WHL!"
    if !errorlevel! neq 0 (
        echo [WARN] Failed to install VmbPy. Allied Vision cameras will not be available.
    ) else (
        echo [OK] VmbPy installed.
    )
) else (
    echo [WARN] VimbaX SDK not found at "C:\Program Files\Allied Vision\Vimba X".
    echo        Allied Vision cameras will not be available.
    echo        To add support later, install VimbaX SDK and run:
    echo        .venv\Scripts\pip install "C:\Program Files\Allied Vision\Vimba X\api\python\vmbpy-*.whl"
)

echo.
echo ============================================================
echo  Setup complete!
echo ============================================================
echo.

:: ----------------------------------------------------------
:: 7. Run the application
:: ----------------------------------------------------------
:run
echo [INFO] Starting LaserCameraViewer...
"%VENV_PYTHON%" "%SCRIPT_DIR%main.py"
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Application exited with an error (code: !errorlevel!).
    pause
)
