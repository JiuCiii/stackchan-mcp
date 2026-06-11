@echo off
setlocal

set "PORT=%~1"
if "%PORT%"=="" set "PORT=COM3"

set "REPO=%~dp0.."
set "WORKSPACE=%REPO%\.."
set "PYTHON=%WORKSPACE%\xiaoke-actions\.venv\Scripts\python.exe"
set "BACKUP=%WORKSPACE%\stackchan-backups\stock-1.4.1-recovery"

if not exist "%PYTHON%" (
  echo esptool Python was not found: %PYTHON%
  exit /b 1
)
if not exist "%BACKUP%\chunk-00-000000.bin" (
  echo Stock firmware backup was not found: %BACKUP%
  exit /b 1
)

echo This restores the backed-up Stack Chan 1.4.1 image on %PORT%.
echo Press Ctrl+C now to cancel, or any key to continue.
pause >nul

"%PYTHON%" -m esptool --chip esp32s3 --port "%PORT%" --baud 460800 write-flash ^
  0x000000 "%BACKUP%\chunk-00-000000.bin" ^
  0x500000 "%BACKUP%\chunk-500000.bin" ^
  0x600000 "%BACKUP%\chunk-600000-rom.bin" ^
  0x700000 "%BACKUP%\current-app-tail-700000-9fffff.bin" ^
  0xA00000 "%BACKUP%\assets-a00000-dfffff.bin"
exit /b %ERRORLEVEL%
