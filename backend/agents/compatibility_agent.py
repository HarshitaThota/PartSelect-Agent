"""
Compatibility Agent
Handles part compatibility checking with appliance models
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class CompatibilityAgent(BaseAgent):
    """Agent specialized in checking part compatibility"""

    def __init__(self):
        super().__init__(
            name="compatibility_agent",
            description="Checks if parts are compatible with specific appliance models"
        )

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Process compatibility check queries"""
        try:
            intent_data = context or {}
            entities = intent_data.get("extracted_entities", {})

            part_numbers = entities.get("part_numbers", [])
            model_numbers = entities.get("model_numbers", [])

            tools_used = []
            results = []

            # Case 1: Direct compatibility check (part + model provided)
            if part_numbers and model_numbers:
                for part_number in part_numbers:
                    for model_number in model_numbers:
                        compatibility_result = await self.call_tool(
                            "check_compatibility",
                            part_number=part_number,
                            model_number=model_number
                        )
                        tools_used.append("check_compatibility")

                        if "error" not in compatibility_result:
                            results.append(compatibility_result)

                        # Also get part details for context
                        part_details = await self.call_tool("get_part_details", part_number=part_number)
                        tools_used.append("get_part_details")

                return AgentResult(
                    success=True,
                    data={
                        "compatibility_results": results,
                        "check_type": "direct_check",
                        "parts_checked": part_numbers,
                        "models_checked": model_numbers,
                        "parts": [part_details] if part_details and "error" not in part_details else []
                    },
                    tools_used=tools_used,
                    message=f"Checked compatibility for {len(part_numbers)} part(s) with {len(model_numbers)} model(s)"
                )

            # Case 2: Part number provided, looking for compatible models
            elif part_numbers:
                parts_info = []
                for part_number in part_numbers:
                    part_details = await self.call_tool("get_part_details", part_number=part_number)
                    tools_used.append("get_part_details")

                    if part_details and "error" not in part_details:
                        parts_info.append(part_details)

                return AgentResult(
                    success=True,
                    data={
                        "parts": parts_info,
                        "check_type": "part_lookup_with_models",
                        "message": "Part details with compatible models provided"
                    },
                    tools_used=tools_used,
                    message=f"Found details and compatible models for {len(parts_info)} part(s)"
                )

            # Case 3: Model number provided, need to find compatible parts
            elif model_numbers:
                # This would require searching for parts that work with this model
                # For now, we'll return a helpful message
                return AgentResult(
                    success=True,
                    data={
                        "check_type": "model_lookup",
                        "models": model_numbers,
                        "message": "To find compatible parts, please specify what type of part you need (e.g., water filter, ice maker, door seal)"
                    },
                    tools_used=tools_used,
                    message="Model number identified, but need part type to search for compatible parts"
                )

            # Case 4: General compatibility question without specific numbers
            else:
                return AgentResult(
                    success=True,
                    data={
                        "check_type": "general_compatibility",
                        "message": "To check compatibility, please provide both a part number (like PS12364199) and your appliance model number (like WDT780SAEM1)"
                    },
                    tools_used=tools_used,
                    message="Need both part number and model number for compatibility check"
                )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Compatibility check failed: {str(e)}"
            )