from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to orders
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_orders": len(self.orders) if self.orders else 0
        }


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    ingredients = Column(Text, nullable=True)
    is_vegetarian = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)
    is_spicy = Column(Boolean, default=False)
    calories = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True)
    image_url = Column(String(255), nullable=True)

    # Relationship to order items
    order_items = relationship("OrderItem", back_populates="product")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "description": self.description,
            "ingredients": self.ingredients,
            "is_vegetarian": self.is_vegetarian,
            "is_gluten_free": self.is_gluten_free,
            "is_spicy": self.is_spicy,
            "calories": self.calories,
            "is_available": self.is_available,
            "image_url": self.image_url
        }


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    status = Column(String(30), default="Pending", nullable=False)  # Pending, Preparing, Out for Delivery, Delivered, Cancelled
    total_amount = Column(Float, nullable=False)
    delivery_address = Column(String(255), nullable=False)
    estimated_delivery_time = Column(String(50), nullable=True)
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self, include_items=True):
        data = {
            "id": self.id,
            "order_number": self.order_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else "Unknown",
            "customer_email": self.customer.email if self.customer else None,
            "customer_phone": self.customer.phone if self.customer else None,
            "status": self.status,
            "total_amount": self.total_amount,
            "delivery_address": self.delivery_address,
            "estimated_delivery_time": self.estimated_delivery_time,
            "special_instructions": self.special_instructions,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
        if include_items and self.items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    customizations = Column(String(255), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "Unknown Item",
            "product_category": self.product.category if self.product else None,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": round(self.quantity * self.unit_price, 2),
            "customizations": self.customizations
        }
