"""
Agent Orchestrator
Coordinates all agents and manages the conversation flow
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
from .response_agent import ResponseAgent
from .tools import PartSelectTools

class AgentOrchestrator:
    """Main orchestrator that coordinates all agents"""

    def __init__(self):
        self.agents = {}
        self.tools = None
        self.parts_data = []
        self.conversation_history = []

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
            "response": ResponseAgent()
        }

        # Register tools with agents that need them
        search_agent = self.agents["search"]
        search_agent.register_tool("search_parts", self.tools.search_parts, "Search for parts")
        search_agent.register_tool("get_parts_by_category", self.tools.get_parts_by_category, "Get parts by category")

        compatibility_agent = self.agents["compatibility"]
        compatibility_agent.register_tool("check_compatibility", self.tools.check_compatibility, "Check part compatibility")
        compatibility_agent.register_tool("get_part_details", self.tools.get_part_details, "Get part details")

        installation_agent = self.agents["installation"]
        installation_agent.register_tool("get_installation_guide", self.tools.get_installation_guide, "Get installation guide")
        installation_agent.register_tool("get_part_details", self.tools.get_part_details, "Get part details")

        troubleshooting_agent = self.agents["troubleshooting"]
        troubleshooting_agent.register_tool("troubleshoot_issue", self.tools.troubleshoot_issue, "Troubleshoot issues")
        troubleshooting_agent.register_tool("find_alternative_parts", self.tools.find_alternative_parts, "Find alternative parts")

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

            else:
                # General query - route to search
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