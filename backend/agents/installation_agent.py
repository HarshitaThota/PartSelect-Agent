"""
Installation Agent
Handles installation guidance and repair instructions
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class InstallationAgent(BaseAgent):
    """Agent specialized in providing installation guidance"""

    def __init__(self):
        super().__init__(
            name="installation_agent",
            description="Provides installation guides and repair instructions"
        )

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Process installation help queries"""
        try:
            intent_data = context or {}
            entities = intent_data.get("extracted_entities", {})

            part_numbers = entities.get("part_numbers", [])
            tools_used = []

            if part_numbers:
                installation_guides = []
                parts_info = []

                for part_number in part_numbers:
                    # Get installation guide
                    guide = await self.call_tool("get_installation_guide", part_number=part_number)
                    tools_used.append("get_installation_guide")

                    if guide and "error" not in guide:
                        installation_guides.append(guide)

                    # Get part details for context
                    part_details = await self.call_tool("get_part_details", part_number=part_number)
                    tools_used.append("get_part_details")

                    if part_details and "error" not in part_details:
                        parts_info.append(part_details)

                return AgentResult(
                    success=True,
                    data={
                        "installation_guides": installation_guides,
                        "parts": parts_info,
                        "guide_type": "specific_part"
                    },
                    tools_used=tools_used,
                    message=f"Found installation guides for {len(installation_guides)} part(s)"
                )

            else:
                # General installation question without specific part
                return AgentResult(
                    success=True,
                    data={
                        "guide_type": "general",
                        "message": "To provide specific installation instructions, please provide the part number (like PS12364199) you need help installing."
                    },
                    tools_used=tools_used,
                    message="Need specific part number for installation guide"
                )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Installation guidance failed: {str(e)}"
            )