# AI JUDGE - Quick Start Guide

## Get Your Free Groq API Key
1. Go to https://console.groq.com/
2. Sign up for free
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

## Setup

### Option 1: Automatic (Windows)
```bash
start.bat
```

### Option 2: Automatic (Mac/Linux)
```bash
chmod +x start.sh
./start.sh
```

### Option 3: Manual Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
# Create .env file and add: GROQ_API_KEY=your_key_here
python app.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Vercel Deployment (Frontend)

1. Push code to GitHub
2. Import project in Vercel
3. Set root directory to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL` = your backend URL
5. Deploy

## Backend Deployment Options

### Railway.app (Free)
```bash
railway login
railway init
railway up
```

### Render.com (Free)
1. Connect GitHub repo
2. Set root directory to `backend`
3. Add environment variable: `GROQ_API_KEY`
4. Deploy

### Docker
```bash
docker-compose up
```

## Testing the API

```bash
# Health check
curl http://localhost:8000/

# Create a case
curl -X POST http://localhost:8000/api/case/create \
  -H "Content-Type: application/json" \
  -d '{"case_id": "test123"}'
```

## Features
✅ Two-sided legal case submission
✅ Document upload (PDF, DOCX, TXT)
✅ AI-powered verdicts using Groq (Free!)
✅ Follow-up arguments (max 5)
✅ Beautiful UI with animations
✅ Production-ready architecture
✅ Kubernetes deployment configs
✅ CI/CD pipeline ready

## Why Groq?
- **FREE tier** with generous limits
- **10x faster** than OpenAI
- **70B parameter model** (llama-3.1)
- No credit card required
- Perfect for legal reasoning tasks

Enjoy your AI Judge! 🏛️⚖️
