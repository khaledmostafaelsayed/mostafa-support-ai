@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 goto error
)
call ".venv\Scripts\activate.bat"
echo Installing requirements (first run may take a few minutes)...
python -m pip install --upgrade pip
if errorlevel 1 goto error
python -m pip install -r requirements.txt
if errorlevel 1 goto error
echo Starting Mostafa Support AI in your browser...
python -m streamlit run app.py
if errorlevel 1 goto error
goto end
:error
echo.
echo Something failed. Check that Python is installed and the internet is available.
pause
:end
endlocal
