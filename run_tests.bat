@echo off
setlocal enabledelayedexpansion

:: Keep console open if executed by double-click
rem if "%~1"=="" (
rem     cmd /k "%~f0" keepopen
rem     exit /b
rem )

cd /d "%~dp0" || (
    echo ERROR: Failed to change directory to script location
    pause
    exit /b 1
)

:: Virtual Environment Activation
if not exist venv\ (
    echo ERROR: venv not found. Create with: python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat || (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Set Flask Environment for Testing
set FLASK_APP=app:create_app(TestingConfig)  :: Point to your app factory and use TestingConfig
set FLASK_ENV=testing                 :: Use 'testing' or 'development' if needed by config loading

:: Pytest Command Base
set "pytest_cmd=python -m pytest -v --cov=app --cov-report=term-missing"
set "test_target=tests" :: Default to run all tests in the tests directory

:: Handle Arguments
if "%~1"=="html" (
    set "pytest_cmd=!pytest_cmd! --cov-report=html:coverage_report" :: Changed output dir
    echo HTML coverage report requested.
) else if "%~1"=="auth" (
    set "test_target=tests/test_auth.py"
    echo Running only auth tests.
) else if "%~1"=="projects" (
    set "test_target=tests/test_projects.py"
    echo Running only project tests.
) else if "%~1"=="assessments" (
    set "test_target=tests/test_assessments.py"
    echo Running only assessment tests.
) else if "%~1"=="failed" (
    set "pytest_cmd=!pytest_cmd! --last-failed"
    echo Running only last failed tests.
) else if "%~1" neq "" and "%~1" neq "keepopen" (
    echo Unknown argument: %1. Running all tests.
)

:: Run Tests
echo Cleaning up old coverage data...
if exist .coverage del .coverage
if exist coverage_report rd /s /q coverage_report

echo Running: !pytest_cmd! !test_target!
!pytest_cmd! !test_target!

:: Check for HTML report and display path
if exist coverage_report\index.html (
    echo Coverage report generated: file:///%cd%/coverage_report/index.html
)

echo Test run complete.

:: Deactivate (optional)
rem call venv\Scripts\deactivate.bat

if "%~1"=="keepopen" pause

endlocal