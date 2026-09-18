import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db, init_db
from app.db.models import Customer, Order, Product, OrderItem
from app.db.seed_data import seed_database
from app.vector_store.menu_vector_store import get_menu_vector_store
from app.agents.graph import run_multi_agent_chat

app = FastAPI(
    title="Tanish Restaurant - Online Food Chat Assistant",
    description="Multi-agent assistant powered by StoreDB and Vector DB Menu Search",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)


# Pydantic Request Models
class ChatRequest(BaseModel):
    query: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []


class DbResetResponse(BaseModel):
    success: bool
    message: str


@app.on_event("startup")
def on_startup():
    """Initialize DB and Vector Store on app startup."""
    init_db()
    print("on_startup: called......")
    # Check if database has records; if not, seed it
    db = next(get_db())
    try:
        if db.query(Customer).count() == 0:
            print("StoreDB is empty. Running initial database seed...")
            seed_database()
        # Initialize and sync vector store
        store = get_menu_vector_store()
        store.sync_with_db()
    finally:
        db.close()


# API Endpoints
@app.post("/api/chat")
def chat_endpoint(payload: ChatRequest):
    """
    Main Multi-Agent Chat endpoint.
    Routes queries through LangGraph state machine (Supervisor -> Order / Menu / Support Agent).
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        print("chat_endpoint: called......")
        result = run_multi_agent_chat(
            query=payload.query.strip(),
            customer_id=payload.customer_id,
            customer_name=payload.customer_name,
            history=payload.history
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customers")
def get_customers(db: Session = Depends(get_db)):
    """List all customers in StoreDB for testing and account switching."""
    print("get_customers: called......")
    customers = db.query(Customer).all()
    return {"customers": [c.to_dict() for c in customers]}


@app.get("/api/orders")
def get_orders(customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List orders in StoreDB, optionally filtered by customer."""
    print("get_orders: called......")
    query = db.query(Order)
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)
    orders = query.order_by(Order.created_at.desc()).all()
    return {"orders": [o.to_dict(include_items=True) for o in orders]}


@app.get("/api/products")
def get_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    """List all products in StoreDB."""
    print("get_products: called......")
    query = db.query(Product)
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    products = query.all()
    return {"products": [p.to_dict() for p in products]}


@app.get("/api/menu/search")
def search_menu_vector_db(
    query: str = Query(..., description="Semantic search query"),
    category: Optional[str] = None,
    is_vegetarian: Optional[bool] = None,
    is_gluten_free: Optional[bool] = None,
    is_spicy: Optional[bool] = None,
    max_price: Optional[float] = None,
    top_k: int = 5
):
    """Direct Vector DB semantic search endpoint."""
    print("search_menu_vector_db: called......")
    store = get_menu_vector_store()
    results = store.search(
        query=query,
        top_k=top_k,
        category=category,
        is_vegetarian=is_vegetarian,
        is_gluten_free=is_gluten_free,
        is_spicy=is_spicy,
        max_price=max_price
    )
    return {"query": query, "total_matches": len(results), "results": results}


@app.post("/api/db/reset")
def reset_db_endpoint():
    """Reset and re-seed StoreDB with fresh records and re-index Vector DB."""
    print("reset_db_endpoint: called......")
    try:
        seed_database()
        store = get_menu_vector_store()
        store.sync_with_db()
        return {"success": True, "message": "StoreDB & Vector DB successfully re-seeded and re-indexed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    """Serve the single-page application UI."""
    print("serve_index: called......")
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Tanish Restaurant AI Backend Running."}
