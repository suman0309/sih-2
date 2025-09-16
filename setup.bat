@echo off
echo Setting up Odisha Krishi AI Platform...
echo.

echo Checking if Python is installed...
python --version
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo Checking if Node.js is installed...
node --version
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo.
echo Setting up Frontend...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo Setting up Backend...
cd ..\backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo Setting up ML Service...
cd ..\ml-service
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install ML service dependencies
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo.
echo To run the application:
echo 1. Open 3 separate command prompts
echo 2. Run 'npm start' in the frontend directory
echo 3. Run 'uvicorn app:app --reload --port 8000' in the backend directory
echo 4. Run 'uvicorn app:app --reload --port 8001' in the ml-service directory
echo.
pause
