# AI Judge - Installation & Setup Guide

## Quick Start (Windows)

### Automated Setup
```bash
# Run the setup script
setup.bat
```

### Manual Setup

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Frontend Setup
```bash
cd frontend

# Install Node.js dependencies
npm install
```

#### 3. Environment Variables

**Backend (.env in backend folder):**
```env
GROQ_API_KEY=your_groq_api_key_here
```

**Frontend (.env.local in frontend folder):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 4. Get Your Free Groq API Key
1. Visit: https://console.groq.com/
2. Sign up for free account
3. Go to API Keys section
4. Create a new API key
5. Copy and paste into backend/.env

## Running the Application

### Option 1: Using Start Script
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Troubleshooting

### Frontend Issues

**Error: Cannot find module 'react'**
```bash
cd frontend
npm install
```

**Port 3000 already in use**
```bash
# Kill the process using port 3000
npx kill-port 3000
# Or change port in package.json
```

### Backend Issues

**Error: No module named 'flask'**
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

**Port 8000 already in use**
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### API Key Issues

**Error: GROQ_API_KEY not found**
1. Create `backend/.env` file
2. Add: `GROQ_API_KEY=your_actual_key`
3. Restart backend server

## Development Tools

### Backend Testing
```bash
cd backend
pytest tests/
```

### Frontend Linting
```bash
cd frontend
npm run lint
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## System Requirements

- **Python:** 3.8 or higher
- **Node.js:** 18.0 or higher
- **RAM:** Minimum 4GB
- **OS:** Windows 10+, macOS 10.15+, Ubuntu 20.04+

## Next Steps

1. Complete the setup using `setup.bat`
2. Get your Groq API key
3. Run `start.bat`
4. Open http://localhost:3000
5. Start testing the AI Judge!

For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)
