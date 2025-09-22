"""
Response Agent
Generates natural language responses using Deepseek LLM cuz yk we need it
"""

import os
import httpx
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class ResponseAgent(BaseAgent):
    """Agent that generates natural language responses using Deepseek"""

    def __init__(self):
        super().__init__(
            name="response_agent",
            description="Generates natural language responses using Deepseek LLM"
        )
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = "https://api.deepseek.com/v1"

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Generate natural language response based on agent results"""
        try:
            intent_data = context.get("intent", "unknown")
            if isinstance(intent_data, str):
                intent_data = {"intent": intent_data}
            specialist_result = context.get("specialist_result", {})
            conversation_history = context.get("conversation_history", [])

            print(f"Response agent processing query: {query}")
            print(f"Intent: {intent_data.get('intent', 'unknown')}")
            print(f"Specialist result keys: {list(specialist_result.keys())}")
            print(f"Transaction type: {specialist_result.get('transaction_type', 'N/A')}")
            print(f"Parts in specialist_result: {len(specialist_result.get('parts', []))}")
            print(f"Has 'part' key: {'part' in specialist_result}")
            if 'part' in specialist_result:
                print(f"Single part: {specialist_result['part'].get('partselect_number', 'unknown')}")

            # Generate response using Deepseek if available
            if self.deepseek_api_key and self.deepseek_api_key != "demo_key":
                print(f"Using Deepseek API for response generation (key: {self.deepseek_api_key[:10]}...)")
                response_text = await self._generate_deepseek_response(
                    query, intent_data, specialist_result, conversation_history
                )
            else:
                print("Using template response (no Deepseek API key)")
                # Fallback to template responses
                response_text = self._generate_template_response(
                    query, intent_data, specialist_result
                )

            # Extract parts from specialist_result for the final response
            parts = specialist_result.get("parts", [])
            if not parts and "part" in specialist_result:
                parts = [specialist_result["part"]]

            # Filter parts based on intent - for search queries, limit to top relevant results
            filtered_parts = self._filter_parts_for_response(parts, intent_data.get("intent"), response_text)

            return AgentResult(
                success=True,
                data={
                    "message": response_text,
                    "parts": filtered_parts,
                    "query_type": intent_data.get("intent", "general"),
                    "confidence": specialist_result.get("confidence", 0.5),
                    "agent_trace": ["scope", "intent", "product", "response"],
                    "tools_used": specialist_result.get("tools_used", [])
                },
                message="Response generated successfully"
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Response generation failed: {str(e)}"
            )

    async def _generate_deepseek_response(self, query: str, intent_data: Dict,
                                        specialist_result: Dict, conversation_history: List) -> str:
        """Generate response using Deepseek API"""
        try:
            # Build context for the LLM
            context = self._build_llm_context(intent_data, specialist_result)

            system_prompt = """You are a helpful PartSelect customer service agent specializing in refrigerator and dishwasher parts.

CRITICAL GUIDELINES:
- ONLY use information provided in the Context section
- NEVER make up or guess part information if not found in context
- If no parts found in context, clearly state "I couldn't find that part number in our system"
- Be concise and helpful
- Focus only on refrigerator and dishwasher parts
- Include specific part numbers and details when available from context
- Provide clear installation and compatibility guidance only when data is available

IMPORTANT: If context shows no parts or empty results, do NOT invent part details. Instead, apologize and ask the customer to verify the part number or provide model information."""

            user_prompt = f"""
User Query: {query}
Intent: {intent_data.get('intent', 'unknown')}
Context: {context}

