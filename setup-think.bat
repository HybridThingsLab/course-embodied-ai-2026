@echo off
rem A decision model on this computer for the brain_signal component, on Windows:
rem double-click this file, or run setup-think.bat in a terminal. Run setup.bat first,
rem and install Ollama from https://ollama.com/download - that one step is yours.
rem Then this checks Ollama, downloads the model Tev1, about 4.4 GB, and asks it one
rem sentence. Safe to run again: what is already there is skipped.
setlocal
cd /d "%~dp0"

echo.
echo == The project's environment
if not exist ".venv\Scripts\python.exe" (set "MSG=there is no .venv folder yet: run setup.bat first" & goto fail)
echo Found.

.venv\Scripts\python.exe -m td_reachy.think_setup %*
if errorlevel 1 (set "MSG=the model is not ready yet" & goto fail)

echo.
echo The model is ready.

echo.
pause
exit /b 0

:fail
echo.
echo Setup stopped: %MSG%
echo Details are above. docs\4-think.md says more.
echo.
pause
exit /b 1
