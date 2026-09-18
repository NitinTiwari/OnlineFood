import re
from typing import Dict, Any, Tuple
from app.agents.state import AgentState
from app.agents.tools.order_tools import (
    get_order_by_number,
    get_customer_orders,
    get_customer_profile,
    get_latest_active_order
)


class OrderAgent:
    """
    Specialized agent for StoreDB order lookup, status tracking, customer order history,
    and delivery coordination.
    """

    def __init__(self):
        self.name = "Order Management Agent"

    def execute(self, state: AgentState) -> AgentState:
        query = state.get("query", "")
        customer_id = state.get("customer_id")
        customer_name = state.get("customer_name")
        print(self.name)
        
        trace_step = {
            "agent": "Order Agent",
            "thought": "Analyzing customer order inquiry and querying StoreDB (Customer, Order, OrderItem tables)...",
            "tool_called": None,
            "tool_input": None,
            "tool_result": None
        }

        # Check for specific order number pattern (e.g. ORD-1001, #1001, 1001, ORD0985)
        order_match = re.search(r'(?:ORD[-_]?\s*(\d{3,4})|#(\d{3,4})|order\s*(?:number|id|#)?\s*(\d{3,4}))', query, re.IGNORECASE)
        explicit_order_num = None
        if order_match:
            explicit_order_num = order_match.group(1) or order_match.group(2) or order_match.group(3)
            if explicit_order_num and not explicit_order_num.startswith("ORD-"):
                explicit_order_num = f"ORD-{explicit_order_num}"

        # 1. Direct Order Number Lookup
        if explicit_order_num:
            trace_step["thought"] = f"Identified specific order reference '{explicit_order_num}'. Querying StoreDB Order table..."
            trace_step["tool_called"] = "get_order_by_number"
            trace_step["tool_input"] = {"order_number": explicit_order_num}

            order_res = get_order_by_number(explicit_order_num)
            trace_step["tool_result"] = order_res

            if order_res.get("success"):
                order = order_res["order"]
                state["order_data"] = order
                response_text = self._format_order_response(order)
            else:
                response_text = f"I searched StoreDB for order **{explicit_order_num}**, but couldn't find a matching record. Please double check the order number."

        # 2. Inquire about Order History or All Orders
        elif any(k in query.lower() for k in ["past orders", "all orders", "order history", "previous orders", "my orders", "what have i ordered"]):
            ident = customer_id or customer_name or 1
            trace_step["thought"] = f"Retrieving complete order history for customer '{customer_name or ident}' from StoreDB..."
            trace_step["tool_called"] = "get_customer_orders"
            trace_step["tool_input"] = {"customer_identifier": ident}

            cust_res = get_customer_orders(ident)
            trace_step["tool_result"] = cust_res

            if cust_res.get("success"):
                orders = cust_res.get("orders", [])
                customer_info = cust_res.get("customer", {})
                if orders:
                    state["order_data"] = orders[0]
                    response_text = self._format_order_history_response(customer_info, orders)
                else:
                    response_text = f"Hello {customer_info.get('name', 'there')}, you currently have no orders recorded in StoreDB."
            else:
                response_text = f"Could not locate customer records for '{ident}'. Please ensure your account profile is selected."

        # 3. Active Order / Current Status Lookup (e.g., "Where is my food?", "Order status", "Track my order")
        else:
            ident = customer_id or customer_name or 1
            trace_step["thought"] = f"Customer is asking for latest order status. Querying active orders for customer #{ident} in StoreDB..."
            trace_step["tool_called"] = "get_latest_active_order"
            trace_step["tool_input"] = {"customer_id": ident}

            active_res = get_latest_active_order(ident)
            trace_step["tool_result"] = active_res

            if active_res.get("success"):
                order = active_res["order"]
                state["order_data"] = order
                response_text = self._format_order_response(order)
            else:
                response_text = "I checked StoreDB but could not find any active or past orders for your account."

        state["agent_trace"].append(trace_step)
        state["final_response"] = response_text
        state["active_agent"] = "Order Agent"
        return state

    def _format_order_response(self, order: Dict[str, Any]) -> str:
        num = order.get("order_number", "N/A")
        status = order.get("status", "Unknown")
        total = order.get("total_amount", 0.0)
        eta = order.get("estimated_delivery_time", "30-40 minutes")
        addr = order.get("delivery_address", "Delivery address on file")
        items = order.get("items", [])
        created_at = order.get("created_at", "Just now")

        status_emoji = {
            "Pending": "⏳",
            "Preparing": "🍳",
            "Out for Delivery": "🛵",
            "Delivered": "✅",
            "Cancelled": "❌"
        }.get(status, "📦")

        lines = [
            f"### {status_emoji} Order Status: **{num}**",
            f"- **Current Status:** `{status}`",
            f"- **Estimated Time / ETA:** {eta}",
            f"- **Delivery Destination:** {addr}",
            f"- **Ordered At:** {created_at}",
            f"- **Total Amount:** **${total:.2f}**",
            "",
            "#### 🛒 Items in this Order:"
        ]

        for item in items:
            name = item.get("product_name", "Food Item")
            qty = item.get("quantity", 1)
            subtotal = item.get("subtotal", 0.0)
            customs = item.get("customizations")
            custom_note = f" *(Note: {customs})*" if customs else ""
            lines.append(f"- **{qty}x** {name}{custom_note} — `${subtotal:.2f}`")

        if status == "Out for Delivery":
            lines.append("\n> 💡 **Driver Update:** Your delivery rider is en route! Keep your phone nearby.")
        elif status == "Preparing":
            lines.append("\n> 💡 **Kitchen Update:** Our chef is currently preparing and packing your fresh meal.")
        elif status == "Delivered":
            lines.append("\n> 💡 **Delivered:** Enjoy your meal! If you'd like to re-order or explore desserts, just ask.")

        return "\n".join(lines)

    def _format_order_history_response(self, customer: Dict[str, Any], orders: list) -> str:
        name = customer.get("name", "Customer")
        lines = [
            f"### 📋 Order History for **{name}**",
            f"You have **{len(orders)}** total orders in our system:\n"
        ]

        for idx, o in enumerate(orders, 1):
            num = o.get("order_number")
            status = o.get("status")
            total = o.get("total_amount", 0.0)
            created = o.get("created_at")
            item_names = [f"{i.get('quantity')}x {i.get('product_name')}" for i in o.get("items", [])]
            items_str = ", ".join(item_names) if item_names else "Items listed in receipt"

            lines.append(f"**{idx}. {num}** — `{status}` — **${total:.2f}**")
            lines.append(f"   *Items:* {items_str}")
            lines.append(f"   *Date:* {created}\n")

        lines.append("You can ask for details or live tracking for any specific order (e.g. *'Track ORD-1001'*).")
        return "\n".join(lines)
