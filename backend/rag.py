"""
RAG Pipeline — ChromaDB vector store + SentenceTransformer embeddings.
Handles document ingestion, semantic search, and context assembly for LLM prompts.
"""

import logging
from typing import List, Dict, Optional

import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings

from config import settings

logger = logging.getLogger(__name__)


class GeminiEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function using Google Gemini API."""

    def __call__(self, input: Documents) -> Embeddings:
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            logger.warning("Gemini API key not configured for embeddings. Using dummy zero embeddings.")
            return [[0.0] * 768 for _ in input]
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=input,
                task_type="retrieval_document"
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            # Fallback to zero vectors
            return [[0.0] * 768 for _ in input]


class RAGPipeline:
    """Production-grade RAG system for travel data retrieval."""

    def __init__(self):
        """Initialize RAG components with lazy loading."""
        self.embedding_function: Optional[GeminiEmbeddingFunction] = None
        self.chroma_client: Optional[chromadb.ClientAPI] = None
        self.collections: Dict = {}
        self._initialized = False

    def initialize(self):
        """Initialize embedding model and vector database."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Gemini Embedding Function...")
            self.embedding_function = GeminiEmbeddingFunction()

            logger.info("Initializing in-memory Ephemeral ChromaDB...")
            self.chroma_client = chromadb.EphemeralClient()

            self._initialized = True
            logger.info("RAG pipeline initialized successfully")

        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            raise

    def ingest_documents(self, collection_name: str, documents: List[Dict]):
        """
        Ingest documents into a named ChromaDB collection.

        Args:
            collection_name: e.g. 'monuments', 'restaurants', 'activities'
            documents: List of dicts with 'id', 'text', and optional 'metadata'
        """
        if not self._initialized:
            self.initialize()

        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function,
            )

            # Skip if already populated
            existing_count = collection.count()
            if existing_count >= len(documents):
                logger.info(
                    f"Collection '{collection_name}' already has {existing_count} docs, skipping ingestion"
                )
                self.collections[collection_name] = collection
                return

            ids = [doc["id"] for doc in documents]
            texts = [doc["text"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]

            # Convert metadata values to strings (ChromaDB requirement)
            clean_metadatas = []
            for m in metadatas:
                clean = {}
                for k, v in m.items():
                    if isinstance(v, (list, dict)):
                        import json
                        clean[k] = json.dumps(v)
                    else:
                        clean[k] = str(v)
                clean_metadatas.append(clean)

            # Batch upsert (ChromaDB handles dedup by ID)
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i : i + batch_size]
                batch_texts = texts[i : i + batch_size]
                batch_meta = clean_metadatas[i : i + batch_size]

                collection.upsert(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_meta,
                )

            self.collections[collection_name] = collection
            logger.info(
                f"Ingested {len(documents)} documents into '{collection_name}'"
            )

        except Exception as e:
            logger.error(f"Ingestion failed for '{collection_name}': {e}")
            raise

    def semantic_search(
        self, query: str, collection_name: str, n_results: int = 5
    ) -> List[Dict]:
        """
        Perform semantic search against a collection.

        Args:
            query: Natural language search query
            collection_name: Which collection to search
            n_results: Number of results to return

        Returns:
            List of matching documents with scores
        """
        if not self._initialized:
            self.initialize()

        try:
            collection = self.collections.get(collection_name)
            if collection is None:
                collection = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                )
                self.collections[collection_name] = collection

            if collection.count() == 0:
                logger.warning(f"Collection '{collection_name}' is empty")
                return []

            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count()),
            )

            formatted = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    score = 0.0
                    if results.get("distances") and results["distances"][0]:
                        # ChromaDB cosine distance: lower = more similar
                        score = 1.0 - results["distances"][0][i]

                    metadata = {}
                    if results.get("metadatas") and results["metadatas"][0]:
                        metadata = results["metadatas"][0][i]

                    formatted.append(
                        {
                            "text": doc,
                            "score": round(score, 4),
                            "metadata": metadata,
                        }
                    )

            logger.info(
                f"Search '{query}' in '{collection_name}': {len(formatted)} results"
            )
            return formatted

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def build_context(
        self, destination: str, preferences: List[str], budget: float
    ) -> str:
        """
        Build a rich context string by searching across all collections.
        Enhanced with city-scoped filtering, better deduplication,
        and result enrichment with coordinates/cost.

        Args:
            destination: Target city
            preferences: User travel preferences
            budget: Total trip budget

        Returns:
            Assembled context string for LLM prompt
        """
        context_parts = []

        # Build diversified search queries targeting different time slots
        queries = [
            f"Top tourist attractions and monuments in {destination}",
            f"Best restaurants and food in {destination}",
            f"Things to do and activities in {destination}",
            f"Morning sightseeing places in {destination}",
            f"Evening entertainment and dining in {destination}",
        ]

        for pref in preferences:
            queries.append(f"{pref} experiences in {destination}")

        if budget < 5000:
            queries.append(f"Budget-friendly options in {destination}")
        elif budget > 30000:
            queries.append(f"Luxury experiences in {destination}")

        # Search each collection with city-scoped filtering
        collection_names = ["monuments", "restaurants", "activities"]
        for coll_name in collection_names:
            for query in queries[:4]:  # Limit queries per collection
                results = self.semantic_search(query, coll_name, n_results=5)
                for r in results:
                    # Apply stricter relevance threshold
                    if r["score"] < settings.similarity_threshold:
                        continue

                    # City-scoped filtering: only accept results for this destination
                    metadata = r.get("metadata", {})
                    result_city = metadata.get("city", "").lower()
                    if result_city and result_city != destination.lower():
                        continue

                    # Enrich text with metadata (coordinates, cost, timing)
                    enriched_text = r["text"]
                    cost_str = metadata.get("cost", "")
                    timing_str = metadata.get("timing", "")
                    if cost_str:
                        enriched_text += f" [Entry cost: ₹{cost_str}]"
                    if timing_str:
                        enriched_text += f" [Hours: {timing_str}]"

                    context_parts.append(enriched_text)

        # Deduplicate by location name (extract first recognizable name)
        seen_names = set()
        unique_parts = []
        for part in context_parts:
            # Use first 60 chars as a dedup key, lowered
            dedup_key = part[:60].lower().strip()
            if dedup_key not in seen_names:
                seen_names.add(dedup_key)
                unique_parts.append(part)

        context = "\n\n".join(unique_parts[:20])  # Cap at 20 entries
        if len(context) > settings.max_context_length:
            context = context[: settings.max_context_length]

        logger.info(
            f"Built context for {destination}: {len(context)} chars, "
            f"{len(unique_parts)} unique entries (from {len(context_parts)} raw)"
        )
        return context


# Singleton instance
rag_pipeline = RAGPipeline()
