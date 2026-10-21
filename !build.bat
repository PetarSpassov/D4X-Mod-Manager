@echo off
:: Builds the app with Nuitka into build\D4XModManager: the exe, its files, vendor\ beside it.
:: Needs Nuitka; it compiles with Zig, which Nuitka keeps in its cache. Run from this folder.
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
python -m nuitka --mode=standalone --python-flag=-m --zig ^
  --include-package-data=d4xmm ^
  --windows-console-mode=disable --windows-icon-from-ico=src\d4xmm\window\logo.ico ^
  --product-name="D4X Mod Manager" --product-version=0.1.0 --file-version=0.1.0 ^
  --company-name="Petar Spassov" --file-description="D4X Mod Manager" ^
  --output-dir=build\nuitka --output-filename=D4XModManager.exe ^
  src\d4xmm || exit /b 1
:: a running D4XModManager.exe locks its files: stop before deleting half of the folder
tasklist /fi "imagename eq D4XModManager.exe" | find /i "D4XModManager.exe" >nul && (
  echo Close D4X Mod Manager first: the build replaces its folder. & exit /b 1)
if exist build\D4XModManager rmdir /s /q build\D4XModManager
if exist build\D4XModManager (echo Could not clear build\D4XModManager. & exit /b 1)
move build\nuitka\d4xmm.dist build\D4XModManager >nul
if not exist build\D4XModManager\D4XModManager.exe (echo The move failed. & exit /b 1)
:: the binaries are not Python, so Nuitka leaves them out; they go in as they came
robocopy vendor build\D4XModManager\vendor /e /njh /njs /ndl /nfl >nul
if errorlevel 8 exit /b 1
copy /y LICENSE build\D4XModManager >nul
copy /y README.md build\D4XModManager >nul
echo Built build\D4XModManager\D4XModManager.exe
