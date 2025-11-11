#!/bin/bash

echo "========================================"
echo "AI Judge - Setup & Run Script"
echo "========================================"
echo ""

echo "[1/4] Setting up Backend..."
cd backend
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit backend/.env and add your GROQ_API_KEY"
    echo "Get free API key from: https://console.groq.com/keys"
    echo ""
    read -p "Press enter to continue after adding API key..."
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt
echo ""

echo "[2/4] Starting Backend Server..."
python app.py &
BACKEND_PID=$!
echo "Backend started on http://localhost:8000 (PID: $BACKEND_PID)"
echo ""

echo "[3/4] Setting up Frontend..."
cd ../frontend
if [ ! -d node_modules ]; then
    echo "Installing Node dependencies..."
    npm install
fi
echo ""

echo "[4/4] Starting Frontend..."
npm run dev &
FRONTEND_PID=$!
echo "Frontend will be available at http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
