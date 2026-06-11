@echo off
setlocal

set "REPO=%~dp0.."
set "WORKSPACE=%REPO%\.."
set "PYTHON=%WORKSPACE%\xiaoke-actions\.venv\Scripts\python.exe"
set "PLATFORMIO_CORE_DIR=%WORKSPACE%\.platformio"
set "PLATFORMIO_SETTING_ENABLE_TELEMETRY=No"

if not exist "%PYTHON%" (
  echo PlatformIO Python was not found: %PYTHON%
  exit /b 1
)

pushd "%REPO%\firmware"
"%PYTHON%" -m platformio run -e m5stack-cores3
if errorlevel 1 goto :failed
"%PYTHON%" -m platformio run -e m5stack-cores3 -t buildfs
if errorlevel 1 goto :failed
popd

echo.
echo Firmware and SPIFFS build completed.
exit /b 0

:failed
set "RESULT=%ERRORLEVEL%"
popd
exit /b %RESULT%
