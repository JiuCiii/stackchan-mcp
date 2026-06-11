@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo Stack Chan Python environment was not found. 1>&2
  exit /b 1
)

".venv\Scripts\python.exe" -m mcp_server.server
