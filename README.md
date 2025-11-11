# AI Judge - Digital Justice System

An AI-powered mock trial platform that simulates legal proceedings with intelligent verdict generation and follow-up arguments.

## Architecture

### Backend (Python/FastAPI)
- RESTful API with FastAPI
- Groq API integration (llama-3.1-70b-versatile model)
- Document processing (PDF, DOCX, TXT)
- In-memory case management (scalable to Redis/PostgreSQL)

### Frontend (Next.js/React/TypeScript)
- Server-side rendering with Next.js 14
- Real-time UI updates
- Drag-and-drop file uploads
- Responsive design with Tailwind CSS

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## API Key Setup

Get free Groq API key from: https://console.groq.com/keys

Add to `backend/.env`:
```
GROQ_API_KEY=your_key_here
```

## Deployment

### Vercel (Frontend)
- Deploy from GitHub
- Add `NEXT_PUBLIC_API_URL` environment variable
- Build command: `cd frontend && npm run build`

### Backend Options
- Railway.app (Free tier)
- Render.com (Free tier)
- AWS Lambda/Azure Functions

## Project Structure
```
vaquil/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment template
├── frontend/
│   ├── app/
│   │   ├── page.tsx       # Main application
│   │   ├── layout.tsx     # Root layout
│   │   └── globals.css    # Global styles
│   ├── package.json       # Node dependencies
│   └── next.config.js     # Next.js config
└── vercel.json            # Vercel deployment
```

## Features Implemented

✅ Two-sided case submission (A vs B)
✅ Multi-format document upload (PDF, DOCX, TXT)
✅ AI-powered verdict generation
✅ Follow-up argument system (max 5 rounds)
✅ Real-time UI updates
✅ Professional legal interface
✅ Groq API integration (free tier)

## Scaling Strategy

### For 1000s of Users
1. **Database**: PostgreSQL for case storage
2. **Caching**: Redis for session management
3. **Queue**: Celery for async processing
4. **CDN**: Cloudflare for static assets
5. **Load Balancer**: Nginx/AWS ALB
6. **Monitoring**: Prometheus + Grafana
7. **Secrets**: AWS Secrets Manager / HashiCorp Vault

### Production Deployment
- **Container**: Docker + Kubernetes
- **CI/CD**: GitHub Actions
- **Infrastructure**: Terraform
- **Cloud**: AWS/GCP/Azure
- **Telemetry**: OpenTelemetry + DataDog

## Product Improvements

1. **Multi-language Support**: Support international jurisdictions
2. **Precedent Database**: Search similar cases
3. **Evidence Scoring**: AI rates evidence strength
4. **Expert Witnesses**: Simulate expert testimonies
5. **Appeal System**: Multi-tier judgment process
6. **Collaboration**: Multiple lawyers per side
7. **Analytics Dashboard**: Case statistics
8. **Legal Citation**: Automatic case law references
9. **Timeline View**: Case chronology
10. **Video Evidence**: Multimedia support

## Impact on Judicial System

### Benefits
- **Legal Education**: Law students practice mock trials
- **Case Preparation**: Lawyers test arguments
- **Access to Justice**: Affordable legal simulation
- **Precedent Analysis**: Quick case law research
- **Settlement Prediction**: Early case assessment
- **Bias Reduction**: Neutral AI analysis

### Indian Jurisdiction Applications
- Pre-litigation assessment
- Arbitration preparation
- Legal aid expansion
- Judge training
- Case backlog analysis
- Consumer court simulations
