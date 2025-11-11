@echo off
echo ================================
echo AI Judge - Setup Script
echo ================================
echo.

echo [1/3] Setting up Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

cd ..

echo.
echo [2/3] Setting up Frontend...
cd frontend

echo Installing Node.js dependencies...
call npm install

cd ..

echo.
echo [3/3] Setup complete!
echo.
echo ================================
echo To start the application:
echo ================================
echo Option 1 (Recommended): Run start.bat
echo Option 2 (Manual):
echo   - Backend: cd backend ^&^& venv\Scripts\activate ^&^& python app.py
echo   - Frontend: cd frontend ^&^& npm run dev
echo ================================
echo.
pause
