@echo off
setlocal
cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
  set "PATH=%CD%\.venv\Scripts;%PATH%"
) else (
  set "PYTHON=python"
)

"%PYTHON%" -m mcp_server.render_queue_bridge
