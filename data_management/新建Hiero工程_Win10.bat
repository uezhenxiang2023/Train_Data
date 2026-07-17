@echo off
setlocal

if not "%~1"=="" goto use_argument

echo Enter the full path for the new Hiero project file.
set /p "OUTPUT_PATH=Destination (.hrox): "
if "%OUTPUT_PATH%"=="" goto cancelled
goto validate

:use_argument
set "OUTPUT_PATH=%~1"

:validate
for %%I in ("%OUTPUT_PATH%") do (
    set "OUTPUT_PATH=%%~fI"
    set "OUTPUT_EXTENSION=%%~xI"
)

if /I not "%OUTPUT_EXTENSION%"==".hrox" (
    echo ERROR: The destination must have a .hrox extension.
    goto failed
)

if exist "%OUTPUT_PATH%" (
    echo ERROR: Refusing to overwrite existing project: "%OUTPUT_PATH%"
    goto failed
)

set "SCRIPT_DIR=%~dp0"
set "NUKE_PATH=%SCRIPT_DIR%hiero_launcher;%NUKE_PATH%"
set "HIERO_PROJECT_SAVE_PATH=%OUTPUT_PATH%"

"D:\Program Files\Nuke16.0v4\Nuke16.0.exe" --studio
exit /b %ERRORLEVEL%

:cancelled
echo Cancelled: no destination was provided.
exit /b 2

:failed
pause
exit /b 1
