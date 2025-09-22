"""
Tool system for PartSelect agents
Tools are reusable functions that agents can call to perform specific tasks
"""

import json
import re
from typing import List, Dict, Any, Optional
from .vector_search_tool import VectorSearchTool

class PartSelectTools:
    """Collection of tools for PartSelect agents"""

    def __init__(self, parts_data: List[Dict]):
        self.parts_data = parts_data
        self.vector_search = VectorSearchTool(parts_data)

    async def search_parts(self, query: str, category: str = None,
                          appliance_type: str = None, brand: str = None, limit: int = 10) -> List[Dict]:
        """Search for parts using hybrid traditional + semantic search"""
        try:
            # First, do traditional keyword-based search
            traditional_results = await self._traditional_search(query, category, appliance_type, brand, limit)

            # If vector search is available, enhance with semantic search
            if self.vector_search.is_available():
                # Build filters for semantic search
                filters = {}
                if appliance_type:
                    filters["appliance_type"] = appliance_type
                if category:
                    filters["category"] = category
                if brand:
                    filters["brand"] = brand

                # Use hybrid search for better results
                print(f"🔍 Using hybrid search with filters: {filters}")
                print(f"🔍 Traditional search found {len(traditional_results)} results before hybrid")
                hybrid_results = await self.vector_search.hybrid_search(
                    query, traditional_results, limit, filters
                )
                print(f"🔍 Hybrid search returned {len(hybrid_results)} results")
                return hybrid_results
            else:
                print("🔍 Using traditional search (vector search not available)")
                return traditional_results

        except Exception as e:
            print(f"❌ Search error: {e}")
            return [{"error": f"Search failed: {str(e)}"}]

    async def _traditional_search(self, query: str, category: str = None,
                                 appliance_type: str = None, brand: str = None, limit: int = 10) -> List[Dict]:
        """Traditional keyword-based search"""
        results = []
        query_lower = query.lower()

        for part in self.parts_data:
            # First, check appliance type filter - this is mandatory
            if appliance_type and part["appliance_type"].lower() != appliance_type.lower():
                continue  # Skip parts that don't match the appliance type

            # If category is specified, filter by category too
            if category and part["category"].lower() != category.lower():
                continue  # Skip parts that don't match the category

            # If brand is specified, filter by brand too
            if brand and part["brand"].lower() != brand.lower():
                continue  # Skip parts that don't match the brand

            score = 0.0

            # Exact part number match (highest priority)
            if (part["partselect_number"].lower() in query_lower or
                part["manufacturer_part_number"].lower() in query_lower):
                score = 1.0

            # Category match
            elif category and part["category"].lower() == category.lower():
                score = 0.9

            # Appliance type match (already filtered above, but give score)
            elif appliance_type and part["appliance_type"].lower() == appliance_type.lower():
                score = 0.8

            # Name/description keyword match
            elif any(word in part["name"].lower() for word in query_lower.split()):
                score = 0.7

            # Brand match
            elif any(word in part["brand"].lower() for word in query_lower.split()):
                score = 0.6

            # Symptom match
            symptoms = part.get("troubleshooting", {}).get("symptoms_fixed", [])
            if any(symptom.lower() in query_lower for symptom in symptoms):
                score = 0.8

            if score > 0:
                part_copy = part.copy()
                part_copy["relevance_score"] = score
                results.append(part_copy)

        # Sort by relevance and return top results
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]

    async def get_part_details(self, part_number: str) -> Optional[Dict]:
        """Get detailed information about a specific part"""
        print(f"get_part_details called with: {part_number}")
        print(f"Searching through {len(self.parts_data)} parts")
        try:
            for i, part in enumerate(self.parts_data):
                if (part["partselect_number"].lower() == part_number.lower() or
                    part["manufacturer_part_number"].lower() == part_number.lower()):
                    print(f"Found match at index {i}: {part['partselect_number']}")
                    return part
            print(f"No match found for {part_number}")
            return None
        except Exception as e:
            print(f"Error in get_part_details: {e}")
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

            # Check for exact match or partial match
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
                "compatible_models": compatible_models[:5],  # Show first 5 for brevity
                "reason": "Model found in compatibility list" if is_compatible else "Model not in compatibility list"
            }

        except Exception as e:
            return {"error": f"Compatibility check failed: {str(e)}"}

    async def get_installation_guide(self, part_number: str) -> Dict[str, Any]:
        """Get installation instructions for a specific part"""
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
        """Find parts that might fix the described symptoms"""
        try:
            symptoms_lower = symptoms.lower()
            potential_parts = []

            for part in self.parts_data:
                # Filter by appliance type if specified
                if appliance_type and part["appliance_type"].lower() != appliance_type.lower():
                    continue

                part_symptoms = part.get("troubleshooting", {}).get("symptoms_fixed", [])
                common_issues = part.get("troubleshooting", {}).get("common_issues", [])

                # Check if any symptoms match
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

            # Sort by confidence
            potential_parts.sort(key=lambda x: x["confidence"], reverse=True)
            return potential_parts[:5]  # Top 5 suggestions

        except Exception as e:
            return [{"error": f"Troubleshooting failed: {str(e)}"}]

    async def get_ordering_info(self, part_number: str) -> Dict[str, Any]:
        """Get ordering information for a part"""
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
        """Find alternative parts that might work as replacements"""
        try:
            original_part = await self.get_part_details(part_number)
            if not original_part or "error" in original_part:
                return []

            alternatives = []
            original_category = original_part.get("category", "")
            original_appliance = original_part.get("appliance_type", "")

            for part in self.parts_data:
                # Skip the original part
                if part["partselect_number"] == part_number:
                    continue

                # Same category and appliance type
                if (part["category"] == original_category and
                    part["appliance_type"] == original_appliance):

                    similarity_score = 0.7

                    # Same brand gets higher score
                    if part["brand"] == original_part["brand"]:
                        similarity_score = 0.9

                    alternatives.append({
                        "part": part,
                        "similarity_score": similarity_score,
                        "replacement_type": "Direct alternative"
                    })

            # Sort by similarity
            alternatives.sort(key=lambda x: x["similarity_score"], reverse=True)
            return alternatives[:3]  # Top 3 alternatives

        except Exception as e:
            return [{"error": f"Failed to find alternatives: {str(e)}"}]

    async def get_parts_by_category(self, category: str, appliance_type: str = None, limit: int = 10) -> List[Dict]:
        """Get parts in a specific category"""
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
        """Perform semantic search using vector embeddings with filtering"""
        if not self.vector_search.is_available():
            print("🔍 Semantic search not available, falling back to traditional search")
            return await self._traditional_search(query, category, appliance_type, brand, top_k)

        # Build filters for semantic search
        filters = {}
        if appliance_type:
            filters["appliance_type"] = appliance_type
        if brand:
            filters["brand"] = brand
        if category:
            filters["category"] = category

        print(f"🔍 Direct semantic search with filters: {filters}")
        return await self.vector_search.semantic_search(query, top_k, filters)

    async def find_similar_parts(self, part_number: str, top_k: int = 3) -> List[Dict]:
        """Find parts similar to a given part using semantic similarity"""
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
        """Initialize the vector search index"""
        if not self.vector_search.is_available():
            print("⚠️ Cannot initialize vector search - missing API keys")
            return False

        return await self.vector_search.initialize_index()