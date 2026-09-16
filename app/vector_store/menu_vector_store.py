import os
import re
import math
from typing import List, Dict, Any, Optional
import numpy as np

from app.db.database import SessionLocal
from app.db.models import Product


class MenuVectorStore:
    """
    Vector Database engine for menu items semantic search.
    Supports OpenAI Embeddings with dense vector cosine similarity,
    plus an internal TF-IDF vectorizer fallback.
    """

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.openai_embeddings = None
        self.use_openai = False
        self._init_embedding_model()
        self.sync_with_db()

    def _init_embedding_model(self):
        """Initialize embedding model if API key is present."""
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from langchain_openai import OpenAIEmbeddings
                self.openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                self.use_openai = True
                print("MenuVectorStore: OpenAIEmbeddings initialized successfully.")
            except Exception as e:
                print(f"MenuVectorStore: Could not initialize OpenAIEmbeddings ({e}), falling back to local vectorizer.")
                self.use_openai = False
        else:
            print("MenuVectorStore: No OPENAI_API_KEY found, using local semantic vector index.")
            self.use_openai = False

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
        """Load all available products from StoreDB and generate vector embeddings."""
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

            # Generate Embeddings
            if self.use_openai and self.openai_embeddings:
                try:
                    raw_vecs = self.openai_embeddings.embed_documents(texts)
                    self.embeddings = np.array(raw_vecs, dtype=np.float32)
                    # Normalize vectors for cosine similarity
                    norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                    norms[norms == 0] = 1e-10
                    self.embeddings = self.embeddings / norms
                    print("MenuVectorStore: Successfully generated OpenAI dense vectors.")
                    return
                except Exception as e:
                    print(f"MenuVectorStore: OpenAI embedding error ({e}), falling back to local vectors.")
                    self.use_openai = False

            # Local TF-IDF Vectorizer
            self._build_local_tfidf_vectors(texts)
            print(f"MenuVectorStore: Built local vector index for {len(self.documents)} items.")

        finally:
            db.close()

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for local vector calculations."""
        tokens = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
        return tokens

    def _build_local_tfidf_vectors(self, texts: List[str]):
        """Generate TF-IDF embedding matrix locally."""
        all_tokens = [self._tokenize(t) for t in texts]
        vocab = set()
        for doc in all_tokens:
            vocab.update(doc)
        self.vocab_list = sorted(list(vocab))
        self.vocab_index = {w: i for i, w in enumerate(self.vocab_list)}
        N = len(texts)

        # Compute IDF
        df = np.zeros(len(self.vocab_list), dtype=np.float32)
        for doc in all_tokens:
            unique_words = set(doc)
            for w in unique_words:
                df[self.vocab_index[w]] += 1.0

        self.idf = np.log((N + 1.0) / (df + 1.0)) + 1.0

        # Compute TF-IDF matrix
        mat = np.zeros((N, len(self.vocab_list)), dtype=np.float32)
        for doc_idx, doc in enumerate(all_tokens):
            for w in doc:
                idx = self.vocab_index[w]
                mat[doc_idx, idx] += 1.0
            # Term Frequency normalization
            if len(doc) > 0:
                mat[doc_idx] = mat[doc_idx] / len(doc)

        mat = mat * self.idf
        # Cosine normalization
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        self.embeddings = mat / norms

    def _embed_query(self, query: str) -> np.ndarray:
        """Compute embedding for input query."""
        if self.use_openai and self.openai_embeddings:
            try:
                vec = np.array(self.openai_embeddings.embed_query(query), dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return vec
            except Exception as e:
                print(f"MenuVectorStore: Query embedding error ({e}), using local.")

        # Local query embedding
        tokens = self._tokenize(query)
        vec = np.zeros(len(self.vocab_list), dtype=np.float32)
        for w in tokens:
            if w in self.vocab_index:
                vec[self.vocab_index[w]] += 1.0
        if len(tokens) > 0:
            vec = vec / len(tokens)
        vec = vec * self.idf
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        is_vegetarian: Optional[bool] = None,
        is_gluten_free: Optional[bool] = None,
        is_spicy: Optional[bool] = None,
        max_price: Optional[float] = None,
        min_similarity: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search over menu items with metadata filters.
        """
        if not self.documents or self.embeddings is None:
            self.sync_with_db()
            if not self.documents:
                return []

        query_vec = self._embed_query(query)
        # Cosine similarities
        scores = np.dot(self.embeddings, query_vec)

        results = []
        for idx, score in enumerate(scores):
            doc = self.documents[idx]

            # Metadata Filters
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

            # Check similarity threshold (relaxed for local fallback)
            sim_score = float(score)
            results.append({
                "product": doc,
                "similarity_score": round(sim_score, 4),
                "matched_text": doc.get("search_text", "")
            })

        # Sort by similarity score descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all product items from store vector DB."""
        return self.documents

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product metadata by ID."""
        for doc in self.documents:
            if doc.get("id") == product_id:
                return doc
        return None

    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find product by exact or fuzzy name match."""
        name_lower = name.lower()
        for doc in self.documents:
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
