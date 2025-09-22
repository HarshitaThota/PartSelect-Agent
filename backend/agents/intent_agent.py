"""
Intent Classification Agent
Pretty much determines what the user wants to do based on their query 
"""

import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult
from .scope_agent import ScopeAgent

class IntentAgent(BaseAgent):
    """Agent that classifies user intent from natural language queries"""

    def __init__(self):
        super().__init__(
            name="intent_classifier",
            description="Classifies user intent from natural language queries"
        )
        self.intent_patterns = self._load_intent_patterns()
        self.scope_agent = ScopeAgent()

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Define patterns for each intent type"""
        return {
            "part_lookup": [
                r"part\s+number\s+([A-Z]{2}\s?\d+)",
                r"([A-Z]{2}\s?\d+)",
                r"what\s+is\s+([A-Z]{2}\s?\d+)",
                r"tell\s+me\s+about\s+([A-Z]{2}\s?\d+)",
                r"details\s+for\s+([A-Z]{2}\s?\d+)"
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
                r"leaking",
                r"common.*problems?",
                r"what.*problems?",
                r"what.*issues?",
                r"problems?\s+with",
                r"issues?\s+with",
                r"what.*wrong",
                r"what.*can.*go.*wrong",
                r"typical.*problems?",
                r"frequent.*problems?",
                r"usual.*problems?"
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
                r"parts\s+for",
                r"add.*ice.*part",
                r"add.*icemaker"
            ],
            "purchase_intent": [
                r"buy",
                r"order",
                r"purchase",
                r"add\s+to\s+cart",
                r"want\s+to\s+buy",
                r"want\s+to\s+order",
                r"want\s+to\s+purchase"
            ],
            "purchase_confirmation": [
                r"^yes$",
                r"^y$",
                r"^ok$",
                r"^okay$",
                r"proceed",
                r"go\s+ahead",
                r"confirm",
                r"add\s+it",
                r"add\s+to\s+cart"
            ],
            "pricing_inquiry": [
                r"price",
                r"cost",
                r"how\s+much",
                r"pricing",
                r"total"
            ],
            "cart_operations": [
                r"cart",
                r"checkout",
                r"view\s+cart",
                r"shopping\s+cart",
                r"add.*cart",
                r"add\s+it",
                r"yes.*add",
                r"proceed.*add"
            ],
            "ordering_info": [
                r"in\s+stock",
                r"availability",
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

            # Check for out-of-scope queries first using intelligent scope detection
            scope_result = await self.scope_agent.process(query)
            if scope_result.success and not scope_result.data.get("is_in_scope", True):
                return AgentResult(
                    success=True,
                    data={
                        "intent": "out_of_scope",
                        "confidence": scope_result.data.get("confidence", 0.9),
                        "extracted_entities": {},
                        "reasoning": scope_result.data.get("reasoning", "Query is outside refrigerator/dishwasher parts scope")
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
            # BUT respect purchase/transaction intent if those keywords are present
            if entities.get("part_numbers"):
                if "install" in query_lower or "how to" in query_lower:
                    primary_intent = "installation_help"
                elif "compatible" in query_lower or "fit" in query_lower:
                    primary_intent = "compatibility_check"
                elif any(keyword in query_lower for keyword in ["buy", "purchase", "order", "want to buy", "want to purchase", "want to order", "add to cart"]):
                    # Keep purchase intent if purchase keywords are present
                    if primary_intent not in ["purchase_intent", "cart_operations"]:
                        primary_intent = "purchase_intent"
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
            r'PS\s?\d{8,}',  # PS12364199 or PS 12364199
            r'W\s?\d{8,}',   # W10712395 or W 10712395
            r'[A-Z]{2,3}\s?\d{6,}',  # General pattern with optional space
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

        # Extract brands (use word boundaries to avoid false matches)
        brands = ["whirlpool", "kenmore", "ge", "frigidaire", "lg", "samsung", "kitchenaid", "bosch"]
        for brand in brands:
            # Use word boundaries to avoid "ge" matching inside "fridge"
            if re.search(r'\b' + brand + r'\b', query.lower()):
                entities["brands"].append(brand.title())

        # Extract appliance types (normalize fridge -> refrigerator)
        query_lower = query.lower()
        if "refrigerator" in query_lower or "fridge" in query_lower:
            entities["appliance_types"].append("refrigerator")
        if "dishwasher" in query_lower:
            entities["appliance_types"].append("dishwasher")

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