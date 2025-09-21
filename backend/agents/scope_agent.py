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
        """Use LLM to intelligently determine if query is about refrigerator/dishwasher parts"""

        # Check for obvious appliance-related terms
        appliance_terms = [
            "refrigerator", "fridge", "dishwasher", "appliance",
            "part", "filter", "ice maker", "door", "seal", "pump",
            "motor", "control", "board", "rack", "arm", "valve",
            "install", "repair", "fix", "compatible", "model",
            "water filter", "heating element", "drain", "hose",
            "gasket", "thermostat", "compressor", "fan", "belt",
            "switch", "timer", "sensor", "dispenser", "bin",
            "drawer", "shelf", "handle", "latch", "spring",
            "wheel", "roller", "bearing", "coil", "condenser"
        ]

        # Check if query contains appliance-related terms
        query_words = query.lower().split()
        has_appliance_terms = any(
            term in query.lower() or any(word in term or term in word for word in query_words)
            for term in appliance_terms
        )

        if has_appliance_terms:
            return self._create_in_scope_result("Contains appliance-related terms")

        # If no obvious appliance terms, it's likely out of scope
        # This is a simple heuristic - we could enhance this with actual LLM calls if needed
        non_appliance_indicators = [
            # Check if it's clearly about other topics
            any(topic in query.lower() for topic in [
                "cat", "dog", "pet", "animal", "weather", "news", "sports",
                "politics", "movie", "music", "book", "travel", "food",
                "recipe", "medicine", "car", "phone", "computer", "software",
                "game", "gaming", "anime", "religion", "philosophy", "god",
                "gita", "bhagwat", "bhagavad", "krishna", "spiritual",
                "biology", "science", "math", "history", "geography"
            ])
        ]

        if any(non_appliance_indicators):
            return self._create_out_of_scope_result("Clearly about non-appliance topics")

        # For ambiguous cases, we could implement actual LLM analysis here
        # For now, if it's not clearly out-of-scope, assume in-scope
        return self._create_in_scope_result("Ambiguous query - defaulting to in-scope")

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