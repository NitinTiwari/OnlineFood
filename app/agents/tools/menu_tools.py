from typing import Dict, Any, List, Optional
from app.vector_store.menu_vector_store import get_menu_vector_store


def search_menu_items(
    query: str,
    category: Optional[str] = None,
    is_vegetarian: Optional[bool] = None,
    is_gluten_free: Optional[bool] = None,
    is_spicy: Optional[bool] = None,
    max_price: Optional[float] = None,
    top_k: int = 4
) -> Dict[str, Any]:
    """
    Search menu items using the Vector DB semantic search engine.
    Supports natural language search ('spicy cheesy pizza', 'healthy vegan bowl') and filters.
    """
    vector_store = get_menu_vector_store()
    results = vector_store.search(
        query=query,
        top_k=top_k,
        category=category,
        is_vegetarian=is_vegetarian,
        is_gluten_free=is_gluten_free,
        is_spicy=is_spicy,
        max_price=max_price
    )
    print("search_menu_items: called......")
    if not results:
        return {
            "success": False,
            "message": f"No menu items found matching '{query}' with the specified criteria.",
            "products": []
        }

    products = [r["product"] for r in results]
    return {
        "success": True,
        "count": len(results),
        "results": results,
        "products": products
    }


def get_menu_recommendations(preference_or_mood: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Generate contextual food recommendations from Vector DB based on mood, craving, or dietary preference.
    """
    print("get_menu_recommendations: called......")
    vector_store = get_menu_vector_store()
    results = vector_store.search(query=preference_or_mood, top_k=top_k)

    return {
        "success": True,
        "prompt": preference_or_mood,
        "recommendations": [r["product"] for r in results]
    }


def get_item_details(item_name: str) -> Dict[str, Any]:
    """
    Get in-depth ingredients, dietary flags, calories, and description for a specific menu item.
    """
    print("get_item_details: called......")
    vector_store = get_menu_vector_store()
    product = vector_store.get_product_by_name(item_name)

    if not product:
        # Fall back to semantic search
        results = vector_store.search(query=item_name, top_k=1)
        if results:
            product = results[0]["product"]

    if not product:
        return {"success": False, "message": f"Menu item '{item_name}' was not found in our catalog."}

    return {"success": True, "product": product}


def get_all_categories() -> Dict[str, Any]:
    """
    Get all categories and summary counts of items.
    """
    print("get_all_categories: called......")
    vector_store = get_menu_vector_store()
    products = vector_store.get_all_products()
    categories = {}
    for p in products:
        cat = p.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "success": True,
        "total_items": len(products),
        "categories": categories
    }
