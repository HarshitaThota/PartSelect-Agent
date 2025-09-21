from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class PartInfo(BaseModel):
    partselect_number: str
    manufacturer_part_number: str
    name: str
    brand: str
    appliance_type: str
    category: str
    price: float
    in_stock: bool
    rating: float
    review_count: int
    installation: Dict[str, Any]
    compatibility: Dict[str, Any]
    troubleshooting: Dict[str, Any]
    description: str

class ChatResponse(BaseModel):
    message: str
    parts: List[PartInfo] = []
    query_type: str
    confidence: Optional[float] = None
    suggested_actions: Optional[List[str]] = []

class SearchResult(BaseModel):
    part: PartInfo
    relevance_score: float
    match_type: str  # "exact", "semantic", "category"