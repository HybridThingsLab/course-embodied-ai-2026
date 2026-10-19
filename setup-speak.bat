@echo off
rem Speaking, for the speaker component, on Windows: double-click this file, or run
rem setup-speak.bat in a terminal. Run setup.bat first.
rem Installs the speaker's packages into the project's environment, fetches Kokoro's
rem model, about 350 MB, and says a sentence, so that the speaker in TouchDesigner speaks
rem at once. The other engines - Supertonic, Piper - fetch theirs the first time they
rem speak; Edge's voices need none. Safe to run again: what is already there is skipped.
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
echo == 2/3  The speaker's packages
uv pip install --python .venv\Scripts\python.exe -e ".[speak]"
if errorlevel 1 (set "MSG=the installation failed" & goto fail)

echo.
echo == 3/3  Kokoro's model, and a sentence to hear
.venv\Scripts\python.exe -m td_reachy.speaker --prepare
if errorlevel 1 (set "MSG=Kokoro could not be made ready" & goto fail)

echo.
echo Speaking is ready.
echo In TouchDesigner: click speaker, Speaker page, type a sentence into Text, Enter.

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
