import re
from typing import Dict, Any, Literal
from app.agents.state import AgentState


class SupervisorAgent:
    """
    Supervisor Agent that analyzes customer queries, determines intent,
    and routes execution to specialized sub-agents:
    - OrderAgent (StoreDB SQL specialist)
    - MenuAgent (Vector DB semantic search specialist)
    - SupportAgent (Store policies & FAQ specialist)
    """

    def __init__(self):
        self.name = "Supervisor Router"

    def route(self, state: AgentState) -> AgentState:
        query = state.get("query", "").strip()
        q_lower = query.lower()

        trace_step = {
            "agent": "Supervisor Router",
            "thought": "Classifying customer intent to determine the best specialized agent...",
            "tool_called": "classify_intent",
            "tool_input": {"query": query},
            "tool_result": {}
        }

        # Check for order-related indicators
        has_order_keyword = any(k in q_lower for k in [
            "order", "ord-", "#", "tracking", "track", "delivery status",
            "where is my", "eta", "status of", "my food", "receipt", "purchase",
            "driver", "ordered"
        ])
        has_order_pattern = bool(re.search(r'(?:ORD[-_]?\d{3,4}|#\d{3,4}|\border\s*#?\d+)', query, re.IGNORECASE))

        # Check for menu/food-related indicators
        has_menu_keyword = any(k in q_lower for k in [
            "menu", "pizza", "burger", "pasta", "bowl", "sushi", "salad",
            "dessert", "drink", "beverage", "spicy", "vegan", "vegetarian",
            "gluten-free", "gluten free", "gf", "calories", "ingredients",
            "recommend", "dish", "food", "eat", "price", "under $", "cost", "available", "taste"
        ])

        # Check for general support / policy indicators
        has_support_keyword = any(k in q_lower for k in [
            "hours", "open", "close", "policy", "refund", "cancel", "payment",
            "contact", "phone", "help", "hello", "hi", "hey"
        ])

        # Decision logic
        if has_order_pattern or (has_order_keyword and not (has_menu_keyword and "add to order" in q_lower)):
            intent = "ORDER_QUERY"
            next_agent = "order_agent"
            thought = "User inquiry relates to customer orders, tracking, or order history. Routing to StoreDB Order Management Agent."

        elif has_menu_keyword:
            intent = "MENU_QUERY"
            next_agent = "menu_agent"
            thought = "User inquiry relates to food items, menu discovery, dietary options, or dish recommendations. Routing to Menu Vector DB Agent."

        elif has_support_keyword:
            intent = "SUPPORT_QUERY"
            next_agent = "support_agent"
            thought = "User inquiry relates to store hours, policies, payment methods, or general support. Routing to Support Agent."

        else:
            # Default to menu agent for food-related queries or support for general chatter
            if len(query.split()) <= 3 and any(w in q_lower for w in ["hi", "hello", "hey", "help", "who are you"]):
                intent = "SUPPORT_QUERY"
                next_agent = "support_agent"
                thought = "User initiated greeting or general inquiry. Routing to Support Agent."
            else:
                intent = "MENU_QUERY"
                next_agent = "menu_agent"
                thought = "Query could not be strictly classified as order or support. Routing to Menu Vector DB Agent for semantic search."

        trace_step["thought"] = thought
        trace_step["tool_result"] = {
            "detected_intent": intent,
            "target_agent": next_agent
        }

        state["intent"] = intent
        state["next_agent"] = next_agent
        state["agent_trace"].append(trace_step)
        return state
