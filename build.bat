@echo off
echo Building FretTool executable with PyInstaller...
echo.

REM Check if icon exists
if exist "icon.ico" (
    set ICON_FLAG=--icon=icon.ico
) else (
    echo Warning: icon.ico not found, building without icon
    set ICON_FLAG=
)

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build the executable
pyinstaller --onefile --windowed --name=FretTool %ICON_FLAG% --add-data "icon.ico;." --add-data "locales;locales" main.py

echo.
if exist "dist\FretTool.exe" (
    echo Build successful! Executable created at: dist\FretTool.exe
) else (
    echo Build failed. Check the output above for errors.
)

pause
