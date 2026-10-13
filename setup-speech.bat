@echo off
rem Speech for the speech_signal component, on Windows: double-click this file, or run
rem setup-speech.bat in a terminal. Run setup.bat first.
rem Installs Whisper's packages into the project's environment and fetches its model,
rem about 0.5 GB, so that switching Listen on in TouchDesigner works at once.
rem Safe to run again: what is already there is skipped.
setlocal
cd /d "%~dp0"

echo.
echo == 1/3  The project's environment
if not exist ".venv\Scripts\python.exe" (set "MSG=there is no .venv folder yet: run setup.bat first" & goto fail)
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (set "MSG=uv was not found: run setup.bat first" & goto fail)
echo Found.

echo.
echo == 2/3  Whisper's packages
uv pip install --python .venv\Scripts\python.exe -e ".[speech]"
if errorlevel 1 (set "MSG=the installation failed" & goto fail)

echo.
echo == 3/3  Whisper's model, and the microphones
.venv\Scripts\python.exe -m td_reachy.listener --prepare
if errorlevel 1 (set "MSG=Whisper could not be made ready" & goto fail)

echo.
echo Speech is ready.
echo In TouchDesigner: click speech_signal, Speech page, switch Listen on.
echo The first time, Windows may ask whether desktop apps may use the microphone.

echo.
pause
exit /b 0

:fail
echo.
echo Setup stopped: %MSG%
echo Details are above. docs\3-sense.md says more.
echo.
pause
exit /b 1
