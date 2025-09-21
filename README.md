# PartSelect Agent

An AI-powered chat agent for PartSelect e-commerce, specializing in refrigerator and dishwasher parts.

## Features
- 🔍 **Smart Search**: Semantic search across 80+ appliance parts
- 🔧 **Installation Guidance**: Step-by-step repair instructions
- ✅ **Compatibility Checking**: Model number validation
- 🛠️ **Troubleshooting**: Symptom-based part recommendations
- 🎯 **Scope Enforcement**: Focused only on refrigerator/dishwasher parts
- 💬 **Multi-turn Conversations**: Context-aware chat experience

## Architecture
- **Frontend**: React + modern chat UI
- **Backend**: FastAPI + RAG pipeline
- **AI**: Deepseek LLM integration
- **Vector Search**: Pinecone + sentence-transformers
- **Data**: 80 realistic appliance parts with full metadata

## Quick Start with Docker 🐳

### Prerequisites
- Docker and Docker Compose installed
- (Optional) API keys for Deepseek, Pinecone, OpenAI

### 1. Clone and Setup
```bash
git clone https://github.com/HarshitaThota/PartSelect-Agent.git
cd PartSelect-Agent
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
# Edit .env with your API keys (or use demo mode)
```

### 3. Start the Application
```bash
docker-compose up --build
```

### 4. Access the Chat
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Demo Mode
The application works without API keys using:
- Local vector search (fallback from Pinecone)
- Template responses (fallback from Deepseek)
- 80 pre-generated appliance parts

## Example Queries
Try these in the chat interface:

**Installation Help:**
- "How can I install part number PS11752778?"
- "What tools do I need for ice maker installation?"

**Compatibility:**
- "Is this part compatible with my WDT780SAEM1 model?"
- "Will PS12364199 fit my Frigidaire dishwasher?"

**Troubleshooting:**
- "The ice maker on my Whirlpool fridge is not working"
- "My dishwasher door won't close properly"

**Product Search:**
- "I need a water filter for my refrigerator"
- "Show me door seals for Frigidaire"

## Development Setup

### Local Development (without Docker)

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Generate Fresh Data:**
```bash
cd scraper
python3 mock_data_generator.py
```

## Project Structure
```
├── frontend/          # React chat interface
├── backend/           # FastAPI + RAG engine
├── scraper/           # Data generation scripts
│   └── data/         # Parts dataset
├── docker-compose.yml # Container orchestration
└── README.md
```

## API Endpoints
- `POST /chat` - Main chat interface
- `GET /parts/search` - Search parts
- `GET /parts/{part_number}` - Get part details
- `POST /compatibility/check` - Check compatibility
- `GET /health` - System health check

## Technology Stack
- **Frontend**: React, CSS3, Modern chat UI
- **Backend**: FastAPI, Pydantic, asyncio
- **AI/ML**: Deepseek LLM, sentence-transformers
- **Vector DB**: Pinecone (with local fallback)
- **Data**: 80 realistic parts with full metadata
- **Infrastructure**: Docker, Docker Compose

---

*Instalily AI Case Study Submission*
**Candidate**: Harshita Thota
**Deadline**: September 22, 2025

## Features Implemented ✅
- [x] React-based chat interface with PartSelect styling
- [x] RAG pipeline with vector search
- [x] Deepseek LLM integration
- [x] Scope enforcement (refrigerator/dishwasher only)
- [x] Part compatibility checking
- [x] Installation guidance system
- [x] Troubleshooting recommendations
- [x] Dockerized full-stack deployment
- [x] Comprehensive dataset with 80 parts
- [x] Multi-turn conversation support