@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

for /d %%D in (*) do (
    if /i not "%%D"=="B" (
    echo Compressing: %%D
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "Compress-Archive -Path '%%D\*' -DestinationPath '%%D.zip' -Force"
        if exist "%%D\01_shots" (
            for /f %%C in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$extensions = @('.mov', '.mp4', '.avi', '.mkv', '.mxf', '.wmv'); @(Get-ChildItem -LiteralPath '%%D\01_shots' -File | Where-Object { $extensions -contains $_.Extension.ToLowerInvariant() }).Count"') do set "VIDEO_COUNT=%%C"
            if "!VIDEO_COUNT!"=="3" (
                if not exist "B" mkdir "B"
                echo Moving %%D.zip to B
                move /Y "%%D.zip" "B\%%D.zip" >nul
            )
            set "VIDEO_COUNT="
        )
    )
)

echo Done.
pause
