@echo off
setlocal

cd /d "%~dp0"

for /d %%D in (*) do (
    echo Compressing: %%D
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "Compress-Archive -Path '%%D\*' -DestinationPath '%%D.zip' -Force"
)

echo Done.
pause
