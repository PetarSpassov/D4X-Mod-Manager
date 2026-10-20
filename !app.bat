@echo off
:: Opens the mod manager's window; pythonw keeps a console window from opening beside it.
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
start "" pythonw -m d4xmm.window.app
