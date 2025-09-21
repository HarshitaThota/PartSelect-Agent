"""
Search Agent
Handles product search and discovery queries
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class SearchAgent(BaseAgent):
    """Agent specialized in searching for parts and products"""

    def __init__(self):
        super().__init__(
            name="search_agent",
            description="Searches for parts based on user queries and filters"
        )

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Process search queries and return relevant parts"""
        try:
            # Extract search parameters from context
            intent_data = context or {}
            entities = intent_data.get("extracted_entities", {})

            search_params = self._build_search_params(query, entities)
            tools_used = []

            # If we have specific part numbers, get those directly
            part_numbers = entities.get("part_numbers", [])
            if part_numbers:
                parts = []
                for part_number in part_numbers:
                    part_details = await self.call_tool("get_part_details", part_number=part_number)
                    if part_details and "error" not in part_details:
                        parts.append(part_details)
                tools_used.append("get_part_details")

                if parts:
                    return AgentResult(
                        success=True,
                        data={
                            "parts": parts,
                            "search_type": "direct_lookup",
                            "query_processed": query
                        },
                        tools_used=tools_used,
                        message=f"Found {len(parts)} parts by direct lookup"
                    )

            # Search by category if specified
            categories = entities.get("categories", [])
            appliance_types = entities.get("appliance_types", [])

            if categories:
                parts = []
                for category in categories:
                    appliance_type = appliance_types[0] if appliance_types else None
                    category_parts = await self.call_tool(
                        "get_parts_by_category",
                        category=category,
                        appliance_type=appliance_type,
                        limit=10
                    )
                    if category_parts and "error" not in category_parts:
                        parts.extend(category_parts)
                tools_used.append("get_parts_by_category")

                if parts:
                    return AgentResult(
                        success=True,
                        data={
                            "parts": parts[:10],  # Limit results
                            "search_type": "category_search",
                            "query_processed": query
                        },
                        tools_used=tools_used,
                        message=f"Found {len(parts)} parts by category search"
                    )

            # General text search
            search_results = await self.call_tool(
                "search_parts",
                query=search_params["query"],
                category=search_params.get("category"),
                appliance_type=search_params.get("appliance_type"),
                limit=10
            )
            tools_used.append("search_parts")

            if "error" in search_results:
                return AgentResult(
                    success=False,
                    message=f"Search failed: {search_results['error']}"
                )

            return AgentResult(
                success=True,
                data={
                    "parts": search_results,
                    "search_type": "text_search",
                    "search_params": search_params,
                    "query_processed": query
                },
                tools_used=tools_used,
                message=f"Found {len(search_results)} parts matching your search"
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Search processing failed: {str(e)}"
            )

    def _build_search_params(self, query: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Build search parameters from query and entities"""
        params = {
            "query": query
        }

        # Add appliance type if specified
        appliance_types = entities.get("appliance_types", [])
        if appliance_types:
            params["appliance_type"] = appliance_types[0]

        # Add category if specified
        categories = entities.get("categories", [])
        if categories:
            params["category"] = categories[0]

        # Add brand filter if specified
        brands = entities.get("brands", [])
        if brands:
            params["brand"] = brands[0]

        return params