from datetime import datetime, timedelta
from app.db.database import Base, SessionLocal, engine, init_db
from app.db.models import Customer, Order, OrderItem, Product


def seed_database():
    """Seed the database with initial customers, products, and orders."""
    # Create tables if not exist
    init_db()

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Customer).count() > 0:
            print("Database already contains records. Clearing existing records to re-seed...")
            db.query(OrderItem).delete()
            db.query(Order).delete()
            db.query(Product).delete()
            db.query(Customer).delete()
            db.commit()

        print("Seeding StoreDB...")

        # 1. Customers
        customers = [
            Customer(
                id=1,
                name="Veer Sharma",
                email="veer.s@example.com",
                phone="+91 98765 43210",
                address="Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103",
                created_at=datetime.utcnow() - timedelta(days=60)
            ),
            Customer(
                id=2,
                name="Priya Patel",
                email="priya.patel@example.com",
                phone="+91 98123 45678",
                address="12B, Sea Mist Apartments, Bandra West, Mumbai, Maharashtra 400050",
                created_at=datetime.utcnow() - timedelta(days=45)
            ),
            Customer(
                id=3,
                name="Rohan Verma",
                email="rohan.verma@example.com",
                phone="+91 97234 56789",
                address="House No. 45, Sector 15, Noida, Uttar Pradesh 201301",
                created_at=datetime.utcnow() - timedelta(days=30)
            ),
            Customer(
                id=4,
                name="Ananya Iyer",
                email="ananya.iyer@example.com",
                phone="+91 99345 67890",
                address="Flat 3A, Temple View Residency, Mylapore, Chennai, Tamil Nadu 600004",
                created_at=datetime.utcnow() - timedelta(days=15)
            ),
            Customer(
                id=5,
                name="Kabir Mehta",
                email="kabir.mehta@example.com",
                phone="+91 96456 78901",
                address="Villa 8, Jubilee Hills, Road No. 36, Hyderabad, Telangana 500033",
                created_at=datetime.utcnow() - timedelta(days=5)
            )
        ]
        db.add_all(customers)
        db.commit()

        # 2. Products (Menu)
        products = [
            # Pizzas
            Product(
                id=1,
                name="Truffle Mushroom Artisan Pizza",
                category="Pizza",
                price=18.99,
                description="Wood-fired sourdough crust topped with wild portobello and cremini mushrooms, white truffle oil, mozzarella, and fresh thyme.",
                ingredients="Sourdough crust, Wild Mushrooms, Mozzarella, White Truffle Oil, Fresh Thyme, Garlic Butter",
                is_vegetarian=True,
                is_gluten_free=False,
                is_spicy=False,
                calories=820,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500"
            ),
            Product(
                id=2,
                name="Spicy Calabrian Pepperoni Pizza",
                category="Pizza",
                price=17.50,
                description="San Marzano tomato base with double artisanal pepperoni, spicy Calabrian chili flakes, hot honey drizzle, and fresh basil.",
                ingredients="San Marzano Sauce, Mozzarella, Artisanal Pepperoni, Calabrian Chilis, Hot Honey, Oregano",
                is_vegetarian=False,
                is_gluten_free=False,
                is_spicy=True,
                calories=950,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1628840042765-356cda07504e?w=500"
            ),
            Product(
                id=3,
                name="Margherita Di Bufala Pizza",
                category="Pizza",
                price=15.99,
                description="Classic Neapolitan pizza featuring creamy buffalo mozzarella, San Marzano tomato sauce, fresh fragrant basil, and extra virgin olive oil.",
                ingredients="Flour, Buffalo Mozzarella, San Marzano Tomatoes, Fresh Basil, EVOO, Sea Salt",
                is_vegetarian=True,
                is_gluten_free=False,
                is_spicy=False,
                calories=740,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=500"
            ),
            # Burgers
            Product(
                id=4,
                name="Smoked Angus Bacon Smash Burger",
                category="Burgers",
                price=16.50,
                description="Double smashed 100% Black Angus beef patties, applewood smoked bacon, aged sharp cheddar, caramelized onions, and secret umami sauce on a brioche bun.",
                ingredients="Black Angus Beef, Smoked Bacon, Aged Cheddar, Caramelized Onion, Brioche Bun, Umami House Sauce",
                is_vegetarian=False,
                is_gluten_free=False,
                is_spicy=False,
                calories=1020,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"
            ),
            Product(
                id=5,
                name="Firecracker Crispy Chicken Burger",
                category="Burgers",
                price=15.25,
                description="Buttermilk fried crispy chicken thigh dipped in fiery Nashville chili glaze, crunchy purple cabbage slaw, and dill pickles.",
                ingredients="Crispy Chicken Thigh, Nashville Chili Glaze, Purple Slaw, Pickles, Chipotle Mayo, Potato Brioche",
                is_vegetarian=False,
                is_gluten_free=False,
                is_spicy=True,
                calories=890,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=500"
            ),
            Product(
                id=6,
                name="Plant-Power Truffle Burger",
                category="Burgers",
                price=16.00,
                description="100% plant-based Beyond meat patty, vegan smoked gouda, baby arugula, roasted garlic aioli, and sauteed balsamic mushrooms.",
                ingredients="Beyond Meat Patty, Vegan Gouda, Sauteed Mushrooms, Baby Arugula, Garlic Aioli, Vegan Brioche",
                is_vegetarian=True,
                is_gluten_free=False,
                is_spicy=False,
                calories=720,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1584947897591-66774a307044?w=500"
            ),
            # Pasta & Bowls
            Product(
                id=7,
                name="Creamy Wild Mushroom Fettuccine",
                category="Pasta",
                price=17.00,
                description="Handmade fettuccine ribbons tossed in a velvety garlic parmesan cream sauce with sauteed chanterelles and crispy sage.",
                ingredients="Fresh Fettuccine, Chanterelle Mushrooms, Heavy Cream, Aged Parmesan, Garlic, Fresh Sage",
                is_vegetarian=True,
                is_gluten_free=False,
                is_spicy=False,
                calories=860,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1608897013039-887f21d8c804?w=500"
            ),
            Product(
                id=8,
                name="Gluten-Free Penne Arrabiata",
                category="Pasta",
                price=14.99,
                description="Brown rice & quinoa gluten-free penne tossed in a spicy garlic tomato sauce, Kalamata olives, capers, and fresh Italian parsley.",
                ingredients="Gluten-Free Penne, Crushed Tomatoes, Red Chili Flakes, Garlic, Kalamata Olives, Parsley",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=True,
                calories=580,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1621996346565-e3d5d6281699?w=500"
            ),
            Product(
                id=9,
                name="Salmon Teriyaki Power Bowl",
                category="Bowls",
                price=18.50,
                description="Pan-seared Atlantic salmon glazed with house ginger teriyaki, served over warm brown rice with edamame, avocado, and pickled ginger.",
                ingredients="Atlantic Salmon, Ginger Teriyaki Glaze, Brown Rice, Avocado, Edamame, Pickled Ginger, Sesame Seeds",
                is_vegetarian=False,
                is_gluten_free=True,
                is_spicy=False,
                calories=680,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500"
            ),
            Product(
                id=10,
                name="Spicy Thai Green Curry Tofu Bowl",
                category="Bowls",
                price=15.50,
                description="Crispy organic tofu simmered in aromatic lemongrass coconut green curry with bamboo shoots, bell peppers, and jasmine rice.",
                ingredients="Crispy Tofu, Coconut Milk, Green Curry Paste, Bamboo Shoots, Thai Basil, Jasmine Rice",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=True,
                calories=620,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"
            ),
            # Asian & Sushi
            Product(
                id=11,
                name="Dragon Fire Sushi Roll (8 pcs)",
                category="Sushi",
                price=16.99,
                description="Tempura shrimp and cucumber inside, wrapped with spicy tuna, sliced avocado, topped with spicy sriracha mayo and crispy tempura crunch.",
                ingredients="Tempura Shrimp, Spicy Tuna, Sliced Avocado, Sushi Rice, Nori, Spicy Mayo, Eel Sauce",
                is_vegetarian=False,
                is_gluten_free=False,
                is_spicy=True,
                calories=540,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500"
            ),
            Product(
                id=12,
                name="Vegan Rainbow Garden Roll (8 pcs)",
                category="Sushi",
                price=13.50,
                description="Crisp asparagus, cucumber, and pickled radish wrapped in sushi rice and topped with thin slices of mango, avocado, and ponzu glaze.",
                ingredients="Asparagus, Cucumber, Pickled Daikon, Avocado, Fresh Mango, Ponzu, Toasted Sesame",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=False,
                calories=380,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=500"
            ),
            # Salads
            Product(
                id=13,
                name="Mediterranean Greek Quinoa Salad",
                category="Salads",
                price=13.00,
                description="Crisp romaine, tri-color quinoa, heirloom cherry tomatoes, cucumbers, Kalamata olives, creamy feta cheese, and lemon herb vinaigrette.",
                ingredients="Romaine, Quinoa, Cherry Tomatoes, Cucumbers, Feta Cheese, Kalamata Olives, Lemon Herb Dressing",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=False,
                calories=440,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500"
            ),
            # Desserts
            Product(
                id=14,
                name="Molten Dark Chocolate Lava Cake",
                category="Desserts",
                price=9.50,
                description="Warm Belgian 70% dark chocolate cake with a rich liquid center, dusted with powdered sugar and served with strawberry compote.",
                ingredients="Belgian Dark Chocolate, Butter, Organic Eggs, Sugar, Flour, Fresh Strawberry Coulis",
                is_vegetarian=True,
                is_gluten_free=False,
                is_spicy=False,
                calories=520,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500"
            ),
            Product(
                id=15,
                name="Classic Sicilian Pistachio Tiramisu",
                category="Desserts",
                price=8.99,
                description="Espresso-soaked ladyfingers layered with creamy mascarpone, bronte pistachio cream, and dusted with dark cocoa powder.",
                ingredients="Ladyfingers, Espresso, Mascarpone, Pistachio Cream, Cocoa, Marsala",
                is_vegetarian=True,
                is_gluten_free=False,
                is_spicy=False,
                calories=480,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"
            ),
            Product(
                id=16,
                name="Vegan Mango Coconut Chia Pudding",
                category="Desserts",
                price=7.50,
                description="Creamy chia seeds soaked in vanilla coconut milk, layered with pure Alphonso mango puree and toasted coconut chips.",
                ingredients="Chia Seeds, Coconut Milk, Pure Mango Puree, Organic Agave, Toasted Coconut Chips",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=False,
                calories=320,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=500"
            ),
            # Beverages
            Product(
                id=17,
                name="Sparkling Hibiscus Berry Lemonade",
                category="Beverages",
                price=5.50,
                description="Freshly brewed organic hibiscus tea with crushed blackberries, fresh Meyer lemon juice, sparkling water, and mint.",
                ingredients="Hibiscus Tea, Wild Blackberries, Meyer Lemon Juice, Sparkling Water, Agave, Mint",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=False,
                calories=110,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500"
            ),
            Product(
                id=18,
                name="Iced Brown Sugar Oat Milk Latte",
                category="Beverages",
                price=6.00,
                description="Double shot of dark roast espresso shaken with house cinnamon brown sugar syrup and poured over creamy oat milk.",
                ingredients="Espresso, Gluten-Free Oat Milk, Dark Brown Sugar, Ceylon Cinnamon, Ice",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=False,
                calories=190,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=500"
            ),
            Product(
                id=19,
                name="Cold-Pressed Green Detox Juice",
                category="Beverages",
                price=7.00,
                description="Pure cold-pressed cucumber, organic celery, Granny Smith apple, baby spinach, ginger, and fresh lime.",
                ingredients="Cucumber, Celery, Green Apple, Spinach, Ginger, Lime",
                is_vegetarian=True,
                is_gluten_free=True,
                is_spicy=False,
                calories=130,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1613478223719-2ab802602423?w=500"
            ),
            Product(
                id=20,
                name="Cheeze burger",
                category="Burgers",
                price=7.00,
                description="Cheezy, cheesy.",
                ingredients="Cheese, Bun, Patty",
                is_vegetarian=True,
                is_gluten_free=False,
                is_spicy=False,
                calories=230,
                is_available=True,
                image_url="https://images.unsplash.com/photo-1613478223720-2ab802602423?w=500"
            )
        ]
        db.add_all(products)
        db.commit()

        # 3. Orders and OrderItems
        now = datetime.utcnow()

        # Order 1: Veer Sharma - Out for Delivery
        order1 = Order(
            id=1,
            order_number="ORD-1001",
            customer_id=1,  # Veer Sharma
            status="Out for Delivery",
            total_amount=36.49,
            delivery_address="Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103",
            estimated_delivery_time="15-20 minutes (Driver en route: Rajesh on E-Bike)",
            special_instructions="Please ring the doorbell and leave at door.",
            created_at=now - timedelta(minutes=28),
            updated_at=now - timedelta(minutes=5)
        )
        db.add(order1)
        db.commit()

        items1 = [
            OrderItem(order_id=1, product_id=1, quantity=1, unit_price=18.99, customizations="Extra Truffle Oil"),
            OrderItem(order_id=1, product_id=11, quantity=1, unit_price=16.99, customizations="Extra Wasabi & Ginger"),
            OrderItem(order_id=1, product_id=17, quantity=1, unit_price=5.50, customizations="Less Ice")
        ]
        order1.total_amount = sum(i.quantity * i.unit_price for i in items1)
        db.add_all(items1)

        # Order 2: Veer Sharma - Past Delivered
        order2 = Order(
            id=2,
            order_number="ORD-0985",
            customer_id=1,  # Veer Sharma
            status="Delivered",
            total_amount=31.49,
            delivery_address="Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103",
            estimated_delivery_time="Delivered at 1:45 PM",
            special_instructions="None",
            created_at=now - timedelta(days=3, hours=4),
            updated_at=now - timedelta(days=3, hours=3)
        )
        db.add(order2)
        db.commit()

        items2 = [
            OrderItem(order_id=2, product_id=4, quantity=1, unit_price=16.50, customizations="Well Done"),
            OrderItem(order_id=2, product_id=14, quantity=1, unit_price=9.50, customizations="Extra Strawberry Sauce"),
            OrderItem(order_id=2, product_id=18, quantity=1, unit_price=6.00, customizations="Extra Oat Milk")
        ]
        order2.total_amount = sum(i.quantity * i.unit_price for i in items2)
        db.add_all(items2)

        # Order 3: Priya Patel - Preparing
        order3 = Order(
            id=3,
            order_number="ORD-1002",
            customer_id=2,  # Priya Patel
            status="Preparing",
            total_amount=34.50,
            delivery_address="12B, Sea Mist Apartments, Bandra West, Mumbai, Maharashtra 400050",
            estimated_delivery_time="30-35 minutes (Kitchen assembling order)",
            special_instructions="Call when outside building lobby.",
            created_at=now - timedelta(minutes=12),
            updated_at=now - timedelta(minutes=10)
        )
        db.add(order3)
        db.commit()

        items3 = [
            OrderItem(order_id=3, product_id=2, quantity=1, unit_price=17.50, customizations="Extra Spicy"),
            OrderItem(order_id=3, product_id=7, quantity=1, unit_price=17.00, customizations="Gluten-Free noodles if possible")
        ]
        order3.total_amount = sum(i.quantity * i.unit_price for i in items3)
        db.add_all(items3)

        # Order 4: Rohan Verma - Pending
        order4 = Order(
            id=4,
            order_number="ORD-1003",
            customer_id=3,  # Rohan Verma
            status="Pending",
            total_amount=24.00,
            delivery_address="House No. 45, Sector 15, Noida, Uttar Pradesh 201301",
            estimated_delivery_time="40-45 minutes (Awaiting kitchen confirmation)",
            special_instructions="Gate code is #4321.",
            created_at=now - timedelta(minutes=4),
            updated_at=now - timedelta(minutes=4)
        )
        db.add(order4)
        db.commit()

        items4 = [
            OrderItem(order_id=4, product_id=9, quantity=1, unit_price=18.50, customizations="No pickled ginger"),
            OrderItem(order_id=4, product_id=17, quantity=1, unit_price=5.50, customizations="Standard")
        ]
        order4.total_amount = sum(i.quantity * i.unit_price for i in items4)
        db.add_all(items4)

        # Order 5: Ananya Iyer - Delivered
        order5 = Order(
            id=5,
            order_number="ORD-0950",
            customer_id=4,  # Ananya Iyer
            status="Delivered",
            total_amount=44.98,
            delivery_address="Flat 3A, Temple View Residency, Mylapore, Chennai, Tamil Nadu 600004",
            estimated_delivery_time="Delivered Yesterday at 7:30 PM",
            special_instructions="Leave with building concierge.",
            created_at=now - timedelta(days=1, hours=6),
            updated_at=now - timedelta(days=1, hours=5)
        )
        db.add(order5)
        db.commit()


        items5 = [
            OrderItem(order_id=5, product_id=1, quantity=1, unit_price=18.99, customizations="Thin crust"),
            OrderItem(order_id=5, product_id=13, quantity=1, unit_price=13.00, customizations="Dressing on the side"),
            OrderItem(order_id=5, product_id=15, quantity=1, unit_price=8.99, customizations="Extra pistachio"),
            OrderItem(order_id=5, product_id=19, quantity=1, unit_price=7.00, customizations="No ice")
        ]
        order5.total_amount = sum(i.quantity * i.unit_price for i in items5)
        db.add_all(items5)

        db.commit()
        print(f"Successfully seeded StoreDB with {len(customers)} customers, {len(products)} products, and 5 orders!")


    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
