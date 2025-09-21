"""
Agent Orchestrator
Coordinates all agents and manages the conversation flow fr 
"""

import json
import os
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult
from .intent_agent import IntentAgent
from .search_agent import SearchAgent
from .compatibility_agent import CompatibilityAgent
from .installation_agent import InstallationAgent
from .troubleshooting_agent import TroubleshootingAgent
from .transaction_agent import TransactionAgent
from .response_agent import ResponseAgent
from .tools import PartSelectTools

class AgentOrchestrator:
    """Main orchestrator that coordinates all agents"""

    def __init__(self):
        self.agents = {}
        self.tools = None
        self.parts_data = []
        self.conversation_history = []
        self.cart = {
            "items": [],
            "total_items": 0,
            "subtotal": 0.0,
            "shipping_cost": 0.0,
            "tax": 0.0,
            "total": 0.0
        }

    async def initialize(self):
        """Initialize all agents and tools"""
        print("🤖 Initializing Agent Orchestrator...")

        # Load parts data
        await self._load_parts_data()

        # Initialize tools
        self.tools = PartSelectTools(self.parts_data)

        # Initialize all agents
        self.agents = {
            "intent": IntentAgent(),
            "search": SearchAgent(),
            "compatibility": CompatibilityAgent(),
            "installation": InstallationAgent(),
            "troubleshooting": TroubleshootingAgent(),
            "transaction": TransactionAgent(),
            "response": ResponseAgent()
        }

        # Register tools with agents that need them
        search_agent = self.agents["search"]
        search_agent.register_tool("search_parts", self.tools.search_parts, "Search for parts")
        search_agent.register_tool("get_parts_by_category", self.tools.get_parts_by_category, "Get parts by category")
        search_agent.register_tool("get_part_details", self.tools.get_part_details, "Get part details")

        compatibility_agent = self.agents["compatibility"]
        compatibility_agent.register_tool("check_compatibility", self.tools.check_compatibility, "Check part compatibility")
        compatibility_agent.register_tool("get_part_details", self.tools.get_part_details, "Get part details")

        installation_agent = self.agents["installation"]
        installation_agent.register_tool("get_installation_guide", self.tools.get_installation_guide, "Get installation guide")
        installation_agent.register_tool("get_part_details", self.tools.get_part_details, "Get part details")

        troubleshooting_agent = self.agents["troubleshooting"]
        troubleshooting_agent.register_tool("troubleshoot_issue", self.tools.troubleshoot_issue, "Troubleshoot issues")
        troubleshooting_agent.register_tool("find_alternative_parts", self.tools.find_alternative_parts, "Find alternative parts")

        # Initialize vector search if available
        print("🔄 Initializing vector search...")
        vector_initialized = await self.tools.initialize_vector_search()
        if vector_initialized:
            print("✅ Vector search initialized successfully")
            # Note: semantic search is now integrated into search_parts method
            # No need to register separate semantic search tools
        else:
            print("⚠️ Vector search not available - using traditional search only")

        print(f"✅ Initialized {len(self.agents)} agents with tools")

    async def _load_parts_data(self):
        """Load parts data from JSON files"""
        try:
            self.parts_data = []

            # Load refrigerator parts
            refrigerator_paths = [
                "data/refrigerator_parts.json",
                "../data/refrigerator_parts.json",
                "/app/data/refrigerator_parts.json"
            ]

            refrigerator_file = None
            for path in refrigerator_paths:
                if os.path.exists(path):
                    refrigerator_file = path
                    break

            if refrigerator_file:
                with open(refrigerator_file, 'r') as f:
                    data = json.load(f)
                    refrigerator_parts = data.get('parts', [])
                    self.parts_data.extend(refrigerator_parts)
                print(f"📦 Loaded {len(refrigerator_parts)} refrigerator parts from {refrigerator_file}")

            # Load dishwasher parts
            dishwasher_paths = [
                "data/dishwasher_parts.json",
                "../data/dishwasher_parts.json",
                "/app/data/dishwasher_parts.json"
            ]

            dishwasher_file = None
            for path in dishwasher_paths:
                if os.path.exists(path):
                    dishwasher_file = path
                    break

            if dishwasher_file:
                with open(dishwasher_file, 'r') as f:
                    data = json.load(f)
                    dishwasher_parts = data.get('parts', [])
                    self.parts_data.extend(dishwasher_parts)
                print(f"📦 Loaded {len(dishwasher_parts)} dishwasher parts from {dishwasher_file}")

            if not self.parts_data:
                print("⚠️ No parts data files found, using empty dataset")
                print(f"Looked for refrigerator parts in: {refrigerator_paths}")
                print(f"Looked for dishwasher parts in: {dishwasher_paths}")

            print(f"📊 Total parts loaded: {len(self.parts_data)}")

        except Exception as e:
            print(f"❌ Error loading parts data: {e}")
            self.parts_data = []

    async def process_query(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process a user query through the agent pipeline"""
        try:
            print(f"🎯 Processing query: {query}")

            # Update conversation history
            if conversation_history:
                self.conversation_history = conversation_history

            # Step 1: Intent Classification
            intent_result = await self.agents["intent"].process(query)
            print(f"🧠 Intent: {intent_result.data.get('intent')} ({intent_result.data.get('confidence', 0):.1%})")

            if not intent_result.success:
                return self._create_error_response("Intent classification failed")

            intent_data = intent_result.data
            intent = intent_data.get("intent")

            # Check for out of scope
            if intent == "out_of_scope":
                return {
                    "message": "I can only help with refrigerator and dishwasher parts. Please ask about appliance parts, installation, compatibility, or troubleshooting.",
                    "parts": [],
                    "query_type": "out_of_scope",
                    "agent_trace": ["intent"]
                }

            # Step 2: Route to appropriate specialist agent
            agent_trace = ["intent"]
            specialist_result = None

            print(f"🎯 Routing query with intent: {intent}")

            if intent in ["part_lookup", "product_search"]:
                specialist_result = await self._handle_search(query, intent_data)
                agent_trace.append("search")

            elif intent == "compatibility_check":
                specialist_result = await self._handle_compatibility(query, intent_data)
                agent_trace.append("compatibility")

            elif intent == "installation_help":
                specialist_result = await self._handle_installation(query, intent_data)
                agent_trace.append("installation")

            elif intent == "troubleshooting":
                specialist_result = await self._handle_troubleshooting(query, intent_data)
                agent_trace.append("troubleshooting")

            elif intent in ["purchase_intent", "purchase_confirmation", "cart_operations", "pricing_inquiry", "checkout_assistance"]:
                print(f"🛒 Routing to transaction agent for intent: {intent}")
                specialist_result = await self._handle_transaction(query, intent_data)
                agent_trace.append("transaction")

            else:
                # General query - route to search
                print(f"🔍 Routing to search agent for unknown intent: {intent}")
                specialist_result = await self._handle_search(query, intent_data)
                agent_trace.append("search")

            if not specialist_result or not specialist_result.success:
                return self._create_error_response("Specialist agent processing failed")

            # Step 3: Generate response
            response_result = await self.agents["response"].process(
                query,
                {
                    "intent": intent_data,
                    "specialist_result": specialist_result.data,
                    "conversation_history": self.conversation_history
                }
            )
            agent_trace.append("response")

            if not response_result.success:
                return self._create_error_response("Response generation failed")

            # Step 4: Format final response
            return {
                "message": response_result.data.get("formatted_response", "I couldn't process your request."),
                "parts": specialist_result.data.get("parts", []),
                "query_type": intent,
                "confidence": intent_data.get("confidence", 0),
                "agent_trace": agent_trace,
                "tools_used": specialist_result.tools_used
            }

        except Exception as e:
            print(f"❌ Error in orchestrator: {e}")
            return self._create_error_response(f"Processing error: {str(e)}")

    async def _handle_search(self, query: str, intent_data: Dict) -> AgentResult:
        """Handle search-related queries"""
        return await self.agents["search"].process(query, intent_data)

    async def _handle_compatibility(self, query: str, intent_data: Dict) -> AgentResult:
        """Handle compatibility check queries"""
        return await self.agents["compatibility"].process(query, intent_data)

    async def _handle_installation(self, query: str, intent_data: Dict) -> AgentResult:
        """Handle installation help queries"""
        return await self.agents["installation"].process(query, intent_data)

    async def _handle_troubleshooting(self, query: str, intent_data: Dict) -> AgentResult:
        """Handle troubleshooting queries"""
        return await self.agents["troubleshooting"].process(query, intent_data)

    async def _handle_transaction(self, query: str, intent_data: Dict) -> AgentResult:
        """Handle transaction-related queries"""
        print(f"🛒 Orchestrator _handle_transaction called with query: {query}")
        print(f"🛒 Intent data: {intent_data}")

        # Check if this is a purchase intent with part number - route to search first
        if intent_data.get("intent") == "purchase_intent":
            entities = intent_data.get("extracted_entities", {})
            part_numbers = entities.get("part_numbers", [])

            if part_numbers:
                print(f"🛒 Purchase intent with part number {part_numbers[0]}, routing to search first")
                # Route to search first to find the part
                search_result = await self.agents["search"].process(query, intent_data)

                if search_result.success and search_result.data.get("parts"):
                    # Pass parts to transaction agent
                    enhanced_context = intent_data.copy()
                    enhanced_context["specialist_result"] = search_result.data
                    print(f"🛒 Found {len(search_result.data.get('parts', []))} parts, passing to transaction agent")
                    return await self.agents["transaction"].process(query, enhanced_context)
                else:
                    print(f"🛒 No parts found in search, continuing with transaction agent anyway")
                    # No parts found, but still process with transaction agent for proper error handling
                    return await self.agents["transaction"].process(query, intent_data)


        # Check if this is a cart add request that needs parts
        if ("add" in query.lower() and
            any(appliance in query.lower() for appliance in ["refrigerator", "fridge", "dishwasher", "ice"])):

            # Route to search first to get parts, then handle transaction
            search_query = query.lower()
            if "refrigerator" in search_query or "fridge" in search_query:
                search_query = "refrigerator parts"
            elif "dishwasher" in search_query:
                search_query = "dishwasher parts"
            elif "ice" in search_query:
                search_query = "ice maker parts"

            # Get parts from search agent
            search_result = await self.agents["search"].process(search_query, intent_data)

            if search_result.success and search_result.data.get("parts"):
                # Pass parts to transaction agent
                enhanced_context = intent_data.copy()
                enhanced_context["specialist_result"] = search_result.data
                return await self.agents["transaction"].process(query, enhanced_context)

        return await self.agents["transaction"].process(query, intent_data)

    async def process_transaction(self, transaction_data: Dict) -> Dict[str, Any]:
        """Process cart/transaction operations"""
        action = transaction_data.get("action")
        part_number = transaction_data.get("part_number")
        quantity = transaction_data.get("quantity", 1)

        if action == "add_to_cart":
            return await self._add_to_cart(part_number, quantity)
        elif action == "remove_from_cart":
            return await self._remove_from_cart(part_number)
        elif action == "update_quantity":
            return await self._update_cart_quantity(part_number, quantity)
        elif action == "clear_cart":
            return await self._clear_cart()
        else:
            return {"success": False, "message": "Invalid action"}

    async def _add_to_cart(self, part_number: str, quantity: int) -> Dict[str, Any]:
        """Add item to cart"""
        # Find the part
        part = next((p for p in self.parts_data if p["partselect_number"] == part_number), None)
        if not part:
            return {"success": False, "message": "Part not found"}

        # Check if item already in cart
        existing_item = next((item for item in self.cart["items"] if item["part"]["partselect_number"] == part_number), None)

        if existing_item:
            existing_item["quantity"] += quantity
        else:
            self.cart["items"].append({
                "part": part,
                "quantity": quantity,
                "selected_options": {},
                "added_date": None
            })

        self._update_cart_totals()
        return {
            "success": True,
            "message": f"Added {part['name']} to cart",
            "cart": self.cart
        }

    async def _remove_from_cart(self, part_number: str) -> Dict[str, Any]:
        """Remove item from cart"""
        original_count = len(self.cart["items"])
        self.cart["items"] = [item for item in self.cart["items"] if item["part"]["partselect_number"] != part_number]

        if len(self.cart["items"]) < original_count:
            self._update_cart_totals()
            return {"success": True, "message": "Item removed from cart", "cart": self.cart}
        else:
            return {"success": False, "message": "Item not found in cart"}

    async def _update_cart_quantity(self, part_number: str, quantity: int) -> Dict[str, Any]:
        """Update item quantity in cart"""
        item = next((item for item in self.cart["items"] if item["part"]["partselect_number"] == part_number), None)

        if item:
            if quantity <= 0:
                return await self._remove_from_cart(part_number)
            else:
                item["quantity"] = quantity
                self._update_cart_totals()
                return {"success": True, "message": "Quantity updated", "cart": self.cart}
        else:
            return {"success": False, "message": "Item not found in cart"}

    def _update_cart_totals(self):
        """Update cart totals"""
        total_items = sum(item["quantity"] for item in self.cart["items"])
        subtotal = sum(item["part"]["price"] * item["quantity"] for item in self.cart["items"])

        # Calculate shipping (free over $50)
        shipping_cost = 0.0 if subtotal >= 50 else 15.99

        # Calculate tax (8.5%)
        tax = subtotal * 0.085

        # Calculate total
        total = subtotal + shipping_cost + tax

        self.cart.update({
            "total_items": total_items,
            "subtotal": round(subtotal, 2),
            "shipping_cost": round(shipping_cost, 2),
            "tax": round(tax, 2),
            "total": round(total, 2)
        })

    def get_cart(self) -> Dict[str, Any]:
        """Get current cart"""
        return self.cart

    async def clear_cart(self) -> Dict[str, Any]:
        """Clear cart"""
        self.cart = {
            "items": [],
            "total_items": 0,
            "subtotal": 0.0,
            "shipping_cost": 0.0,
            "tax": 0.0,
            "total": 0.0
        }
        return {"success": True, "message": "Cart cleared"}

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "message": "I'm sorry, I encountered an error processing your request. Please try rephrasing your question.",
            "parts": [],
            "query_type": "error",
            "error": error_message,
            "agent_trace": ["error"]
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "agents_loaded": len(self.agents),
            "parts_data_loaded": len(self.parts_data),
            "tools_available": bool(self.tools),
            "agent_list": list(self.agents.keys())
        }