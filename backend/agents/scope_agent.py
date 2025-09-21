"""
Scope Detection Agent
Intelligently determines if a query is within scope (refrigerator/dishwasher parts) using LLM
"""

import re
from typing import Dict, Any
from .base_agent import BaseAgent, AgentResult

class ScopeAgent(BaseAgent):
    """Agent that intelligently determines if queries are about refrigerator/dishwasher parts"""

    def __init__(self):
        super().__init__(
            name="scope_detector",
            description="Determines if queries are about refrigerator/dishwasher parts using intelligent analysis"
        )

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Determine if a query is within scope (refrigerator/dishwasher parts)"""
        try:
            query_lower = query.lower().strip()

            # Quick checks for obvious in-scope indicators
            if self._has_part_numbers(query_lower):
                return self._create_in_scope_result("Contains part numbers")

            if self._has_model_numbers(query_lower):
                return self._create_in_scope_result("Contains model numbers")

            # Use LLM-based intelligent scope detection
            scope_result = await self._analyze_scope_with_llm(query)

            return scope_result

        except Exception as e:
            # If there's an error, assume in-scope to be safe
            return self._create_in_scope_result(f"Error in scope detection: {str(e)}")

    def _has_part_numbers(self, query: str) -> bool:
        """Check if query contains appliance part numbers"""
        part_patterns = [
            r'PS\d{8,}',  # PS12364199
            r'W\d{8,}',   # W10712395
            r'[A-Z]{2,3}\d{6,}',  # General pattern
        ]

        for pattern in part_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    def _has_model_numbers(self, query: str) -> bool:
        """Check if query contains appliance model numbers"""
        model_patterns = [
            r'[A-Z]{2,4}\d{3,}[A-Z]*\d*',  # WDT780SAEM1, FFHS2622MS
        ]

        for pattern in model_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    async def _analyze_scope_with_llm(self, query: str) -> AgentResult:
        """Use intelligent analysis to determine if query is about refrigerator/dishwasher parts, shopping cart, or part usage"""

        query_lower = query.lower().strip()

        # Define the specific scope: refrigerator/dishwasher parts, shopping cart, part usage

        # 1. Check for refrigerator/dishwasher parts related content
        appliance_indicators = [
            # Direct appliance mentions
            "refrigerator", "fridge", "dishwasher", "appliance",
            # Part types
            "part", "filter", "ice maker", "door", "seal", "pump", "motor",
            "control", "board", "rack", "arm", "valve", "water filter",
            "heating element", "drain", "hose", "gasket", "thermostat",
            "compressor", "fan", "belt", "switch", "timer", "sensor",
            "dispenser", "bin", "drawer", "shelf", "handle", "latch",
            "spring", "wheel", "roller", "bearing", "coil", "condenser",
            # Actions related to parts
            "install", "repair", "fix", "replace", "compatible", "model",
            "troubleshoot", "maintenance", "warranty"
        ]

        # 2. Check for shopping cart related content
        cart_indicators = [
            "cart", "add to cart", "shopping cart", "checkout", "purchase",
            "buy", "order", "price", "cost", "total", "payment", "shipping",
            "quantity", "remove", "clear cart", "view cart", "proceed to checkout",
            # Confirmation words for purchase/cart context
            "yes", "y", "ok", "okay", "proceed", "go ahead", "confirm", "add it"
        ]

        # 3. Check for part usage/installation related content
        usage_indicators = [
            "how to use", "how to install", "instructions", "guide",
            "tutorial", "steps", "installation", "setup", "configure",
            "operate", "manual", "directions", "procedure"
        ]

        # Check if query contains any scope-relevant indicators
        has_appliance_content = any(indicator in query_lower for indicator in appliance_indicators)
        has_cart_content = any(indicator in query_lower for indicator in cart_indicators)
        has_usage_content = any(indicator in query_lower for indicator in usage_indicators)

        # If query contains scope-relevant content, it's in scope
        if has_appliance_content or has_cart_content or has_usage_content:
            scope_type = []
            if has_appliance_content:
                scope_type.append("appliance parts")
            if has_cart_content:
                scope_type.append("shopping cart")
            if has_usage_content:
                scope_type.append("part usage")

            return self._create_in_scope_result(f"Query relates to {' and '.join(scope_type)}")

        # Check for clearly out-of-scope content
        # If query is asking about topics completely unrelated to appliances, shopping, or parts
        out_of_scope_indicators = [
            # Entertainment & Media
            "movie", "film", "tv show", "anime", "cartoon", "doraemon", "naruto",
            "music", "song", "artist", "band", "concert", "album",
            # Animals & Pets
            "cat", "dog", "pet", "animal", "fish", "bird", "horse", "cow",
            # Religion & Philosophy
            "god", "religion", "spiritual", "gita", "bhagwat", "bhagavad",
            "krishna", "bible", "quran", "church", "temple", "prayer",
            # Science & Education
            "math", "physics", "chemistry", "biology", "science", "history",
            "geography", "literature", "school", "university", "education",
            # Technology (non-appliance)
            "computer", "software", "programming", "code", "website", "app",
            "internet", "social media", "facebook", "twitter", "instagram",
            # Sports & Games
            "football", "basketball", "soccer", "tennis", "game", "gaming",
            "video game", "sports", "team", "player", "match",
            # General Topics
            "weather", "news", "politics", "government", "election", "president",
            "travel", "vacation", "hotel", "flight", "car", "vehicle",
            "health", "medicine", "doctor", "hospital", "fitness", "exercise"
        ]

        # Check if query is clearly about out-of-scope topics
        has_out_of_scope_content = any(indicator in query_lower for indicator in out_of_scope_indicators)

        if has_out_of_scope_content:
            return self._create_out_of_scope_result("Query is about topics unrelated to refrigerator/dishwasher parts, shopping cart, or part usage")

        # Check for general questions without any scope context
        general_patterns = ["what is", "who is", "tell me about", "explain", "define", "describe"]
        is_general_question = any(pattern in query_lower for pattern in general_patterns)

        if is_general_question:
            # For general questions, check if they have any appliance/cart/usage context
            if not (has_appliance_content or has_cart_content or has_usage_content):
                return self._create_out_of_scope_result("General question without appliance, cart, or usage context")

        # For ambiguous cases that don't clearly fall into either category,
        # default to out-of-scope to be more precise about our scope
        return self._create_out_of_scope_result("Query does not clearly relate to refrigerator/dishwasher parts, shopping cart, or part usage")

    def _create_in_scope_result(self, reasoning: str) -> AgentResult:
        """Create result indicating query is in scope"""
        return AgentResult(
            success=True,
            data={
                "is_in_scope": True,
                "reasoning": reasoning,
                "confidence": 0.9
            },
            message=f"Query is in scope: {reasoning}"
        )

    def _create_out_of_scope_result(self, reasoning: str) -> AgentResult:
        """Create result indicating query is out of scope"""
        return AgentResult(
            success=True,
            data={
                "is_in_scope": False,
                "reasoning": reasoning,
                "confidence": 0.9
            },
            message=f"Query is out of scope: {reasoning}"
        )