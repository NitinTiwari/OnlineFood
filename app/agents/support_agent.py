from typing import Dict, Any
from app.agents.state import AgentState


class SupportAgent:
    """
    Specialized agent for general customer service, operating hours, delivery radius,
    cancellation policies, allergen advice, and contact information.
    """

    def __init__(self):
        self.name = "Customer Support & Policy Agent"

    def execute(self, state: AgentState) -> AgentState:
        query = state.get("query", "").lower()

        trace_step = {
            "agent": "Support Agent",
            "thought": "Customer asking for general store information or policies. Accessing FAQ knowledge base...",
            "tool_called": "get_store_policy_info",
            "tool_input": {"topic": query},
            "tool_result": {"status": "policy_retrieved"}
        }

        if any(w in query for w in ["hours", "open", "closing", "time", "when"]):
            response_text = (
                "### ⏰ Store Operating Hours\n"
                "- **Monday – Thursday:** 10:00 AM – 10:30 PM\n"
                "- **Friday – Saturday:** 10:00 AM – 11:45 PM\n"
                "- **Sunday:** 11:00 AM – 10:00 PM\n\n"
                "Orders placed online are fulfilled immediately during kitchen hours!"
            )

        elif any(w in query for w in ["delivery", "radius", "fee", "free delivery", "how long", "speed"]):
            response_text = (
                "### 🛵 Delivery Information\n"
                "- **Average Delivery Time:** 30–45 minutes\n"
                "- **Delivery Radius:** Up to 12 miles from our central kitchen\n"
                "- **Delivery Fee:** $2.99 flat rate (*Free delivery on all orders over $30*)\n"
                "- **Real-time Tracking:** Available on all active orders with live driver status!"
            )

        elif any(w in query for w in ["cancel", "refund", "return", "mistake", "wrong"]):
            response_text = (
                "### 🔄 Cancellation & Refund Policy\n"
                "- **Orders in `Pending` or `Preparing`:** Can be modified or cancelled immediately with 100% full refund.\n"
                "- **Orders `Out for Delivery`:** Cannot be cancelled as food has already departed, but our support desk can assist with replacement or credits if there is any delivery delay.\n"
                "- **Support Hotline:** 1-800-FOOD-AI (24/7)"
            )

        elif any(w in query for w in ["pay", "payment", "card", "apple pay", "cash", "crypto"]):
            response_text = (
                "### 💳 Accepted Payment Methods\n"
                "- Credit & Debit Cards (Visa, MasterCard, Amex, Discover)\n"
                "- Apple Pay & Google Pay\n"
                "- Cash on Delivery (COD)\n"
                "- In-app Tanish Restaurant digital wallet"
            )

        else:
            response_text = (
                "### 👋 Hello from Tanish Restaurant AI Support!\n"
                "I am your multi-agent dining concierge. Here is how I can assist you:\n\n"
                "1. **Order Tracking:** Ask *'Where is my order #ORD-1001?'* or *'Show my recent orders'*\n"
                "2. **Menu Discovery:** Ask *'Find spicy pizzas'* or *'Show gluten-free pasta options under $16'*\n"
                "3. **Store Inquiries:** Ask about our operating hours, delivery fees, or allergen guidelines.\n\n"
                "How can I help you today?"
            )

        state["agent_trace"].append(trace_step)
        state["final_response"] = response_text
        state["active_agent"] = "Support Agent"
        return state
