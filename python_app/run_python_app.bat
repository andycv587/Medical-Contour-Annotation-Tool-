@echo off
setlocal
set PYEXE=%LocalAppData%\Programs\Python\Python311\python.exe
if not exist "%PYEXE%" (
  echo Python not found at %PYEXE%
  exit /b 1
)
"%PYEXE%" -m pip install -r "%~dp0requirements.txt"
"%PYEXE%" "%~dp0main.py"
