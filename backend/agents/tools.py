"""
Tool system for PartSelect agents
Tools are reusable functions that agents can call to perform specific tasks
"""

import json
import re
from typing import List, Dict, Any, Optional

class PartSelectTools:
    """Collection of tools for PartSelect agents"""

    def __init__(self, parts_data: List[Dict]):
        self.parts_data = parts_data

    async def search_parts(self, query: str, category: str = None,
                          appliance_type: str = None, limit: int = 10) -> List[Dict]:
        """Search for parts based on query, category, and appliance type"""
        try:
            results = []
            query_lower = query.lower()

            for part in self.parts_data:
                score = 0.0

                # Exact part number match (highest priority)
                if (part["partselect_number"].lower() in query_lower or
                    part["manufacturer_part_number"].lower() in query_lower):
                    score = 1.0

                # Category match
                elif category and part["category"].lower() == category.lower():
                    score = 0.9

                # Appliance type match
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

        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    async def get_part_details(self, part_number: str) -> Optional[Dict]:
        """Get detailed information about a specific part"""
        try:
            for part in self.parts_data:
                if (part["partselect_number"].lower() == part_number.lower() or
                    part["manufacturer_part_number"].lower() == part_number.lower()):
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