import json
import re
from typing import List, Dict, Any, Optional
from .vector_search_tool import VectorSearchTool

class PartSelectTools:

    def __init__(self, parts_data: List[Dict]):
        self.parts_data = parts_data
        self.vector_search = VectorSearchTool(parts_data)

    async def search_parts(self, query: str, category: str = None,
                          appliance_type: str = None, brand: str = None, limit: int = 10) -> List[Dict]:
        try:
            # first we traditional keyword searching
            traditional_results = await self._traditional_search(query, category, appliance_type, brand, limit)

            # if vector search is available enhance with semantic search
            if self.vector_search.is_available():
                filters = {}
                if appliance_type:
                    filters["appliance_type"] = appliance_type
                if category:
                    filters["category"] = category
                if brand:
                    filters["brand"] = brand

                hybrid_results = await self.vector_search.hybrid_search(
                    query, traditional_results, limit, filters
                )
                return hybrid_results
            else:
                return traditional_results

        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    async def _traditional_search(self, query: str, category: str = None,
                                 appliance_type: str = None, brand: str = None, limit: int = 10) -> List[Dict]:
        results = []
        query_lower = query.lower()

        for part in self.parts_data:
            # mandatory check appliance type filter
            if appliance_type and part["appliance_type"].lower() != appliance_type.lower():
                continue  # skip parts that don't match the appliance type

            # when category is specified filter by it
            if category and part["category"].lower() != category.lower():
                continue  # skippy skip again

            # when brand is specified yktv
            if brand and part["brand"].lower() != brand.lower():
                continue  

            score = 0.0

            # part number match (highest priority)
            if (part["partselect_number"].lower() in query_lower or
                part["manufacturer_part_number"].lower() in query_lower):
                score = 1.0

            elif category and part["category"].lower() == category.lower():
                score = 0.9

            elif appliance_type and part["appliance_type"].lower() == appliance_type.lower():
                score = 0.8

            elif any(word in part["name"].lower() for word in query_lower.split()):
                score = 0.7

            elif any(word in part["brand"].lower() for word in query_lower.split()):
                score = 0.6

            symptoms = part.get("troubleshooting", {}).get("symptoms_fixed", [])
            if any(symptom.lower() in query_lower for symptom in symptoms):
                score = 0.8

            if score > 0:
                part_copy = part.copy()
                part_copy["relevance_score"] = score
                results.append(part_copy)

        # sortibg by relevance and return top results
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]

    async def get_part_details(self, part_number: str) -> Optional[Dict]:
        try:
            search_term = part_number.lower().strip()

            for i, part in enumerate(self.parts_data):
                searchable_numbers = part.get("searchable_numbers", [])
                if any(num.lower() == search_term for num in searchable_numbers):
                    return part

                if (part["partselect_number"].lower() == search_term or
                    part["manufacturer_part_number"].lower() == search_term):
                    return part
            return None
        except Exception as e:
            return {"error": f"Failed to get part details: {str(e)}"}

    async def check_compatibility(self, part_number: str, model_number: str) -> Dict[str, Any]:
        """Check if a part is compatible with a specific model"""
        try:
            part = await self.get_part_details(part_number)
            if not part or "error" in part:
                return {
                    "compatible": False,
                    "reason": "Part not found",
                    "part_number": part_number,
                    "model_number": model_number
                }

            compatible_models = part.get("compatibility", {}).get("compatible_models", [])
            model_lower = model_number.lower()

            is_compatible = any(
                model_lower in compatible_model.lower() or
                compatible_model.lower() in model_lower
                for compatible_model in compatible_models
            )

            return {
                "compatible": is_compatible,
                "part_number": part_number,
                "model_number": model_number,
                "part_name": part.get("name", ""),
                "compatible_models": compatible_models[:5],  
                "reason": "Model found in compatibility list" if is_compatible else "Model not in compatibility list"
            }

        except Exception as e:
            return {"error": f"Compatibility check failed: {str(e)}"}

    async def get_installation_guide(self, part_number: str) -> Dict[str, Any]:
        try:
            part = await self.get_part_details(part_number)
            if not part or "error" in part:
                return {"error": "Part not found"}

            installation = part.get("installation", {})
            return {
                "part_number": part_number,
                "part_name": part.get("name", ""),
                "difficulty": installation.get("difficulty", "Unknown"),
                "time_required": installation.get("time", "Unknown"),
                "tools_required": installation.get("tools_required", False),
                "instructions": installation.get("instructions", "No instructions available"),
                "video_available": installation.get("video_available", False),
                "safety_notes": "Always disconnect power before beginning any repair"
            }

        except Exception as e:
            return {"error": f"Failed to get installation guide: {str(e)}"}

    async def troubleshoot_issue(self, symptoms: str, appliance_type: str = None) -> List[Dict]:
        try:
            symptoms_lower = symptoms.lower()
            potential_parts = []

            for part in self.parts_data:
   
                if appliance_type and part["appliance_type"].lower() != appliance_type.lower():
                    continue

                part_symptoms = part.get("troubleshooting", {}).get("symptoms_fixed", [])
                common_issues = part.get("troubleshooting", {}).get("common_issues", [])

                symptom_match = any(
                    symptom.lower() in symptoms_lower or symptoms_lower in symptom.lower()
                    for symptom in part_symptoms + common_issues
                )

                if symptom_match:
                    potential_parts.append({
                        "part": part,
                        "symptoms_addressed": [s for s in part_symptoms if s.lower() in symptoms_lower],
                        "confidence": 0.8 if len([s for s in part_symptoms if s.lower() in symptoms_lower]) > 1 else 0.6
                    })

            potential_parts.sort(key=lambda x: x["confidence"], reverse=True)
            return potential_parts[:5]  # Top 5 suggestions

        except Exception as e:
            return [{"error": f"Troubleshooting failed: {str(e)}"}]

    async def get_ordering_info(self, part_number: str) -> Dict[str, Any]:
        try:
            part = await self.get_part_details(part_number)
            if not part or "error" in part:
                return {"error": "Part not found"}

            ordering = part.get("ordering", {})
            return {
                "part_number": part_number,
                "part_name": part.get("name", ""),
                "price": part.get("price", 0),
                "in_stock": part.get("in_stock", False),
                "quantity_available": ordering.get("quantity_available", 0),
                "shipping_time": part.get("shipping_time", "Unknown"),
                "warranty": part.get("warranty", "Unknown"),
                "return_policy": ordering.get("return_policy", "Unknown")
            }

        except Exception as e:
            return {"error": f"Failed to get ordering info: {str(e)}"}

    async def find_alternative_parts(self, part_number: str) -> List[Dict]:
        try:
            original_part = await self.get_part_details(part_number)
            if not original_part or "error" in original_part:
                return []

            alternatives = []
            original_category = original_part.get("category", "")
            original_appliance = original_part.get("appliance_type", "")

            for part in self.parts_data:
                # skip the original part
                if part["partselect_number"] == part_number:
                    continue

                if (part["category"] == original_category and
                    part["appliance_type"] == original_appliance):

                    similarity_score = 0.7

                    # same brand gets higher score
                    if part["brand"] == original_part["brand"]:
                        similarity_score = 0.9

                    alternatives.append({
                        "part": part,
                        "similarity_score": similarity_score,
                        "replacement_type": "Direct alternative"
                    })

            alternatives.sort(key=lambda x: x["similarity_score"], reverse=True)
            return alternatives[:3]  

        except Exception as e:
            return [{"error": f"Failed to find alternatives: {str(e)}"}]

    async def get_parts_by_category(self, category: str, appliance_type: str = None, limit: int = 10) -> List[Dict]:
        try:
            results = []
            for part in self.parts_data:
                if part["category"].lower() == category.lower():
                    if not appliance_type or part["appliance_type"].lower() == appliance_type.lower():
                        results.append(part)

            return results[:limit]

        except Exception as e:
            return [{"error": f"Failed to get parts by category: {str(e)}"}]

    async def semantic_search(self, query: str, top_k: int = 5, appliance_type: str = None, brand: str = None, category: str = None) -> List[Dict]:
        if not self.vector_search.is_available():
            return await self._traditional_search(query, category, appliance_type, brand, top_k)

        filters = {}
        if appliance_type:
            filters["appliance_type"] = appliance_type
        if brand:
            filters["brand"] = brand
        if category:
            filters["category"] = category
        return await self.vector_search.semantic_search(query, top_k, filters)

    async def find_similar_parts(self, part_number: str, top_k: int = 3) -> List[Dict]:
        if not self.vector_search.is_available():
            # Fallback to category-based similarity
            part = await self.get_part_details(part_number)
            if part and "error" not in part:
                return await self.get_parts_by_category(
                    part.get("category", ""),
                    part.get("appliance_type", ""),
                    top_k
                )
            return []

        return await self.vector_search.find_similar_parts(part_number, top_k)

    async def initialize_vector_search(self) -> bool:
        if not self.vector_search.is_available():
            return False

        return await self.vector_search.initialize_index()