@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title InsightFlow - Business Intelligence Workspace

echo.
echo ==========================================================
echo   INSIGHTFLOW - BUSINESS INTELLIGENCE WORKSPACE
echo ==========================================================
echo.
if not exist "app.py" (
  echo ERROR: app.py is missing. Extract the complete ZIP folder first.
  pause
  exit /b 1
)
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python Launcher ^(py^) was not found.
  echo Install Python 3.11 or newer from python.org and enable the launcher.
  pause
  exit /b 1
)
py -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.11 or newer is required.
  echo Your detected Python version is too old for this release.
  pause
  exit /b 1
)
echo Checking InsightFlow dependencies...
py -c "import streamlit,pandas,numpy,plotly,sklearn,openpyxl,xlrd,openai" >nul 2>nul
if errorlevel 1 (
  echo Installing required packages. An active internet connection is required on first launch.
  py -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed. Check your internet connection and Python installation.
    pause
    exit /b 1
  )
)
py -c "import streamlit,pandas,numpy,plotly,sklearn,openpyxl,xlrd,openai" >nul 2>nul
if errorlevel 1 (
  echo ERROR: One or more required packages are still unavailable.
  echo Run py -m pip install -r requirements.txt from this folder and retry.
  pause
  exit /b 1
)
echo Running project self-tests...
py self_test.py
if errorlevel 1 (
  echo.
  echo ERROR: The project self-test did not pass. The app was not started.
  pause
  exit /b 1
)
echo.
echo Starting InsightFlow. The launcher will select a free port.
py launch_insightflow.py
if errorlevel 1 (
  echo.
  echo InsightFlow exited with an error. Review the message above.
  pause
)
endlocal
