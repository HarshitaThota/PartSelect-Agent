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
    appliance_type: Optional[str] = "refrigerator"
    category: Optional[str] = "general"
    price: float
    in_stock: Optional[bool] = True
    rating: Optional[float] = 5.0
    review_count: Optional[int] = 0
    installation: Optional[Dict[str, Any]] = {}
    compatibility: Optional[Dict[str, Any]] = {}
    troubleshooting: Optional[Dict[str, Any]] = {}
    description: Optional[str] = ""

class ChatResponse(BaseModel):
    message: str
    parts: List[PartInfo] = []
    query_type: str
    confidence: Optional[float] = None
    suggested_actions: Optional[List[str]] = []

class CartItem(BaseModel):
    part: PartInfo
    quantity: int = 1
    selected_options: Optional[Dict[str, Any]] = {}
    added_date: Optional[str] = None

class Cart(BaseModel):
    items: List[CartItem] = []
    total_items: int = 0
    subtotal: float = 0.0
    shipping_cost: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    discount_code: Optional[str] = None
    discount_amount: float = 0.0

class TransactionRequest(BaseModel):
    action: str  # "add_to_cart", "remove_from_cart", "update_quantity", "clear_cart"
    part_number: Optional[str] = None
    quantity: Optional[int] = 1
    cart_item_id: Optional[str] = None

class TransactionResponse(BaseModel):
    success: bool
    message: str
    cart: Optional[Cart] = None
    suggested_actions: Optional[List[str]] = []

class SearchResult(BaseModel):
    part: PartInfo
    relevance_score: float
    match_type: str  # "exact", "semantic", "category"