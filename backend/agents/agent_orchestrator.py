"""
Simplified Agent Orchestrator
Streamlined for demo purposes - much cleaner than the original
"""

import json
import os
from typing import Dict, Any, List
from .scope_agent import ScopeAgent
from .intent_agent import IntentAgent
from .product_agent import ProductAgent
from .troubleshooting_agent import TroubleshootingAgent
from .transaction_agent import TransactionAgent
from .response_agent import ResponseAgent
from .tools import PartSelectTools

class AgentOrchestrator:
    """Simplified orchestrator - direct tool access, no complex registration"""

    def __init__(self):
        self.tools = None
        self.parts_data = []
        self.cart = {"items": [], "total_items": 0, "subtotal": 0.0}

    async def initialize(self):
        """Simple initialization"""
        print("Initializing Simple Orchestrator...")

        # Load parts data
        await self._load_parts_data()

        # Initialize tools
        self.tools = PartSelectTools(self.parts_data)

        # Initialize agents with direct tool access (no registration needed)
        self.scope_agent = ScopeAgent()
        self.intent_agent = IntentAgent()
        self.product_agent = ProductAgent(self.tools)
        self.troubleshooting_agent = TroubleshootingAgent(self.tools)
        self.transaction_agent = TransactionAgent()
        self.response_agent = ResponseAgent()

        # Initialize vector search if available
        vector_initialized = await self.tools.initialize_vector_search()
        print("✅ Vector search ready" if vector_initialized else "⚠️ Traditional search only")
        print("✅ Simple orchestrator ready")

    async def _load_parts_data(self):
        """Load parts data from JSON files"""
        try:
            self.parts_data = []

            # Load refrigerator parts
            refrigerator_paths = [
                "data/refrigerator_parts.json",
                "../data/refrigerator_parts.json"
            ]

            for path in refrigerator_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        self.parts_data.extend(data.get('parts', []))
                    break

            # Load dishwasher parts
            dishwasher_paths = [
                "data/dishwasher_parts.json",
                "../data/dishwasher_parts.json"
            ]

            for path in dishwasher_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        self.parts_data.extend(data.get('parts', []))
                    break

            print(f"✅ Loaded {len(self.parts_data)} parts")

        except Exception as e:
            print(f"⚠️ Error loading parts data: {e}")
            self.parts_data = []

    async def process_query(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Simplified query processing pipeline"""
        try:
            print(f"Processing: {query}")

            # Step 1: Check scope
            scope_result = await self.scope_agent.process(query)
            if not scope_result.data.get("is_in_scope", True):
                return {
                    "message": "I can only help with refrigerator and dishwasher parts.",
                    "parts": [],
                    "query_type": "out_of_scope"
                }

            # Step 2: Classify intent
            intent_result = await self.intent_agent.process(query)
            intent = intent_result.data.get("intent", "general_info")
            entities = intent_result.data.get("extracted_entities", {})

            # Step 3: Route to appropriate agent
            context = {"intent": intent, "extracted_entities": entities, "conversation_history": conversation_history}

            if intent in ["part_lookup", "product_search", "compatibility_check", "installation_help"]:
                specialist_result = await self.product_agent.process(query, context)
            elif intent == "troubleshooting":
                specialist_result = await self.troubleshooting_agent.process(query, context)
            elif intent in ["purchase_intent", "add_to_cart", "cart_management"]:
                # First get part details from product agent, then process transaction
                product_result = await self.product_agent.process(query, context)
                if product_result and product_result.success:
                    # Pass product agent results to transaction agent
                    context["specialist_result"] = product_result.data
                    context["cart"] = self.cart
                    specialist_result = await self.transaction_agent.process(query, context)
                else:
                    # If product agent fails, use its result directly
                    specialist_result = product_result
            else:
                specialist_result = await self.product_agent.process(query, context)

            # Step 4: Generate response
            context["specialist_result"] = specialist_result.data if specialist_result else {}
            final_result = await self.response_agent.process(query, context)

            return final_result.data

        except Exception as e:
            print(f"Error: {e}")
            return {
                "message": "Sorry, I encountered an error. Please try again.",
                "parts": [],
                "query_type": "error"
            }

    async def process_transaction(self, transaction_data: Dict) -> Dict[str, Any]:
        """Simple transaction processing"""
        try:
            return {"success": True, "message": "Transaction processed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_cart(self) -> Dict[str, Any]:
        """Get current cart"""
        return self.cart

    async def clear_cart(self) -> Dict[str, Any]:
        """Clear cart"""
        self.cart = {"items": [], "total_items": 0, "subtotal": 0.0}
        return {"success": True}

    def get_agent_status(self) -> Dict[str, Any]:
        """Simple agent status"""
        return {
            "agents": ["scope", "intent", "product", "troubleshooting", "transaction", "response"],
            "tools_available": self.tools is not None,
            "parts_loaded": len(self.parts_data)
        }