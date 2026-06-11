@echo off
setlocal

set "PORT=%~1"
if "%PORT%"=="" set "PORT=COM3"

set "REPO=%~dp0.."
set "WORKSPACE=%REPO%\.."
set "PYTHON=%WORKSPACE%\xiaoke-actions\.venv\Scripts\python.exe"
set "PLATFORMIO_CORE_DIR=%WORKSPACE%\.platformio"
set "PLATFORMIO_SETTING_ENABLE_TELEMETRY=No"

call "%~dp0build_firmware.cmd"
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo Flashing Stack Chan on %PORT%...
pushd "%REPO%\firmware"
"%PYTHON%" -m platformio run -e m5stack-cores3 -t upload --upload-port "%PORT%"
if errorlevel 1 goto :failed
"%PYTHON%" -m platformio run -e m5stack-cores3 -t uploadfs --upload-port "%PORT%"
if errorlevel 1 goto :failed
popd

echo.
echo Flash completed. Keep the USB cable connected for serial verification.
exit /b 0

:failed
set "RESULT=%ERRORLEVEL%"
popd
exit /b %RESULT%
