import re
import os
import json
from typing import Dict, Any, Literal
from app.agents.state import AgentState
from groq import Groq
from app.agents.tools import order_tools, menu_tools

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
        # Groq client will be lazily instantiated; set via environment variables (.env)
        self._groq_client = None
        self._groq_api_key = os.getenv("GROQ_API_KEY")
        self._groq_model = os.getenv("GROQ_MODEL", "mixtral-8b7-32768")

    def _get_groq_client(self) -> Groq:
        """Create (or reuse) a Groq client instance using the API key."""
        if not self._groq_api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment variables")
        if self._groq_client is None:
            self._groq_client = Groq(api_key=self._groq_api_key)
        return self._groq_client

    # ---------------------------------------------------------------------
    # Keyword‑based routing (fallback)
    # ---------------------------------------------------------------------
    def _keyword_route(self, state: AgentState) -> AgentState:
        query = state.get("query", "").strip()
        q_lower = query.lower()

        trace_step = {
            "agent": "Supervisor Router",
            "thought": "Classifying customer intent using keyword heuristics...",
            "tool_called": "classify_intent",
            "tool_input": {"query": query},
            "tool_result": {}
        }

        # Order related detection
        has_order_keyword = any(k in q_lower for k in [
            "order", "ord-", "#", "tracking", "track", "delivery status",
            "where is my", "eta", "status of", "my food", "receipt", "purchase",
            "driver", "ordered"
        ])
        has_order_pattern = bool(re.search(r'(?:ORD[-_]?\d{3,4}|#\d{3,4}|\border\s*#?\d+)', query, re.IGNORECASE))

        # Menu related detection
        has_menu_keyword = any(k in q_lower for k in [
            "menu", "pizza", "burger", "pasta", "bowl", "sushi", "salad",
            "dessert", "drink", "beverage", "spicy", "vegan", "vegetarian",
            "gluten-free", "gluten free", "gf", "calories", "ingredients",
            "recommend", "dish", "food", "eat", "price", "under $", "cost", "available", "taste"
        ])

        # Support related detection
        has_support_keyword = any(k in q_lower for k in [
            "hours", "open", "close", "policy", "refund", "cancel", "payment",
            "contact", "phone", "help", "hello", "hi", "hey"
        ])

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
            if len(query.split()) <= 3 and any(w in q_lower for w in ["hi", "hello", "hey", "help", "who are you"]):
                intent = "SUPPORT_QUERY"
                next_agent = "support_agent"
                thought = "User initiated greeting or general inquiry. Routing to Support Agent."
            else:
                intent = "MENU_QUERY"
                next_agent = "menu_agent"
                thought = "Query could not be strictly classified as order or support. Routing to Menu Vector DB Agent for semantic search."

        trace_step["thought"] = thought
        trace_step["tool_result"] = {"detected_intent": intent, "target_agent": next_agent}
        state["intent"] = intent
        state["next_agent"] = next_agent
        state["agent_trace"].append(trace_step)
        return state

    # ---------------------------------------------------------------------
    # LLM‑based routing using Groq
    # ---------------------------------------------------------------------
    def _llm_route(self, state: AgentState) -> AgentState:
        query = state.get("query", "").strip()
        trace_step = {
            "agent": "Supervisor Router",
            "thought": "Classifying customer intent using Groq LLM...",
            "tool_called": "classify_intent_llm",
            "tool_input": {"query": query},
            "tool_result": {}
        }
        try:
            client = self._get_groq_client()
            system_prompt = (
                "You are an intent classifier for an online food ordering system. "
                "Classify the user's request into one of the following intents: "
                "ORDER_QUERY, MENU_QUERY, SUPPORT_QUERY. Return a JSON object with two fields: "
                "'intent' and 'target_agent' (order_agent, menu_agent, support_agent)."
            )
            response = client.chat.completions.create(
                model=self._groq_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
                temperature=0,
                max_tokens=100,
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            intent = result.get("intent")
            next_agent = result.get("target_agent")
            thought = f"LLM classified intent as {intent}, routing to {next_agent}."
            print("\n Intent  ", intent, "\n Next Agent  ", next_agent, "\n Thought  ", thought)
        except Exception as e:
            # Fallback to keyword routing on any error
            trace_step["thought"] = f"LLM classification failed ({e}); falling back to keyword routing."
            state = self._keyword_route(state)
            trace_step["tool_result"] = {"fallback": True}
            state["agent_trace"].append(trace_step)
            return state

        trace_step["thought"] = thought
        trace_step["tool_result"] = {"detected_intent": intent, "target_agent": next_agent}
        state["intent"] = intent
        state["next_agent"] = next_agent
        state["agent_trace"].append(trace_step)
        return state

    def route(self, state: AgentState) -> AgentState:
        """Route the incoming state to the appropriate sub-agent.
        Attempts LLM based classification first, falling back to keyword routing on error.
        """
        return self._llm_route(state)


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
