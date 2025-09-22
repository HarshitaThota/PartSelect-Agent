# Product Agent
# for the product queries like search, installation, and compatibility 


from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class ProductAgent(BaseAgent):

    def __init__(self, tools=None):
        super().__init__(
            name="product_agent",
            description="Handles product search, installation guidance, and compatibility checking"
        )
        self.tools = tools  # Direct tool access instead of registration

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        try:
            intent_data = context or {}
            intent = intent_data.get("intent", "part_lookup")

            # Route to appropriate handler based on intent
            if intent == "part_lookup":
                return await self._handle_part_search(query, intent_data)
            elif intent == "installation_help":
                return await self._handle_installation(query, intent_data)
            elif intent == "compatibility_check":
                return await self._handle_compatibility(query, intent_data)
            else:
                # Default to part search for unknown intents
                return await self._handle_part_search(query, intent_data)

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Product processing failed: {str(e)}"
            )

    async def _handle_part_search(self, query: str, intent_data: Dict[str, Any]) -> AgentResult:
        entities = intent_data.get("extracted_entities", {})
        search_params = self._build_search_params(query, entities)
        tools_used = []

        # if there's have specific part numbers, get those directly
        part_numbers = entities.get("part_numbers", [])
        if part_numbers:
            parts = []
            for part_number in part_numbers:
                part_details = await self.tools.get_part_details(part_number) if self.tools else None
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

        # search by category if specified
        categories = entities.get("categories", [])
        appliance_types = entities.get("appliance_types", [])

        if categories:
            parts = []
            for category in categories:
                appliance_type = appliance_types[0] if appliance_types else None
                category_parts = await self.tools.get_parts_by_category(
                    category=category,
                    appliance_type=appliance_type,
                    limit=10
                ) if self.tools else []
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

        search_results = await self.tools.search_parts(
            query=search_params["query"],
            category=search_params.get("category"),
            appliance_type=search_params.get("appliance_type"),
            brand=search_params.get("brand"),
            limit=10
        ) if self.tools else []
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

    async def _handle_installation(self, query: str, intent_data: Dict[str, Any]) -> AgentResult:
        """Handle installation guidance queries"""
        entities = intent_data.get("extracted_entities", {})
        part_numbers = entities.get("part_numbers", [])
        tools_used = []

        if part_numbers:
            installation_guides = []
            parts_info = []

            for part_number in part_numbers:
                # gett installation guide
                guide = await self.tools.get_installation_guide(part_number) if self.tools else {}
                tools_used.append("get_installation_guide")

                if guide and "error" not in guide:
                    installation_guides.append(guide)

                # get part details for context
                part_details = await self.tools.get_part_details(part_number) if self.tools else None
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
            return AgentResult(
                success=True,
                data={
                    "guide_type": "general",
                    "message": "To provide specific installation instructions, please provide the part number (like PS12364199) you need help installing."
                },
                tools_used=tools_used,
                message="Need specific part number for installation guide"
            )

    async def _handle_compatibility(self, query: str, intent_data: Dict[str, Any]) -> AgentResult:
        entities = intent_data.get("extracted_entities", {})
        part_numbers = entities.get("part_numbers", [])
        model_numbers = entities.get("model_numbers", [])
        tools_used = []
        results = []

        # Case 1: Direct compatibility check (part + model provided)
        if part_numbers and model_numbers:
            for part_number in part_numbers:
                for model_number in model_numbers:
                    compatibility_result = await self.tools.check_compatibility(
                        part_number=part_number,
                        model_number=model_number
                    ) if self.tools else {}
                    tools_used.append("check_compatibility")

                    if "error" not in compatibility_result:
                        results.append(compatibility_result)
                    part_details = await self.tools.get_part_details(part_number) if self.tools else None
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
                part_details = await self.tools.get_part_details(part_number) if self.tools else None
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

    def _build_search_params(self, query: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        params = {
            "query": query
        }

        # appliance type if specified
        appliance_types = entities.get("appliance_types", [])
        if appliance_types:
            params["appliance_type"] = appliance_types[0]

        # category if specified
        categories = entities.get("categories", [])
        if categories:
            params["category"] = categories[0]

        # brand filter if specified
        brands = entities.get("brands", [])
        if brands:
            params["brand"] = brands[0]

        return params