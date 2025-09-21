"""
Transaction Agent
Handles purchase assistance, cart operations, and checkout flow
"""

import os
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult

class TransactionAgent(BaseAgent):
    """Agent that handles transaction-related operations and purchase assistance"""

    def __init__(self):
        super().__init__(
            name="transaction_agent",
            description="Handles purchase assistance, cart operations, and checkout flow"
        )

    async def process(self, query: str, context: Dict[str, Any] = None) -> AgentResult:
        """Process transaction-related queries"""
        try:
            # Handle different context structures
            if context and "intent" in context and isinstance(context["intent"], str):
                # Direct intent data format from orchestrator
                intent_data = context
                intent = context.get("intent", "")
            else:
                # Nested intent format
                intent_data = context.get("intent", {}) if context else {}
                intent = intent_data.get("intent", "")

            specialist_result = context.get("specialist_result", {}) if context else {}
            parts = specialist_result.get("parts", [])

            if intent == "purchase_intent":
                return await self._handle_purchase_intent(query, parts, context)
            elif intent == "cart_operations":
                return await self._handle_cart_operations(query, context)
            elif intent == "pricing_inquiry":
                return await self._handle_pricing_inquiry(query, parts, context)
            elif intent == "checkout_assistance":
                return await self._handle_checkout_assistance(query, context)
            else:
                return await self._handle_general_transaction_query(query, parts, context)

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"Transaction processing failed: {str(e)}"
            )

    async def _handle_purchase_intent(self, query: str, parts: List[Dict], context: Dict) -> AgentResult:
        """Handle when user wants to purchase a part"""
        if not parts:
            return AgentResult(
                success=True,
                data={
                    "transaction_type": "purchase_intent_no_parts",
                    "message": "I'd be happy to help you find the right part to purchase. Could you provide more details about what you're looking for?",
                    "suggested_actions": [
                        "Search for specific part numbers",
                        "Browse by appliance type",
                        "Get compatibility recommendations"
                    ]
                },
                message="No parts available for purchase"
            )

        # Take the first/most relevant part
        part = parts[0]

        return AgentResult(
            success=True,
            data={
                "transaction_type": "purchase_intent",
                "part": part,
                "cart_action": "add_to_cart",
                "total_price": part.get("price", 0),
                "availability": "in_stock" if part.get("in_stock", True) else "out_of_stock",
                "purchase_options": {
                    "quantity": 1,
                    "shipping_options": ["standard", "expedited"],
                    "warranty_available": True
                },
                "suggested_actions": [
                    f"Add {part['name']} to cart for ${part['price']}",
                    "View installation instructions",
                    "Check compatibility with your model",
                    "Proceed to checkout"
                ]
            },
            message=f"Ready to help you purchase {part['name']} (#{part['partselect_number']})"
        )

    async def _handle_cart_operations(self, query: str, context: Dict) -> AgentResult:
        """Handle cart-related operations"""

        # Check if user is asking to add a specific type of part
        if "add" in query.lower():
            if "ice" in query.lower() or "icemaker" in query.lower():
                return AgentResult(
                    success=True,
                    data={
                        "transaction_type": "cart_add_request",
                        "message": "I'd be happy to help you add an ice maker part to your cart! Let me show you the available ice maker parts first. You can then click 'Add to Cart' on the one you need.",
                        "suggested_actions": [
                            "Search for ice maker parts",
                            "Browse refrigerator parts",
                            "View current cart"
                        ],
                        "redirect_search": "ice maker parts"
                    },
                    message="Redirecting to show available ice maker parts"
                )
            elif "refrigerator" in query.lower() or "fridge" in query.lower():
                return AgentResult(
                    success=True,
                    data={
                        "transaction_type": "cart_add_request",
                        "message": "I'd be happy to help you add refrigerator parts to your cart! Let me show you some popular refrigerator parts that you can add to your cart.",
                        "suggested_actions": [
                            "Browse refrigerator parts",
                            "Search for specific parts",
                            "View current cart"
                        ],
                        "redirect_search": "refrigerator parts"
                    },
                    message="Redirecting to show available refrigerator parts"
                )
            elif "dishwasher" in query.lower():
                return AgentResult(
                    success=True,
                    data={
                        "transaction_type": "cart_add_request",
                        "message": "I'd be happy to help you add dishwasher parts to your cart! Let me show you some popular dishwasher parts that you can add to your cart.",
                        "suggested_actions": [
                            "Browse dishwasher parts",
                            "Search for specific parts",
                            "View current cart"
                        ],
                        "redirect_search": "dishwasher parts"
                    },
                    message="Redirecting to show available dishwasher parts"
                )

        # General cart operations
        cart_items = context.get("cart_items", [])

        return AgentResult(
            success=True,
            data={
                "transaction_type": "cart_operations",
                "cart_summary": {
                    "items_count": len(cart_items),
                    "total_price": sum(item.get("price", 0) for item in cart_items),
                    "items": cart_items
                },
                "available_actions": [
                    "view_cart",
                    "update_quantities",
                    "remove_items",
                    "proceed_to_checkout",
                    "continue_shopping"
                ],
                "suggested_actions": [
                    "View your cart summary",
                    "Update item quantities",
                    "Proceed to secure checkout"
                ]
            },
            message="Here are your cart options"
        )

    async def _handle_pricing_inquiry(self, query: str, parts: List[Dict], context: Dict) -> AgentResult:
        """Handle pricing and cost-related questions"""
        if not parts:
            return AgentResult(
                success=True,
                data={
                    "transaction_type": "pricing_inquiry_general",
                    "message": "I can help you with pricing information. Please specify which part you're interested in.",
                    "suggested_actions": [
                        "Search for a specific part number",
                        "Browse parts by category",
                        "Compare similar parts"
                    ]
                },
                message="General pricing inquiry"
            )

        pricing_data = []
        total_value = 0

        for part in parts[:3]:  # Show top 3 parts
            price = part.get("price", 0)
            total_value += price

            pricing_data.append({
                "part_number": part["partselect_number"],
                "name": part["name"],
                "brand": part["brand"],
                "price": price,
                "availability": "in_stock" if part.get("in_stock", True) else "out_of_stock",
                "savings_info": self._calculate_savings(part)
            })

        return AgentResult(
            success=True,
            data={
                "transaction_type": "pricing_inquiry",
                "pricing_details": pricing_data,
                "bundle_total": total_value if len(parts) > 1 else None,
                "shipping_info": {
                    "standard_shipping": "FREE on orders over $50",
                    "expedited_shipping": "$15.99",
                    "estimated_delivery": "3-5 business days"
                },
                "suggested_actions": [
                    "Add to cart",
                    "Compare with similar parts",
                    "Check installation requirements",
                    "View warranty options"
                ]
            },
            message=f"Here's the pricing information for {len(pricing_data)} part(s)"
        )

    async def _handle_checkout_assistance(self, query: str, context: Dict) -> AgentResult:
        """Handle checkout process assistance"""
        return AgentResult(
            success=True,
            data={
                "transaction_type": "checkout_assistance",
                "checkout_steps": [
                    "Review cart items and quantities",
                    "Enter shipping information",
                    "Select payment method",
                    "Apply discount codes (if available)",
                    "Review order summary",
                    "Complete secure payment"
                ],
                "payment_options": ["Credit Card", "PayPal", "Apple Pay"],
                "security_features": [
                    "SSL encrypted checkout",
                    "Secure payment processing",
                    "Order confirmation email"
                ],
                "support_options": [
                    "Live chat assistance",
                    "Phone support: 1-800-PARTSELECT",
                    "Email support"
                ],
                "suggested_actions": [
                    "Proceed to secure checkout",
                    "Apply discount code",
                    "Contact support if needed"
                ]
            },
            message="I'm here to help you through the checkout process"
        )

    async def _handle_general_transaction_query(self, query: str, parts: List[Dict], context: Dict) -> AgentResult:
        """Handle general transaction-related questions"""
        return AgentResult(
            success=True,
            data={
                "transaction_type": "general_transaction",
                "available_services": [
                    "Part search and selection",
                    "Price comparisons",
                    "Add items to cart",
                    "Checkout assistance",
                    "Order tracking",
                    "Return and warranty support"
                ],
                "policies": {
                    "returns": "30-day return policy",
                    "warranty": "1-year manufacturer warranty",
                    "shipping": "Free shipping on orders over $50"
                },
                "suggested_actions": [
                    "Search for specific parts",
                    "Get installation help",
                    "Check part compatibility",
                    "View your cart"
                ]
            },
            message="I can help you with purchasing, pricing, and transaction questions"
        )

    def _calculate_savings(self, part: Dict) -> Dict[str, Any]:
        """Calculate potential savings information for a part"""
        price = part.get("price", 0)

        # Simulate savings calculations (in real implementation, compare with MSRP)
        msrp = price * 1.2  # Assume 20% markup as MSRP
        savings_amount = msrp - price
        savings_percent = (savings_amount / msrp) * 100 if msrp > 0 else 0

        return {
            "msrp": round(msrp, 2),
            "partselect_price": price,
            "savings_amount": round(savings_amount, 2),
            "savings_percent": round(savings_percent, 1),
            "free_shipping_eligible": price >= 50
        }