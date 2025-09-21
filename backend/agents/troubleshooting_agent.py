"""
Troubleshooting Agent
Handles problem diagnosis and repair recommendations
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class TroubleshootingAgent(BaseAgent):
    """Agent specialized in troubleshooting appliance issues"""

    def __init__(self):
        super().__init__(
            name="troubleshooting_agent",
            description="Diagnoses problems and recommends repair solutions"
        )

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Process troubleshooting queries"""
        try:
            intent_data = context or {}
            entities = intent_data.get("extracted_entities", {})

            appliance_types = entities.get("appliance_types", [])
            tools_used = []

            # Extract symptoms from the query
            symptoms = self._extract_symptoms(query)

            if symptoms:
                appliance_type = appliance_types[0] if appliance_types else None

                # Find parts that might fix these symptoms
                potential_solutions = await self.call_tool(
                    "troubleshoot_issue",
                    symptoms=symptoms,
                    appliance_type=appliance_type
                )
                tools_used.append("troubleshoot_issue")

                if potential_solutions and "error" not in potential_solutions:
                    # Extract parts from solutions
                    parts = [solution.get("part") for solution in potential_solutions if solution.get("part")]

                    return AgentResult(
                        success=True,
                        data={
                            "troubleshooting_results": potential_solutions,
                            "parts": parts,
                            "symptoms_analyzed": symptoms,
                            "appliance_type": appliance_type
                        },
                        tools_used=tools_used,
                        message=f"Found {len(potential_solutions)} potential solutions for the reported symptoms"
                    )

            # If no specific symptoms identified, provide general guidance
            return AgentResult(
                success=True,
                data={
                    "troubleshooting_type": "general_guidance",
                    "message": "Please describe the specific problem you're experiencing (e.g., 'not working', 'making noise', 'leaking', 'not cooling') for better troubleshooting assistance."
                },
                tools_used=tools_used,
                message="Need more specific symptoms for troubleshooting"
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Troubleshooting failed: {str(e)}"
            )

    def _extract_symptoms(self, query: str) -> str:
        """Extract symptoms from the query text"""
        query_lower = query.lower()

        # Common symptom keywords
        symptom_patterns = [
            "not working", "broken", "not cooling", "not heating",
            "making noise", "leaking", "not draining", "won't start",
            "not cleaning", "door won't close", "ice not dispensing",
            "water not flowing", "temperature issues", "vibrating",
            "overheating", "freezing up", "not defrosting"
        ]

        found_symptoms = []
        for symptom in symptom_patterns:
            if symptom in query_lower:
                found_symptoms.append(symptom)

        return " ".join(found_symptoms) if found_symptoms else query_lower