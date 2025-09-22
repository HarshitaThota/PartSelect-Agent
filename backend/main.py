from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv("../.env")

# modules
from models import ChatRequest, ChatResponse, PartInfo, TransactionRequest, TransactionResponse, Cart
from agents.agent_orchestrator import AgentOrchestrator

app = FastAPI(title="PartSelect Chat Agent API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_orchestrator = None

@app.on_event("startup")
async def startup_event():
    global agent_orchestrator
    try:
        agent_orchestrator = AgentOrchestrator()
        await agent_orchestrator.initialize()
        print("Agent Orchestrator initialized successfully")
    except Exception as e:
        print(f"Error initializing Agent Orchestrator: {e}")

@app.get("/")
async def root():
    return {"message": "PartSelect Chat Agent API", "status": "running"}

@app.get("/health")
async def health_check():
    health_data = {
        "status": "healthy",
        "agent_orchestrator": agent_orchestrator is not None,
        "agents_loaded": len(agent_orchestrator.agents) if agent_orchestrator else 0,
        "services": {}
    }

    if agent_orchestrator:
        # Deepseek model status
        response_agent = agent_orchestrator.agents.get("response")
        if response_agent:
            deepseek_key = response_agent.deepseek_api_key
            health_data["services"]["deepseek"] = {
                "configured": bool(deepseek_key and deepseek_key != "demo_key"),
                "model": "deepseek-chat",
                "api_url": "https://api.deepseek.com/v1",
                "status": "active" if deepseek_key and deepseek_key != "demo_key" else "fallback"
            }

        # Vector Search status
        if hasattr(agent_orchestrator, 'tools') and agent_orchestrator.tools:
            vector_available = agent_orchestrator.tools.vector_search.is_available()
            health_data["services"]["vector_search"] = {
                "configured": vector_available,
                "pinecone_index": os.getenv("PINECONE_INDEX_NAME", "partselect-parts"),
                "openai_model": "text-embedding-3-small",
                "dimensions": 512,
                "status": "active" if vector_available else "disabled"
            }

        # parts data
        parts_count = len(agent_orchestrator.parts_data) if hasattr(agent_orchestrator, 'parts_data') else 0
        health_data["services"]["parts_data"] = {
            "total_parts": parts_count,
            "status": "loaded" if parts_count > 0 else "empty"
        }

    return health_data

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        # query through agent pipeline
        result = await agent_orchestrator.process_query(
            query=request.message,
            conversation_history=request.conversation_history
        )

        print(f"DEBUG: Result from orchestrator: {result}")

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
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
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
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        result = await agent_orchestrator.tools.check_compatibility(part_number, model_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compatibility check error: {str(e)}")

@app.post("/cart/add")
async def add_to_cart(request: TransactionRequest):
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        result = await agent_orchestrator.process_transaction(request.dict())
        return TransactionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart operation failed: {str(e)}")

@app.get("/cart")
async def get_cart():
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        cart = agent_orchestrator.get_cart()
        return cart
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cart: {str(e)}")

@app.post("/cart/update")
async def update_cart(request: TransactionRequest):
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        result = await agent_orchestrator.process_transaction(request.dict())
        return TransactionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart update failed: {str(e)}")

@app.delete("/cart/clear")
async def clear_cart():
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    try:
        result = await agent_orchestrator.clear_cart()
        return {"success": True, "message": "Cart cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cart: {str(e)}")

@app.get("/agents/status")
async def get_agent_status():
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")

    return agent_orchestrator.get_agent_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)