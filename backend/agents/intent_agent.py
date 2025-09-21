"""
Intent Classification Agent
Determines what the user wants to do based on their query
"""

import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class IntentAgent(BaseAgent):
    """Agent that classifies user intent from natural language queries"""

    def __init__(self):
        super().__init__(
            name="intent_classifier",
            description="Classifies user intent from natural language queries"
        )
        self.intent_patterns = self._load_intent_patterns()

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Define patterns for each intent type"""
        return {
            "part_lookup": [
                r"part\s+number\s+([A-Z]{2}\d+)",
                r"([A-Z]{2}\d+)",
                r"what\s+is\s+([A-Z]{2}\d+)",
                r"tell\s+me\s+about\s+([A-Z]{2}\d+)",
                r"details\s+for\s+([A-Z]{2}\d+)"
            ],
            "compatibility_check": [
                r"compatible\s+with",
                r"fit\s+my\s+(\w+)",
                r"work\s+with\s+model",
                r"model\s+([A-Z0-9]+)",
                r"will.*work.*(\w+)",
                r"does.*fit"
            ],
            "installation_help": [
                r"how\s+to\s+install",
                r"install.*part",
                r"installation\s+guide",
                r"how\s+do\s+i\s+install",
                r"replace.*part",
                r"repair.*guide",
                r"fix.*install"
            ],
            "troubleshooting": [
                r"not\s+working",
                r"broken",
                r"fix.*problem",
                r"repair",
                r"troubleshoot",
                r"issue\s+with",
                r"problem\s+with",
                r"won't\s+work",
                r"not\s+functioning",
                r"making\s+noise",
                r"leaking"
            ],
            "product_search": [
                r"need.*filter",
                r"looking\s+for",
                r"find.*part",
                r"search\s+for",
                r"show\s+me",
                r"water\s+filter",
                r"ice\s+maker",
                r"door\s+seal",
                r"parts\s+for"
            ],
            "ordering_info": [
                r"price",
                r"cost",
                r"buy",
                r"order",
                r"purchase",
                r"in\s+stock",
                r"shipping",
                r"delivery"
            ],
            "general_info": [
                r"what\s+is",
                r"tell\s+me\s+about",
                r"information\s+about",
                r"details\s+about"
            ]
        }

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Classify the intent of a user query"""
        try:
            query_lower = query.lower().strip()

            # Check for out-of-scope queries first
            if self._is_out_of_scope(query_lower):
                return AgentResult(
                    success=True,
                    data={
                        "intent": "out_of_scope",
                        "confidence": 0.9,
                        "extracted_entities": {},
                        "reasoning": "Query is outside refrigerator/dishwasher parts scope"
                    },
                    message="Query identified as out of scope"
                )

            # Extract entities (part numbers, model numbers, etc.)
            entities = self._extract_entities(query_lower)

            # Classify intent based on patterns
            intent_scores = {}

            for intent, patterns in self.intent_patterns.items():
                score = 0.0
                matched_patterns = []

                for pattern in patterns:
                    if re.search(pattern, query_lower, re.IGNORECASE):
                        score += 1.0
                        matched_patterns.append(pattern)

                if score > 0:
                    # Normalize score by number of patterns
                    intent_scores[intent] = score / len(patterns)

            # Determine primary intent
            if not intent_scores:
                primary_intent = "general_info"
                confidence = 0.5
            else:
                primary_intent = max(intent_scores, key=intent_scores.get)
                confidence = intent_scores[primary_intent]

            # Special case: if we found a part number, it's likely a part lookup
            if entities.get("part_numbers"):
                if "install" in query_lower or "how to" in query_lower:
                    primary_intent = "installation_help"
                elif "compatible" in query_lower or "fit" in query_lower:
                    primary_intent = "compatibility_check"
                else:
                    primary_intent = "part_lookup"
                confidence = max(confidence, 0.8)

            return AgentResult(
                success=True,
                data={
                    "intent": primary_intent,
                    "confidence": confidence,
                    "extracted_entities": entities,
                    "intent_scores": intent_scores,
                    "reasoning": f"Classified as {primary_intent} based on patterns and entities"
                },
                message=f"Intent classified as {primary_intent} with {confidence:.1%} confidence",
                next_agent="orchestrator"
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Intent classification failed: {str(e)}"
            )

    def _is_out_of_scope(self, query: str) -> bool:
        """Check if query is outside our scope (refrigerator/dishwasher parts)"""
        # Scope indicators (in scope)
        in_scope_keywords = [
            "refrigerator", "fridge", "dishwasher", "appliance",
            "part", "filter", "ice maker", "door", "seal", "pump",
            "motor", "control", "board", "rack", "arm", "valve",
            "install", "repair", "fix", "compatible", "model"
        ]

        # Out of scope keywords
        out_of_scope_keywords = [
            "weather", "news", "sports", "politics", "car", "phone",
            "computer", "software", "medicine", "food", "recipe",
            "movie", "music", "book", "travel"
        ]

        # Check for part numbers (always in scope)
        if re.search(r'[A-Z]{2}\d+', query):
            return False

        # Check for model numbers (always in scope)
        if re.search(r'[A-Z]{2,4}\d{3,}', query):
            return False

        # If query contains out-of-scope keywords and no in-scope keywords
        has_out_of_scope = any(keyword in query for keyword in out_of_scope_keywords)
        has_in_scope = any(keyword in query for keyword in in_scope_keywords)

        return has_out_of_scope and not has_in_scope

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities like part numbers, model numbers, etc."""
        entities = {
            "part_numbers": [],
            "model_numbers": [],
            "brands": [],
            "appliance_types": [],
            "categories": []
        }

        # Extract part numbers (PS + digits, W + digits, etc.)
        part_patterns = [
            r'PS\d{8,}',  # PS12364199
            r'W\d{8,}',   # W10712395
            r'[A-Z]{2,3}\d{6,}',  # General pattern
        ]

        for pattern in part_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities["part_numbers"].extend(matches)

        # Extract model numbers
        model_patterns = [
            r'[A-Z]{2,4}\d{3,}[A-Z]*\d*',  # WDT780SAEM1, FFHS2622MS
        ]

        for pattern in model_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities["model_numbers"].extend(matches)

        # Extract brands
        brands = ["whirlpool", "kenmore", "ge", "frigidaire", "lg", "samsung", "kitchenaid", "bosch"]
        for brand in brands:
            if brand in query.lower():
                entities["brands"].append(brand.title())

        # Extract appliance types
        appliances = ["refrigerator", "fridge", "dishwasher"]
        for appliance in appliances:
            if appliance in query.lower():
                entities["appliance_types"].append(appliance)

        # Extract categories
        categories = [
            "water filter", "ice maker", "door seal", "door shelf", "drawer",
            "wash arm", "pump", "rack", "control board", "motor", "valve"
        ]
        for category in categories:
            if category in query.lower():
                entities["categories"].append(category)

        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities