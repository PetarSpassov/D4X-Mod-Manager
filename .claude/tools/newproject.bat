@echo off
rem Copies this template into a folder you pick: no .git, state or todelete, never overwriting.
rem A folder given as the first argument skips the dialog, so the self-test can run it.
setlocal
for %%I in ("%~dp0..\..") do set "SRC=%%~fI"
set "DEST=%~1"
set "PS=Add-Type -AssemblyName System.Windows.Forms; $d = New-Object"
set "PS=%PS% System.Windows.Forms.FolderBrowserDialog; $d.Description = 'Copy the template into';"
set "PS=%PS% if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath }"
if defined DEST goto copy
for /f "usebackq delims=" %%D in (`powershell -NoProfile -STA -Command "%PS%"`) do (
    set "DEST=%%D"
)
:copy
if not defined DEST (
    echo No folder chosen; nothing copied.
    goto done
)
robocopy "%SRC%" "%DEST%" /E /XD .git state todelete /XC /XN /XO /NFL /NDL /NJH /NP
if errorlevel 8 (
    echo Copy failed; robocopy's summary is above.
    set "FAIL=1"
    goto done
)
echo Copied into %DEST%. Next: open a session there and follow README steps 2-5.
:done
if "%~1"=="" pause
if defined FAIL exit /b 1
exit /b 0
