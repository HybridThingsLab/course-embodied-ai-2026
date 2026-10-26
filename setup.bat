@echo off
rem One-time setup on Windows: double-click this file, or run setup.bat in a terminal.
rem Installs uv if needed, creates the project's Python environment .venv, installs
rem the robot software and the simulator, then starts everything once as a check.
rem Safe to run again: steps that are already done are skipped or quick.
setlocal
cd /d "%~dp0"

echo.
echo == 1/4  uv, which manages Python
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
    echo Installing uv from astral.sh ...
    powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
)
where uv >nul 2>nul
if errorlevel 1 (set "MSG=uv could not be installed" & goto fail)
uv --version

echo.
echo == 2/4  Python environment .venv
if exist ".venv\Scripts\python.exe" (
    echo Already there - keeping it. To start fresh, delete the .venv folder and run this again.
) else (
    uv venv --python 3.12 --managed-python
    if errorlevel 1 (set "MSG=the environment could not be created" & goto fail)
)

echo.
echo == 3/4  Robot software, bridge and simulator - a few hundred MB the first time
uv pip install --python .venv\Scripts\python.exe -e ".[sim]"
if errorlevel 1 (set "MSG=the installation failed" & goto fail)

echo.
echo == 4/4  Check: start the simulator and the bridge once, then stop
echo The very first start can take a few minutes.
.venv\Scripts\python.exe -m td_reachy.station --headless --check
if errorlevel 1 (set "MSG=the check did not pass" & goto fail)

echo.
echo Setup complete.
echo Next: open touchdesigner\01_puppet.toe in TouchDesigner - docs\getting-started.md, step 4.
echo From now on the robot software starts from TouchDesigner - reachy_hub's Station page -
echo or in a terminal: .venv\Scripts\python.exe -m td_reachy.station
echo.
pause
exit /b 0

:fail
echo.
echo Setup stopped: %MSG%
echo Details are above. The troubleshooting list in docs\getting-started.md covers the usual causes.
echo.
pause
exit /b 1
