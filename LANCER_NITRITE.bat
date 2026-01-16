@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title NiTriTe V25.0
color 0B

REM Aller dans le dossier du script
cd /d "%~dp0"

echo.
echo ================================================================
echo           LANCEMENT NiTriTe V25.0
echo ================================================================
echo.
echo Dossier: %CD%
echo.

REM Verifier Python 3.12
where py >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python Launcher 'py' non trouve!
    echo.
    echo Installez Python 3.12 depuis: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python 3.12 non trouve!
    echo.
    echo Installez Python 3.12 depuis: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python 3.12 detecte
echo.
echo Lancement de l'application...
echo.

REM Lancer l'application Python
py -3.12 -m src.v14_mvp.main_app
set EXITCODE=%ERRORLEVEL%

REM Si erreur, afficher message et pause
if %EXITCODE% neq 0 (
    echo.
    echo ================================================================
    echo           ERREUR AU LANCEMENT (code: %EXITCODE%)
    echo ================================================================
    echo.
    echo Pour installer les dependances:
    echo   py -3.12 -m pip install -r requirements.txt
    echo.
    pause
)

endlocal
