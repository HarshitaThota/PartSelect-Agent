# PartSelect Agent

An AI-powered chat agent for PartSelect e-commerce, specializing in refrigerator and dishwasher parts.

## Features
- Product search and recommendations
- Model compatibility checking
- Installation guidance with videos
- Troubleshooting assistance
- Focused on refrigerator and dishwasher parts only

## Architecture
- **Frontend**: React-based chat interface
- **Backend**: FastAPI with RAG pipeline
- **AI**: Deepseek LLM integration
- **Vector Search**: Pinecone for semantic search
- **Data**: Scraped PartSelect product catalog

## Development

### Frontend
```bash
cd frontend
npm install
npm start
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---
*Instalily AI Case Study - Due: September 22, 2025*