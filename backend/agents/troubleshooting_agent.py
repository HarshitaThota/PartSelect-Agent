"""
Troubleshooting Agent
Handles problem diagnosis and repair recommendations
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class TroubleshootingAgent(BaseAgent):
    """Agent specialized in troubleshooting appliance issues"""

    def __init__(self, tools=None):
        super().__init__(
            name="troubleshooting_agent",
            description="Diagnoses problems and recommends repair solutions"
        )
        self.tools = tools  # Direct tool access

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Process troubleshooting queries"""
        try:
            intent_data = context or {}
            entities = intent_data.get("extracted_entities", {})

            appliance_types = entities.get("appliance_types", [])
            tools_used = []

            # Check if this is a general problems inquiry
            if self._is_general_problems_query(query):
                appliance_type = appliance_types[0] if appliance_types else "general"
                common_problems = self._get_common_problems(appliance_type)

                return AgentResult(
                    success=True,
                    data={
                        "troubleshooting_type": "common_problems",
                        "appliance_type": appliance_type,
                        "common_problems": common_problems,
                        "parts": []  # No parts needed for general info
                    },
                    tools_used=tools_used,
                    message=f"Common {appliance_type} problems and solutions provided"
                )

            # Extract symptoms from the query
            symptoms = self._extract_symptoms(query)

            if symptoms:
                appliance_type = appliance_types[0] if appliance_types else None

                # Find parts that might fix these symptoms
                potential_solutions = await self.tools.troubleshoot_issue(
                    symptoms=symptoms,
                    appliance_type=appliance_type
                ) if self.tools else []
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

    def _is_general_problems_query(self, query: str) -> bool:
        """Check if the query is asking for general problems/issues"""
        query_lower = query.lower()
        general_patterns = [
            "common problems", "common issues", "what problems", "what issues",
            "typical problems", "frequent problems", "usual problems",
            "what can go wrong", "what goes wrong", "problems with",
            "issues with", "what are the problems"
        ]

        return any(pattern in query_lower for pattern in general_patterns)

    def _get_common_problems(self, appliance_type: str) -> List[Dict[str, str]]:
        """Get common problems for the specified appliance type"""

        dishwasher_problems = [
            {
                "problem": "Dishes not getting clean",
                "causes": "Clogged spray arms, worn wash arms, dirty filters, incorrect loading",
                "solutions": "Clean spray arms and filters, check water temperature (120°F), ensure proper loading, use rinse aid"
            },
            {
                "problem": "Dishwasher not draining",
                "causes": "Clogged drain hose, faulty drain pump, blocked garbage disposal",
                "solutions": "Check and clear drain hose, inspect drain pump, run garbage disposal if connected"
            },
            {
                "problem": "Water not filling",
                "causes": "Faulty water inlet valve, clogged water supply line, door not properly closed",
                "solutions": "Check water supply, ensure door is fully closed and latched, inspect inlet valve"
            },
            {
                "problem": "Dishwasher leaking",
                "causes": "Worn door seals, loose connections, cracked tub, overloading",
                "solutions": "Inspect and replace door seals, check all connections, avoid overloading"
            },
            {
                "problem": "Dishwasher won't start",
                "causes": "Door not latched, no power, faulty control panel, child lock enabled",
                "solutions": "Ensure door is properly closed, check power supply, inspect control panel, disable child lock"
            },
            {
                "problem": "Unusual noises",
                "causes": "Loose wash arms, worn pump motor, dishes hitting each other, foreign objects",
                "solutions": "Secure wash arms, check for loose items, ensure proper loading, inspect for foreign objects"
            }
        ]

        refrigerator_problems = [
            {
                "problem": "Not cooling properly",
                "causes": "Dirty condenser coils, faulty compressor, blocked air vents, door seal issues",
                "solutions": "Clean condenser coils, check door seals, ensure proper air circulation, inspect compressor"
            },
            {
                "problem": "Ice maker not working",
                "causes": "Water supply issues, faulty ice maker assembly, clogged water filter, frozen water line",
                "solutions": "Check water supply, replace water filter, inspect ice maker assembly, thaw frozen lines"
            },
            {
                "problem": "Water dispenser not working",
                "causes": "Clogged water filter, faulty water inlet valve, frozen water lines, air in lines",
                "solutions": "Replace water filter, check water inlet valve, thaw frozen lines, purge air from system"
            },
            {
                "problem": "Strange noises",
                "causes": "Faulty compressor, worn evaporator fan motor, loose components, ice buildup",
                "solutions": "Inspect compressor, check fan motors, secure loose parts, defrost if needed"
            },
            {
                "problem": "Freezer too warm",
                "causes": "Faulty defrost system, blocked air vents, door seal problems, overloading",
                "solutions": "Check defrost components, ensure proper air flow, inspect door seals, reduce load"
            },
            {
                "problem": "Water leaking",
                "causes": "Clogged drain tube, faulty water inlet valve, damaged water lines, ice buildup",
                "solutions": "Clear drain tube, inspect water connections, check for ice blockages, replace damaged lines"
            }
        ]

        if appliance_type == "dishwasher":
            return dishwasher_problems
        elif appliance_type in ["refrigerator", "fridge"]:
            return refrigerator_problems
        else:
            # Return combined list for general queries
            return dishwasher_problems + refrigerator_problems