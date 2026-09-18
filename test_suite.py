import unittest
from app.db.database import SessionLocal, init_db
from app.db.models import Customer, Order, OrderItem, Product
from app.db.seed_data import seed_database
from app.vector_store.menu_vector_store import get_menu_vector_store
from app.agents.graph import run_multi_agent_chat
from fastapi.testclient import TestClient
from app.main import app


class TestTanishRestaurantMultiAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n--- INITIALIZING TEST SUITE ---")
        seed_database()
        cls.client = TestClient(app)
        cls.vector_store = get_menu_vector_store()
        cls.vector_store.sync_with_db()

    def test_01_storedb_tables_and_relationships(self):
        """Test Customer, Order, OrderItem, Product tables and relations."""
        db = SessionLocal()
        try:
            customers = db.query(Customer).all()
            self.assertGreaterEqual(len(customers), 5, "StoreDB should have at least 5 customers")
            
            products = db.query(Product).all()
            self.assertGreaterEqual(len(products), 15, "StoreDB should have at least 15 products")

            orders = db.query(Order).all()
            self.assertGreaterEqual(len(orders), 5, "StoreDB should have at least 5 orders")

            # Check order items relationship
            order1 = db.query(Order).filter(Order.order_number == "ORD-1001").first()
            self.assertIsNotNone(order1)
            self.assertEqual(order1.customer.name, "Veer Sharma")
            self.assertGreater(len(order1.items), 0)
            self.assertEqual(order1.status, "Out for Delivery")
            print("[PASS] StoreDB Schema and Relationships Verified")
        finally:
            db.close()

    def test_02_vector_store_semantic_search(self):
        """Test Vector DB menu indexing and semantic search with filters."""
        # 1. Broad query
        results = self.vector_store.search(query="truffle mushroom pizza", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertIn("Truffle", results[0]["product"]["name"])

        # 2. Dietary filter (Gluten-Free)
        gf_results = self.vector_store.search(query="pasta", is_gluten_free=True, top_k=3)
        self.assertGreater(len(gf_results), 0)
        for r in gf_results:
            self.assertTrue(r["product"]["is_gluten_free"])

        # 3. Price filter
        cheap_results = self.vector_store.search(query="dessert", max_price=10.0, top_k=3)
        self.assertGreater(len(cheap_results), 0)
        for r in cheap_results:
            self.assertLessEqual(r["product"]["price"], 10.0)

        print("[PASS] Vector DB Semantic Search & Filtering Verified")

    def test_03_multi_agent_order_routing(self):
        """Test Supervisor -> Order Agent routing and StoreDB querying."""
        # Specific order query
        res = run_multi_agent_chat("Where is my order #ORD-1001?", customer_id=1, customer_name="Veer Sharma")
        self.assertEqual(res["active_agent"], "Order Agent")
        self.assertIsNotNone(res["order_data"])
        self.assertEqual(res["order_data"]["order_number"], "ORD-1001")
        self.assertIn("Out for Delivery", res["response"])
        self.assertGreaterEqual(len(res["agent_trace"]), 2)

        # Customer order history query
        res_history = run_multi_agent_chat("Show my past orders", customer_id=1, customer_name="Veer Sharma")

        self.assertEqual(res_history["active_agent"], "Order Agent")
        self.assertIn("Order History", res_history["response"])
        print("[PASS] Multi-Agent Order Routing & Tracking Verified")

    def test_04_multi_agent_menu_routing(self):
        """Test Supervisor -> Menu Agent routing with Vector DB search."""
        res = run_multi_agent_chat("Find spicy pizza under $20")
        self.assertEqual(res["active_agent"], "Menu Agent")
        self.assertIsNotNone(res["menu_matches"])
        self.assertGreater(len(res["menu_matches"]), 0)
        self.assertIn("Calabrian", res["response"])

        # Ingredients inquiry
        res_ing = run_multi_agent_chat("What are the ingredients in Truffle Mushroom Artisan Pizza?")
        self.assertEqual(res_ing["active_agent"], "Menu Agent")
        self.assertIn("Truffle", res_ing["response"])
        print("[PASS] Multi-Agent Menu Vector Search Routing Verified")

    def test_05_multi_agent_support_routing(self):
        """Test Supervisor -> Support Agent routing for policy questions."""
        res = run_multi_agent_chat("What are your store hours and delivery radius?")
        self.assertEqual(res["active_agent"], "Support Agent")
        self.assertIn("Hours", res["response"])
        print("[PASS] Multi-Agent Support Policy Routing Verified")

    def test_06_fastapi_endpoints(self):
        """Test FastAPI REST endpoints."""
        # Chat API
        chat_resp = self.client.post("/api/chat", json={"query": "Where is my order #ORD-1002?", "customer_id": 2})
        self.assertEqual(chat_resp.status_code, 200)
        data = chat_resp.json()
        self.assertEqual(data["active_agent"], "Order Agent")

        # Customers API
        cust_resp = self.client.get("/api/customers")
        self.assertEqual(cust_resp.status_code, 200)
        self.assertEqual(len(cust_resp.json()["customers"]), 5)

        # Orders API
        ord_resp = self.client.get("/api/orders?customer_id=1")
        self.assertEqual(ord_resp.status_code, 200)
        self.assertGreaterEqual(len(ord_resp.json()["orders"]), 2)

        # Products API
        prod_resp = self.client.get("/api/products?category=Pizza")
        self.assertEqual(prod_resp.status_code, 200)
        self.assertGreaterEqual(len(prod_resp.json()["products"]), 3)

        # Menu Vector Search API
        vec_resp = self.client.get("/api/menu/search?query=burger&is_vegetarian=true")
        self.assertEqual(vec_resp.status_code, 200)
        self.assertGreater(vec_resp.json()["total_matches"], 0)

        print("[PASS] All FastAPI Endpoints Verified Successfully")

    def test_07_pinecone_vector_store_integration(self):
        """Test Pinecone Vector Store initialization and query workflow."""
        from unittest.mock import MagicMock, patch
        from app.vector_store.menu_vector_store import MenuVectorStore

        # Test index creation when index does not exist
        mock_pc = MagicMock()
        mock_idx_item = MagicMock()
        mock_idx_item.name = "some_other_index"
        mock_pc.list_indexes.return_value = [mock_idx_item]
        mock_pc.describe_index.return_value.status = {"ready": True}

        mock_index_instance = MagicMock()
        mock_index_instance.query.return_value = {
            "matches": [
                {
                    "id": "1",
                    "score": 0.95,
                    "metadata": {
                        "id": 1,
                        "name": "Truffle Mushroom Artisan Pizza",
                        "category": "Pizza",
                        "price": 22.0,
                        "is_vegetarian": True,
                        "is_gluten_free": False,
                        "is_spicy": False,
                        "search_text": "Dish: Truffle Mushroom Artisan Pizza."
                    }
                }
            ]
        }
        mock_pc.Index.return_value = mock_index_instance

        with patch("app.vector_store.menu_vector_store.Pinecone", return_value=mock_pc):
            store = MenuVectorStore(index_name="OnlineFood", api_key="pc_test_key_123")
            # Verify Pinecone create_index was called with 'OnlineFood' and dimension 384
            mock_pc.create_index.assert_called_once()
            self.assertEqual(mock_pc.create_index.call_args[1]["name"], "onlinefood")
            self.assertEqual(mock_pc.create_index.call_args[1]["dimension"], 384)

            # Test search query through Pinecone
            res = store.search("truffle pizza", top_k=1)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["product"]["name"], "Truffle Mushroom Artisan Pizza")
            self.assertEqual(res[0]["similarity_score"], 0.95)
            print("[PASS] Pinecone Vector Store Integration & Auto-Index Creation Verified")


if __name__ == "__main__":
    unittest.main()

