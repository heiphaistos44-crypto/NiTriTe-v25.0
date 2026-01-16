@echo off
chcp 65001 >nul
title NiTriTe V20 - Build Portable

echo ================================================================
echo   NiTriTe V20 - Build de la Version Portable
echo ================================================================
echo.
echo Ce script va compiler l'application en un executable portable.
echo L'operation peut prendre plusieurs minutes...
echo.
echo ================================================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH
    echo.
    echo Veuillez installer Python 3.8 ou superieur depuis:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Afficher la version de Python
echo [*] Version de Python detectee:
python --version
echo.

REM Lancer le script de build Python
echo [*] Lancement du build...
echo.
python build_portable.py

REM Vérifier le code de retour
if errorlevel 1 (
    echo.
    echo ================================================================
    echo   BUILD ECHOUE !
    echo ================================================================
    echo.
    echo Consultez les messages d'erreur ci-dessus pour plus de details.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ================================================================
    echo   BUILD TERMINE AVEC SUCCES !
    echo ================================================================
    echo.
    echo L'executable portable se trouve dans:
    echo   - dist/NiTriTe_V20_Portable/
    echo.
    echo Le package de distribution se trouve dans:
    echo   - release/NiTriTe_V20_Portable/
    echo.
    echo Pour tester l'application:
    echo   1. Allez dans dist/NiTriTe_V20_Portable/
    echo   2. Lancez Lancer_NiTriTe_V20.bat ou NiTriTe_V20_Portable.exe
    echo.
    echo Pour distribuer l'application:
    echo   1. Compressez le dossier release/NiTriTe_V20_Portable/
    echo   2. Partagez l'archive ZIP/RAR
    echo.
)

pause
