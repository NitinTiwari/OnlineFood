import re
from typing import Dict, Any, List, Optional
from app.agents.state import AgentState
from app.agents.tools.menu_tools import (
    search_menu_items,
    get_menu_recommendations,
    get_item_details,
    get_all_categories
)


class MenuAgent:
    """
    Specialized agent for Menu discovery, Vector DB semantic item search,
    dietary/allergen guidance, and food recommendations.
    """

    def __init__(self):
        self.name = "Menu & Food Recommendation Agent"

    def execute(self, state: AgentState) -> AgentState:
        query = state.get("query", "")
        q_lower = query.lower()

        trace_step = {
            "agent": "Menu Vector Search Agent",
            "thought": "Extracting search intent, dietary flags, and performing semantic search in Vector DB...",
            "tool_called": None,
            "tool_input": None,
            "tool_result": None
        }

        # Extract filters
        is_veg = True if any(w in q_lower for w in ["veg", "vegetarian", "plant-based", "meatless"]) else None
        is_gf = True if any(w in q_lower for w in ["gluten-free", "gluten free", "gf", "celiac"]) else None
        is_spicy = True if any(w in q_lower for w in ["spicy", "hot", "fire", "chili", "fiery"]) else None

        # Price filter (e.g. under $15, less than 20)
        price_match = re.search(r'(?:under|less than|below|\<\s*)\$?(\d+(?:\.\d+)?)', q_lower)
        max_price = float(price_match.group(1)) if price_match else None

        # Category detection
        category = None
        for cat in ["pizza", "burger", "pasta", "bowl", "sushi", "salad", "dessert", "beverage", "drink"]:
            if cat in q_lower:
                category = cat.capitalize() if cat != "drink" else "Beverages"
                if category == "Burger":
                    category = "Burgers"
                if category == "Bowl":
                    category = "Bowls"
                if category == "Salad":
                    category = "Salads"
                if category == "Dessert":
                    category = "Desserts"
                break

        # 1. Specific Menu Item Details
        if any(w in q_lower for w in ["ingredients", "calories", "what is in", "tell me about", "describe"]) and not any(w in q_lower for w in ["menu", "recommend", "options"]):
            trace_step["thought"] = "Customer asking about specific dish details/ingredients. Searching Vector DB for item details..."
            trace_step["tool_called"] = "get_item_details"
            trace_step["tool_input"] = {"item_name": query}

            detail_res = get_item_details(query)
            trace_step["tool_result"] = detail_res

            if detail_res.get("success"):
                product = detail_res["product"]
                state["menu_matches"] = [product]
                response_text = self._format_single_product(product)
            else:
                # Fallback to vector search
                search_res = search_menu_items(query=query, top_k=3)
                state["menu_matches"] = search_res.get("products", [])
                response_text = self._format_search_results(query, search_res.get("results", []))

        # 2. General Categories Overview
        elif any(w in q_lower for w in ["what categories", "what do you have", "show categories", "view menu categories"]):
            trace_step["thought"] = "Customer asking for full menu categories breakdown..."
            trace_step["tool_called"] = "get_all_categories"
            trace_step["tool_input"] = {}

            cat_res = get_all_categories()
            trace_step["tool_result"] = cat_res
            response_text = self._format_categories_overview(cat_res)

        # 3. Semantic Vector Search
        else:
            trace_step["thought"] = (
                f"Executing Vector DB similarity search for query='{query}' "
                f"(category={category}, veg={is_veg}, gf={is_gf}, spicy={is_spicy}, max_price={max_price})..."
            )
            trace_step["tool_called"] = "search_menu_items"
            trace_step["tool_input"] = {
                "query": query,
                "category": category,
                "is_vegetarian": is_veg,
                "is_gluten_free": is_gf,
                "is_spicy": is_spicy,
                "max_price": max_price,
                "top_k": 4
            }

            search_res = search_menu_items(
                query=query,
                category=category,
                is_vegetarian=is_veg,
                is_gluten_free=is_gf,
                is_spicy=is_spicy,
                max_price=max_price,
                top_k=4
            )
            trace_step["tool_result"] = {
                "count": search_res.get("count", 0),
                "matched_names": [p.get("name") for p in search_res.get("products", [])]
            }

            results = search_res.get("results", [])
            products = search_res.get("products", [])
            state["menu_matches"] = products

            if results:
                response_text = self._format_search_results(query, results)
            else:
                response_text = (
                    f"I couldn't find any menu items strictly matching '{query}'. "
                    f"Try searching for broader terms like **pizza**, **burger**, **gluten-free pasta**, or **desserts**."
                )

        state["agent_trace"].append(trace_step)
        state["final_response"] = response_text
        state["active_agent"] = "Menu Agent"
        return state

    def _format_single_product(self, p: Dict[str, Any]) -> str:
        name = p.get("name")
        price = p.get("price", 0.0)
        cat = p.get("category")
        desc = p.get("description")
        ing = p.get("ingredients", "Fresh artisan ingredients")
        cals = p.get("calories", "N/A")

        badges = []
        if p.get("is_vegetarian"):
            badges.append("🌱 Vegetarian")
        if p.get("is_gluten_free"):
            badges.append("🌾 Gluten-Free")
        if p.get("is_spicy"):
            badges.append("🌶️ Spicy")

        badge_str = " | ".join(badges) if badges else "Standard"

        return (
            f"### 🍽️ **{name}** — `${price:.2f}`\n"
            f"- **Category:** {cat}\n"
            f"- **Dietary Tags:** {badge_str}\n"
            f"- **Calories:** {cals} kcal\n"
            f"- **Ingredients:** {ing}\n\n"
            f"**Description:** {desc}\n\n"
            f"*Available for immediate order and delivery!*"
        )

    def _format_search_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        lines = [
            f"### 🔍 Menu Search Results for *\"{query}\"*",
            f"Here are the top dishes found in our store catalog using semantic vector search:\n"
        ]

        for idx, res in enumerate(results, 1):
            p = res.get("product", {})
            name = p.get("name")
            price = p.get("price", 0.0)
            cat = p.get("category")
            desc = p.get("description")
            sim = res.get("similarity_score", 0.0)

            tags = []
            if p.get("is_vegetarian"):
                tags.append("🌱 Veg")
            if p.get("is_gluten_free"):
                tags.append("🌾 GF")
            if p.get("is_spicy"):
                tags.append("🌶️ Spicy")

            tag_str = f" `[{', '.join(tags)}]`" if tags else ""
            lines.append(f"**{idx}. {name}** — **${price:.2f}**{tag_str}")
            lines.append(f"   *{cat}* • {desc}")
            lines.append(f"   *(Semantic match score: {sim:.2f})*\n")

        lines.append("Would you like more details about any of these items or recommendations for drinks and sides?")
        return "\n".join(lines)

    def _format_categories_overview(self, cat_res: Dict[str, Any]) -> str:
        cats = cat_res.get("categories", {})
        total = cat_res.get("total_items", 0)

        lines = [
            f"### 📖 Store Menu Overview ({total} Items Available)",
            "Here are the delicious food categories we offer:\n"
        ]

        icons = {
            "Pizza": "🍕",
            "Burgers": "🍔",
            "Pasta": "🍝",
            "Bowls": "🥗",
            "Sushi": "🍣",
            "Salads": "🥬",
            "Desserts": "🍰",
            "Beverages": "🥤"
        }

        for cat_name, count in cats.items():
            icon = icons.get(cat_name, "🍽️")
            lines.append(f"- {icon} **{cat_name}** ({count} dishes)")

        lines.append("\nYou can search by asking questions like:")
        lines.append("- *'Show me spicy burgers'*")
        lines.append("- *'What gluten-free bowls are available?'*")
        lines.append("- *'Find me a sweet dessert under $10'*")

        return "\n".join(lines)
