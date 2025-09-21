# PartSelect AI Chat Agent

An intelligent AI-powered chat assistant for PartSelect, specializing in refrigerator and dishwasher parts with advanced agentic architecture.

## 🌟 Features
- 🔍 **Smart Part Search**: Semantic search across 27 authentic PartSelect parts
- 🔧 **Installation Guidance**: Step-by-step repair instructions with difficulty ratings
- ✅ **Compatibility Checking**: Model number validation and part fitment
- 🛠️ **Troubleshooting**: Symptom-based part recommendations and fixes
- 🎯 **Scope Enforcement**: Focused exclusively on refrigerator/dishwasher parts
- 💬 **Multi-turn Conversations**: Context-aware conversational experience
- 🤖 **6-Agent Architecture**: Specialized AI agents for different tasks

## 🏗️ Architecture

### Multi-Agent System
- **Intent Agent**: Classifies user queries and determines routing
- **Search Agent**: Handles part lookup and product discovery
- **Compatibility Agent**: Validates part-to-model compatibility
- **Installation Agent**: Provides repair guidance and instructions
- **Troubleshooting Agent**: Diagnoses issues and recommends solutions
- **Response Agent**: Orchestrates final responses with proper formatting

### Technology Stack
- **Frontend**: React with PartSelect-branded UI design
- **Backend**: FastAPI with agentic orchestration
- **AI**: Deepseek LLM integration with fallback responses
- **Data**: 27 authentic PartSelect parts (19 refrigerator + 8 dishwasher)

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd case-study

# Start with Docker
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Option 2: Local Development
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install
npm start
```

## 📁 Project Structure
```
case-study/
├── backend/                    # FastAPI backend
│   ├── agents/                # Multi-agent system
│   │   ├── agent_orchestrator.py  # Main orchestrator
│   │   ├── intent_agent.py        # Query classification
│   │   ├── search_agent.py        # Part search & discovery
│   │   ├── compatibility_agent.py # Model compatibility
│   │   ├── installation_agent.py  # Repair guidance
│   │   ├── troubleshooting_agent.py # Issue diagnosis
│   │   ├── response_agent.py      # Response formatting
│   │   ├── tools.py               # Shared utilities
│   │   └── base_agent.py          # Agent base class
│   ├── main.py                # FastAPI app entry point
│   ├── models.py              # Pydantic data models
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container config
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatWindow.js      # Main chat interface
│   │   ├── api/
│   │   │   └── api.js             # Backend API calls
│   │   ├── App.js                 # Main React component
│   │   └── index.js               # React entry point
│   ├── package.json           # Node dependencies
│   └── Dockerfile            # Frontend container config
│
├── data/                      # Parts dataset
│   ├── refrigerator_parts.json   # 19 authentic parts
│   └── dishwasher_parts.json     # 8 authentic parts
│
├── docker-compose.yml         # Container orchestration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🗃️ Data Overview
- **Total Parts**: 27 authentic PartSelect parts
- **Refrigerator Parts**: 19 (ice dispensers, filters, door components)
- **Dishwasher Parts**: 8 (spray arms, heating elements, gaskets)
- **Part Details**: Full metadata including prices, compatibility, installation guides

## 💬 Example Queries

### Installation Help
- "How can I install part number PS11752778?"
- "What tools do I need for ice maker installation?"
- "Show me installation steps for dishwasher door gasket"

### Compatibility Check
- "Is PS11752778 compatible with my Whirlpool refrigerator?"
- "Will this part fit my model WDT780SAEM1?"
- "Can I use PS12364199 in my Frigidaire dishwasher?"

### Troubleshooting
- "My ice maker is not working"
- "Dishwasher door won't close properly"
- "Water dispenser is leaking"

### Product Search
- "I need a water filter for my refrigerator"
- "Show me door seals for Frigidaire"
- "Find dishwasher spray arms"

## 🛠️ API Endpoints
- `POST /chat` - Main chat interface
- `GET /health` - System health check
- `GET /docs` - Interactive API documentation

## 🌐 Environment Variables
Create a `.env` file (optional - works without keys):
```bash
DEEPSEEK_API_KEY=your_deepseek_key  # Optional: Uses fallback if not provided
```

## 🧪 Agent System Details

### Intent Classification
- **part_lookup**: Direct part number searches
- **product_search**: Category and feature-based searches
- **compatibility_check**: Model compatibility validation
- **installation_help**: Repair and installation guidance
- **troubleshooting**: Problem diagnosis and solutions
- **general_info**: General appliance questions
- **out_of_scope**: Non-appliance queries (redirected)

### Tool Integration
Each agent has access to specialized tools:
- **search_parts()**: Semantic part search
- **get_parts_by_category()**: Category filtering
- **check_compatibility()**: Model validation
- **get_installation_guide()**: Repair instructions
- **diagnose_issue()**: Problem identification

## 🎨 UI Features
- **PartSelect Branding**: Authentic color scheme and typography
- **Real-time Chat**: Instant responses with typing indicators
- **Responsive Design**: Works on desktop and mobile
- **Clean Interface**: Focused on part assistance

## 🚢 Deployment
The application is fully containerized and production-ready:
- **Multi-stage Docker builds** for optimization
- **Health checks** for reliability
- **Volume persistence** for data
- **Environment-based configuration**

---

## 📋 Case Study Information
**Project**: Instalily AI PartSelect Chat Agent
**Candidate**: Harshita Thota
**Timeline**: 2-day implementation
**Date**: September 2025

### ✅ Requirements Completed
- [x] React-based chat interface with PartSelect styling
- [x] Multi-agent backend architecture (6 specialized agents)
- [x] Deepseek LLM integration with intelligent fallbacks
- [x] Scope enforcement (refrigerator/dishwasher only)
- [x] Part compatibility checking and validation
- [x] Installation guidance with step-by-step instructions
- [x] Troubleshooting and issue diagnosis
- [x] Dockerized full-stack deployment
- [x] Authentic PartSelect dataset (27 parts)
- [x] Multi-turn conversation support
- [x] Production-ready configuration

### 🏆 Key Achievements
- **Advanced Agent Architecture**: 6 specialized AI agents working in concert
- **Authentic Data**: Real PartSelect parts with complete metadata
- **Production Quality**: Full Docker deployment with health checks
- **User Experience**: Beautiful PartSelect-branded interface
- **Robust Fallbacks**: Works with or without external API keys
- **Comprehensive Coverage**: All major appliance part scenarios handled