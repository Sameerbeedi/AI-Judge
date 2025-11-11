@echo off
echo ========================================
echo AI Judge - Setup & Run Script
echo ========================================
echo.

echo [1/4] Setting up Backend...
cd backend
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit backend\.env and add your GROQ_API_KEY
    echo Get free API key from: https://console.groq.com/keys
    echo.
    pause
)

echo Installing Python dependencies...
pip install -r requirements.txt
echo.

echo [2/4] Starting Backend Server...
start "AI Judge Backend" cmd /k "python app.py"
echo Backend started on http://localhost:8000
echo.

echo [3/4] Setting up Frontend...
cd ..\frontend
if not exist node_modules (
    echo Installing Node dependencies...
    npm install
)
echo.

echo [4/4] Starting Frontend...
start "AI Judge Frontend" cmd /k "npm run dev"
echo Frontend will be available at http://localhost:3000
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause > nul
