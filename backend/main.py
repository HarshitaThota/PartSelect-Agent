from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from models import ChatRequest, ChatResponse, PartInfo
from agents.agent_orchestrator import AgentOrchestrator

app = FastAPI(title="PartSelect Chat Agent API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent Orchestrator
agent_orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize Agent Orchestrator on startup"""
    global agent_orchestrator
    try:
        agent_orchestrator = AgentOrchestrator()
        await agent_orchestrator.initialize()
        print("✅ Agent Orchestrator initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Agent Orchestrator: {e}")

@app.get("/")
async def root():
    return {"message": "PartSelect Chat Agent API", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent_orchestrator": agent_orchestrator is not None,
        "agents_loaded": len(agent_orchestrator.agents) if agent_orchestrator else 0
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        # Process the query through agent pipeline
        result = await agent_orchestrator.process_query(
            query=request.message,
            conversation_history=request.conversation_history
        )

        # Convert to ChatResponse format
        parts = [PartInfo(**part) for part in result.get("parts", [])]

        return ChatResponse(
            message=result.get("message", "I couldn't process your request."),
            parts=parts,
            query_type=result.get("query_type", "unknown"),
            confidence=result.get("confidence"),
            suggested_actions=result.get("suggested_actions", [])
        )

    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/parts/search")
async def search_parts(q: str, limit: int = 10):
    """Search parts endpoint"""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        results = await agent_orchestrator.tools.search_parts(q, limit=limit)
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/parts/{part_number}")
async def get_part_details(part_number: str):
    """Get specific part details"""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        part = await agent_orchestrator.tools.get_part_details(part_number)
        if not part:
            raise HTTPException(status_code=404, detail="Part not found")
        return part
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving part: {str(e)}")

@app.post("/compatibility/check")
async def check_compatibility(part_number: str, model_number: str):
    """Check part compatibility with model"""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        result = await agent_orchestrator.tools.check_compatibility(part_number, model_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compatibility check error: {str(e)}")

@app.get("/agents/status")
async def get_agent_status():
    """Get status of all agents"""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    return agent_orchestrator.get_agent_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)