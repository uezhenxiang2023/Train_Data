@echo off
setlocal

if not "%~1"=="" goto use_argument

echo Enter the directory for the new Hiero project file.
set /p "OUTPUT_DIRECTORY=Destination directory: "
if "%OUTPUT_DIRECTORY%"=="" goto cancelled
goto validate

:use_argument
set "OUTPUT_DIRECTORY=%~1"

:validate
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%.") do set "PROJECT_NAME=%%~nxI"
for %%I in ("%OUTPUT_DIRECTORY%") do set "OUTPUT_DIRECTORY=%%~fI"
set "OUTPUT_PATH=%OUTPUT_DIRECTORY%\%PROJECT_NAME%.hrox"

if exist "%OUTPUT_PATH%" (
    echo ERROR: Refusing to overwrite existing project: "%OUTPUT_PATH%"
    goto failed
)

set "NUKE_PATH=%SCRIPT_DIR%hiero_launcher;%NUKE_PATH%"
set "HIERO_PROJECT_SAVE_PATH=%OUTPUT_PATH%"

"D:\Program Files\Nuke16.0v4\Nuke16.0.exe" --studio
exit /b %ERRORLEVEL%

:cancelled
echo Cancelled: no destination directory was provided.
exit /b 2

:failed
pause
exit /b 1