Please provide a helpful response about the parts query."""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.deepseek_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 400,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    generated_response = result["choices"][0]["message"]["content"]
                    print(f"Deepseek API success: Generated {len(generated_response)} characters")
                    return generated_response
                else:
                    print(f"Deepseek API error: {response.status_code} - {response.text}")
                    return self._generate_template_response(query, intent_data, specialist_result)

        except Exception as e:
            print(f"Deepseek API error: {e}")
            return self._generate_template_response(query, intent_data, specialist_result)

    def _generate_template_response(self, query: str, intent_data: Dict, specialist_result: Dict) -> str:
        """Generate template response when API is unavailable"""
        intent = intent_data.get("intent", "general")
        parts = specialist_result.get("parts", [])

        if intent == "part_lookup" and parts:
            part = parts[0]
            return f"I found the {part['name']} (Part #{part['partselect_number']}) for ${part['price']}. This {part['brand']} part is {'in stock' if part['in_stock'] else 'currently out of stock'}."

        elif intent == "compatibility_check":
            compatibility_results = specialist_result.get("compatibility_results", [])
            if compatibility_results:
                result = compatibility_results[0]
                if result.get("compatible"):
                    return f"Yes, part {result['part_number']} is compatible with model {result['model_number']}. {result.get('reason', '')}"
                else:
                    return f"Part {result['part_number']} is not compatible with model {result['model_number']}. {result.get('reason', '')}"

        elif intent == "installation_help":
            installation_guides = specialist_result.get("installation_guides", [])
            if installation_guides:
                guide = installation_guides[0]
                return f"To install {guide['part_name']}: This is a {guide['difficulty']} repair taking about {guide['time_required']}. {guide['instructions']} {'Tools required.' if guide['tools_required'] else 'No tools needed.'}"

        elif intent == "troubleshooting":
            # Check for common problems response
            common_problems = specialist_result.get("common_problems", [])
            if common_problems:
                appliance_type = specialist_result.get("appliance_type", "appliance")
                problems_text = "\n".join([
                    f"• {problem['problem']}: {problem['solutions']}"
                    for problem in common_problems[:5]  # Limit to top 5 problems
                ])
                return f"Here are the most common {appliance_type} problems and their solutions:\n\n{problems_text}"

            # Legacy troubleshooting results format
            troubleshooting_results = specialist_result.get("troubleshooting_results", [])
            if troubleshooting_results:
                return f"Based on the symptoms described, I found {len(troubleshooting_results)} potential solutions. The most likely cause could be related to {troubleshooting_results[0]['part']['category']}."

        elif intent == "product_search" and parts:
            return f"I found {len(parts)} parts matching your search. Here are the top results with pricing and availability information."

        # Transaction-related intents
        elif intent in ["cart_operations", "purchase_intent", "pricing_inquiry", "checkout_assistance"]:
            transaction_type = specialist_result.get("transaction_type", "")
            message = specialist_result.get("message", "")

            if message:
                return message
            elif transaction_type == "cart_add_request":
                return "I'd be happy to help you add an ice maker part to your cart! Let me show you the available ice maker parts first. You can then click 'Add to Cart' on the one you need."
            elif intent == "cart_operations":
                return "I can help you with cart operations. Would you like to view your cart, add items, or proceed to checkout?"
            elif intent == "purchase_intent":
                return "I'm ready to help you purchase the parts you need. Please let me know which specific part you'd like to buy."
            elif intent == "pricing_inquiry":
                return "I can provide pricing information for any parts you're interested in. Please specify which part you'd like pricing for."
            elif intent == "checkout_assistance":
                return "I'm here to help you through the checkout process. Let me guide you through each step."

        # Default response
        return "I'm here to help with refrigerator and dishwasher parts. Please let me know what specific part you're looking for, or describe the issue you're experiencing."

    def _build_llm_context(self, intent_data: Dict, specialist_result: Dict) -> str:
        """Build context string for LLM"""
        context_parts = []

        # Add intent information
        context_parts.append(f"User intent: {intent_data.get('intent', 'unknown')}")

        # Handle different data structures for parts
        parts = specialist_result.get("parts", [])

        # For transaction intents, the part might be in a "part" key (singular)
        if not parts and "part" in specialist_result:
            parts = [specialist_result["part"]]
            print(f"Using singular 'part' from transaction agent: {parts[0].get('partselect_number', 'unknown')}")

        # Add parts information with detailed data
        if parts:
            context_parts.append(f"Found {len(parts)} relevant parts:")
            for i, part in enumerate(parts[:2]):  # Limit to top 2 for context
                part_info = [
                    f"Part {i+1}: {part['name']} (#{part['partselect_number']}) - ${part['price']}",
                    f"  Brand: {part.get('brand', 'N/A')}",
                    f"  Description: {part.get('description', 'No description available')}",
                    f"  Installation Difficulty: {part.get('installation_difficulty', 'Unknown')}",
                    f"  Tools Required: {', '.join(part.get('tools_required', [])) if part.get('tools_required') else 'None'}",
                    f"  Model Compatibility: {', '.join(part.get('model_compatibility', []))[:100]}...",
                    f"  In Stock: {'Yes' if part.get('in_stock', False) else 'No'}"
                ]
                context_parts.extend(part_info)

        # Add compatibility results
        compatibility_results = specialist_result.get("compatibility_results", [])
        if compatibility_results:
            for result in compatibility_results:
                context_parts.append(f"Compatibility: {result['part_number']} with {result['model_number']} = {result['compatible']}")

        # Add installation guides
        installation_guides = specialist_result.get("installation_guides", [])
        if installation_guides:
            for guide in installation_guides:
                context_parts.append(f"Installation: {guide['difficulty']} difficulty, {guide['time_required']}")

        # Add transaction-specific information
        transaction_type = specialist_result.get("transaction_type", "")
        if transaction_type:
            context_parts.append(f"Transaction type: {transaction_type}")

            # Add cart action if available
            cart_action = specialist_result.get("cart_action", "")
            if cart_action:
                context_parts.append(f"Cart action: {cart_action}")

            # Add purchase options if available
            purchase_options = specialist_result.get("purchase_options", {})
            if purchase_options:
                context_parts.append(f"Purchase options: quantity={purchase_options.get('quantity', 1)}, shipping available")

        # Add troubleshooting common problems
        common_problems = specialist_result.get("common_problems", [])
        if common_problems:
            appliance_type = specialist_result.get("appliance_type", "appliance")
            context_parts.append(f"Common {appliance_type} problems and solutions:")
            for i, problem in enumerate(common_problems[:5]):  # Limit to top 5
                context_parts.append(f"{i+1}. {problem['problem']}")
                context_parts.append(f"   Causes: {problem['causes']}")
                context_parts.append(f"   Solutions: {problem['solutions']}")

        return "\n".join(context_parts) if context_parts else "No specific context available"

    def _filter_parts_for_response(self, parts: List[Dict], intent: str, response_text: str) -> List[Dict]:
        """Filter parts based on what's mentioned in the response text to maintain consistency"""
        if not parts:
            return parts

        # For specific part lookups, purchase intents, or installation help, return all parts
        if intent in ["part_lookup", "purchase_intent", "installation_help", "compatibility_check"]:
            return parts

        # For search queries, try to extract part numbers mentioned in response
        import re
        mentioned_part_numbers = re.findall(r'#(PS\d+)', response_text)

        if mentioned_part_numbers:
            # Return only parts mentioned in the response
            filtered_parts = []
            for part in parts:
                if part.get('partselect_number') in mentioned_part_numbers:
                    filtered_parts.append(part)

            # If we found matches, return them in the order mentioned
            if filtered_parts:
                return filtered_parts

        # Fallback: for general searches, limit to top 3 most relevant parts
        if intent in ["general_info", "product_search"] and len(parts) > 3:
            return parts[:3]

        return parts