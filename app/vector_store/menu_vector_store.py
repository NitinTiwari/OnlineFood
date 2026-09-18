
import os
import time
from typing import List, Dict, Any, Optional
import numpy as np
from dotenv import load_dotenv

# Pinecone import moved to lazy import within _init_pinecone
from langchain_huggingface import HuggingFaceEmbeddings

from app.db.database import SessionLocal
from app.db.models import Product

load_dotenv()


class MenuVectorStore:
    """
    Pinecone Cloud Vector Database engine for menu items semantic search.
    Embeds StoreDB product catalog into Pinecone vector index named 'OnlineFood'.
    """

    def __init__(
        self,
        index_name: Optional[str] = None,
        api_key: Optional[str] = None,
        cloud: Optional[str] = None,
        region: Optional[str] = None,
        embedding_model_name: Optional[str] = None,
    ):
        self.api_key = (api_key or os.getenv("PINECONE_API_KEY", "")).strip()
        raw_name = (index_name or os.getenv("PINECONE_INDEX_NAME", "onlinefood")).strip()
        self.index_name = raw_name.lower().replace("_", "-")
        self.cloud = (cloud or os.getenv("PINECONE_CLOUD", "aws")).strip()
        self.region = (region or os.getenv("PINECONE_REGION", "us-east-1")).strip()
        self.embedding_model_name = (
            embedding_model_name or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        ).strip()
        self.dimension = 384  # Standard dimension for sentence-transformers/all-MiniLM-L6-v2 and BAAI/bge-small-en-v1.5

        self.documents: List[Dict[str, Any]] = []
        self._cached_embeddings: Optional[np.ndarray] = None
        self.embedder: Optional[HuggingFaceEmbeddings] = None
        self.pc: Optional[Any] = None
        self.index = None

        self._init_embedder()
        self._init_pinecone()
        self.sync_with_db()

    def _init_embedder(self):
        """Initialize HuggingFaceEmbeddings model."""
        try:
            hf_token = os.getenv("HF_TOKEN")
            model_kwargs = {"trust_remote_code": True}
            if hf_token:
                model_kwargs["token"] = hf_token

            self.embedder = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                model_kwargs=model_kwargs,
            )
            print(f"MenuVectorStore: HuggingFaceEmbeddings initialized with model '{self.embedding_model_name}'.")
        except Exception as e:
            print(f"MenuVectorStore: Failed to initialize HuggingFaceEmbeddings ({e}).")
            self.embedder = None

    def _init_pinecone(self):
        """Initialize Pinecone client and ensure the 'onlinefood' index exists."""
        if not self.api_key:
            print(
                "MenuVectorStore: [WARNING] PINECONE_API_KEY is not set in environment or .env. "
                f"Please set PINECONE_API_KEY to store vectors in Pinecone index '{self.index_name}'."
            )
            return

        try:
            from pinecone import Pinecone, ServerlessSpec
            self.pc = Pinecone(api_key=self.api_key)
            indexes_res = self.pc.list_indexes()
            if hasattr(indexes_res, "names"):
                existing_indexes = list(indexes_res.names())
            elif isinstance(indexes_res, (list, tuple)):
                existing_indexes = [getattr(idx, "name", str(idx)) for idx in indexes_res]
            else:
                existing_indexes = [str(indexes_res)]

            if self.index_name not in existing_indexes:
                print(f"MenuVectorStore: Index '{self.index_name}' not found on Pinecone. Creating new Serverless index...")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud=self.cloud, region=self.region),
                )
                # Wait until index is ready
                while True:
                    desc = self.pc.describe_index(self.index_name)
                    status = getattr(desc, "status", {})
                    if isinstance(status, dict) and status.get("ready", False):
                        break
                    elif getattr(status, "ready", False):
                        break
                    time.sleep(1)
                print(f"MenuVectorStore: Pinecone index '{self.index_name}' created successfully.")

            self.index = self.pc.Index(self.index_name)
            print(f"MenuVectorStore: Connected to Pinecone index '{self.index_name}'.")
        except Exception as e:
            print(f"MenuVectorStore: Pinecone initialization error ({e}).")
            self.index = None


    def _create_search_text(self, product: Product) -> str:
        """Create rich textual representation for vector embedding."""
        dietary_tags = []
        if product.is_vegetarian:
            dietary_tags.append("Vegetarian/Veg")
        if product.is_gluten_free:
            dietary_tags.append("Gluten-Free (GF)")
        if product.is_spicy:
            dietary_tags.append("Spicy/Hot")
        if not dietary_tags:
            dietary_tags.append("Standard")

        diet_str = ", ".join(dietary_tags)
        return (
            f"Dish: {product.name}. "
            f"Category: {product.category}. "
            f"Price: ${product.price:.2f}. "
            f"Calories: {product.calories or 'N/A'} kcal. "
            f"Dietary: {diet_str}. "
            f"Ingredients: {product.ingredients or ''}. "
            f"Description: {product.description}"
        )

    def sync_with_db(self):
        """Load all available products from StoreDB, compute embeddings, and upsert to Pinecone."""
        db = SessionLocal()
        try:
            products = db.query(Product).filter(Product.is_available == True).all()
            if not products:
                print("MenuVectorStore: No products found in StoreDB.")
                return

            self.documents = []
            texts = []
            for p in products:
                p_dict = p.to_dict()
                search_text = self._create_search_text(p)
                p_dict["search_text"] = search_text
                self.documents.append(p_dict)
                texts.append(search_text)

            print(f"MenuVectorStore: Indexing {len(self.documents)} products...")

            if not self.embedder:
                print("MenuVectorStore: Embedder not initialized. Skipping embedding generation.")
                return

            # Compute embeddings
            raw_vecs = self.embedder.embed_documents(texts)
            embeddings_array = np.array(raw_vecs, dtype=np.float32)
            # Normalize vectors
            norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
            norms[norms == 0] = 1e-10
            self._cached_embeddings = embeddings_array / norms

            # Upsert into Pinecone if available
            if self.index:
                try:
                    vectors_to_upsert = []
                    for p_dict, vec in zip(self.documents, raw_vecs):
                        metadata = {
                            "id": int(p_dict["id"]),
                            "name": str(p_dict["name"]),
                            "category": str(p_dict["category"]),
                            "price": float(p_dict["price"]),
                            "description": str(p_dict["description"]),
                            "ingredients": str(p_dict.get("ingredients") or ""),
                            "is_vegetarian": bool(p_dict.get("is_vegetarian", False)),
                            "is_gluten_free": bool(p_dict.get("is_gluten_free", False)),
                            "is_spicy": bool(p_dict.get("is_spicy", False)),
                            "calories": int(p_dict.get("calories") or 0),
                            "is_available": bool(p_dict.get("is_available", True)),
                            "image_url": str(p_dict.get("image_url") or ""),
                            "search_text": str(p_dict.get("search_text") or ""),
                        }
                        vectors_to_upsert.append({
                            "id": str(p_dict["id"]),
                            "values": [float(x) for x in vec],
                            "metadata": metadata,
                        })

                    # Upsert in batches of 50
                    for i in range(0, len(vectors_to_upsert), 50):
                        batch = vectors_to_upsert[i : i + 50]
                        self.index.upsert(vectors=batch)

                    print(f"MenuVectorStore: Upserted {len(vectors_to_upsert)} product vectors into Pinecone index '{self.index_name}'.")
                except Exception as e:
                    print(f"MenuVectorStore: Error upserting vectors to Pinecone ({e}).")

        finally:
            db.close()

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        is_vegetarian: Optional[bool] = None,
        is_gluten_free: Optional[bool] = None,
        is_spicy: Optional[bool] = None,
        max_price: Optional[float] = None,
        min_similarity: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search over menu items with metadata filters on Pinecone.
        """
        if not self.documents:
            self.sync_with_db()
            if not self.documents:
                return []

        if not self.embedder:
            return []

        # Generate query vector
        query_vec = self.embedder.embed_query(query)

        # 1. Query Pinecone if connected
        if self.index:
            try:
                filter_dict = {}
                if is_vegetarian is True:
                    filter_dict["is_vegetarian"] = {"$eq": True}
                if is_gluten_free is True:
                    filter_dict["is_gluten_free"] = {"$eq": True}
                if is_spicy is True:
                    filter_dict["is_spicy"] = {"$eq": True}
                if max_price is not None:
                    filter_dict["price"] = {"$lte": float(max_price)}

                # Query Pinecone
                query_res = self.index.query(
                    vector=[float(x) for x in query_vec],
                    top_k=max(top_k * 2, 10),
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None,
                )

                results = []
                for match in query_res.get("matches", []):
                    meta = match.get("metadata", {})
                    score = float(match.get("score", 0.0))

                    if min_similarity is not None and score < min_similarity:
                        continue
                    if category and category.lower() not in meta.get("category", "").lower():
                        continue

                    results.append({
                        "product": meta,
                        "similarity_score": round(score, 4),
                        "matched_text": meta.get("search_text", ""),
                    })

                    if len(results) >= top_k:
                        break

                if results:
                    return results
            except Exception as e:
                print(f"MenuVectorStore: Pinecone query error ({e}), falling back to cached vectors.")

        # 2. In-memory cosine similarity fallback using cached dense embeddings
        if self._cached_embeddings is not None and len(self.documents) > 0:
            query_arr = np.array(query_vec, dtype=np.float32)
            norm = np.linalg.norm(query_arr)
            if norm > 0:
                query_arr = query_arr / norm

            scores = np.dot(self._cached_embeddings, query_arr)
            results = []
            for idx, score in enumerate(scores):
                doc = self.documents[idx]

                if category and category.lower() not in doc.get("category", "").lower():
                    continue
                if is_vegetarian is True and not doc.get("is_vegetarian"):
                    continue
                if is_gluten_free is True and not doc.get("is_gluten_free"):
                    continue
                if is_spicy is True and not doc.get("is_spicy"):
                    continue
                if max_price is not None and doc.get("price", 0.0) > max_price:
                    continue

                sim_score = float(score)
                if min_similarity is not None and sim_score < min_similarity:
                    continue

                results.append({
                    "product": doc,
                    "similarity_score": round(sim_score, 4),
                    "matched_text": doc.get("search_text", ""),
                })

            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:top_k]

        return []

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all product items from store catalog."""
        if not self.documents:
            self.sync_with_db()
        return self.documents

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product metadata by ID."""
        for doc in self.get_all_products():
            if doc.get("id") == product_id:
                return doc
        return None

    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find product by exact or fuzzy name match."""
        name_lower = name.lower()
        for doc in self.get_all_products():
            if name_lower in doc.get("name", "").lower():
                return doc
        return None


# Global Singleton Instance
_menu_vector_store: Optional[MenuVectorStore] = None


def get_menu_vector_store() -> MenuVectorStore:
    global _menu_vector_store
    if _menu_vector_store is None:
        _menu_vector_store = MenuVectorStore()
    return _menu_vector_store
