import re
from typing import Dict, Any, List, Optional
from app.db.database import SessionLocal
from app.db.models import Customer, Order, OrderItem, Product


def get_order_by_number(order_number: str) -> Dict[str, Any]:
    """
    Look up an order by order number (e.g., 'ORD-1001' or '1001') in StoreDB.
    Returns full details including customer name, items, status, total price, and delivery info.
    """
    db = SessionLocal()
    try:
        # Normalize order number
        clean_num = order_number.strip().upper()
        if not clean_num.startswith("ORD-") and clean_num.isdigit():
            clean_num = f"ORD-{clean_num}"

        order = db.query(Order).filter(
            (Order.order_number.ilike(f"%{clean_num}%")) | 
            (Order.id == int(clean_num.replace("ORD-", "")) if clean_num.replace("ORD-", "").isdigit() else False)
        ).first()

        if not order:
            return {
                "success": False,
                "message": f"No order found matching '{order_number}' in StoreDB."
            }

        return {
            "success": True,
            "order": order.to_dict(include_items=True)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_customer_orders(customer_identifier: Any) -> Dict[str, Any]:
    """
    Look up all orders for a customer by customer ID, name, email, or phone in StoreDB.
    """
    db = SessionLocal()
    try:
        customer = None
        if isinstance(customer_identifier, int) or (isinstance(customer_identifier, str) and customer_identifier.isdigit()):
            customer = db.query(Customer).filter(Customer.id == int(customer_identifier)).first()
        elif isinstance(customer_identifier, str):
            clean_id = customer_identifier.strip()
            customer = db.query(Customer).filter(
                (Customer.name.ilike(f"%{clean_id}%")) |
                (Customer.email.ilike(f"%{clean_id}%")) |
                (Customer.phone.ilike(f"%{clean_id}%"))
            ).first()

        if not customer:
            return {
                "success": False,
                "message": f"Customer '{customer_identifier}' not found in StoreDB."
            }

        orders = db.query(Order).filter(Order.customer_id == customer.id).order_by(Order.created_at.desc()).all()

        return {
            "success": True,
            "customer": customer.to_dict(),
            "total_orders": len(orders),
            "orders": [o.to_dict(include_items=True) for o in orders]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_customer_profile(customer_identifier: Any) -> Dict[str, Any]:
    """
    Get customer profile from StoreDB.
    """
    db = SessionLocal()
    try:
        customer = None
        if isinstance(customer_identifier, int) or (isinstance(customer_identifier, str) and customer_identifier.isdigit()):
            customer = db.query(Customer).filter(Customer.id == int(customer_identifier)).first()
        elif isinstance(customer_identifier, str):
            clean_id = customer_identifier.strip()
            customer = db.query(Customer).filter(
                (Customer.name.ilike(f"%{clean_id}%")) |
                (Customer.email.ilike(f"%{clean_id}%")) |
                (Customer.phone.ilike(f"%{clean_id}%"))
            ).first()

        if not customer:
            return {"success": False, "message": f"Customer '{customer_identifier}' not found."}

        return {"success": True, "customer": customer.to_dict()}
    finally:
        db.close()


def get_latest_active_order(customer_id: int) -> Dict[str, Any]:
    """
    Find the most recent active order (Preparing, Out for Delivery, Pending) for a customer.
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.customer_id == customer_id,
            Order.status.in_(["Pending", "Preparing", "Out for Delivery"])
        ).order_by(Order.created_at.desc()).first()

        if not order:
            # Fall back to the absolute most recent order even if delivered
            order = db.query(Order).filter(
                Order.customer_id == customer_id
            ).order_by(Order.created_at.desc()).first()

        if not order:
            return {"success": False, "message": f"No orders found for customer ID {customer_id}."}

        return {"success": True, "order": order.to_dict(include_items=True)}
    finally:
        db.close()
