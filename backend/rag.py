"""
RAG Pipeline — In-memory vector store + Gemini API embeddings.
Handles document ingestion, semantic search, and context assembly for LLM prompts.
"""

import logging
from typing import List, Dict, Optional
import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate the cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = sum(x * x for x in v1) ** 0.5
    norm_v2 = sum(x * x for x in v2) ** 0.5
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


class RAGPipeline:
    """Production-grade in-memory RAG system using Gemini Embeddings API."""

    def __init__(self):
        """Initialize in-memory structures."""
        self.collections: Dict[str, List[Dict]] = {}
        self._initialized = False

    def initialize(self):
        """Initialize connection/configurations for Gemini."""
        if self._initialized:
            return
        try:
            logger.info("Initializing in-memory RAG pipeline with Gemini Embeddings API...")
            # Verify if API key is configured
            if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
                genai.configure(api_key=settings.gemini_api_key)
            self._initialized = True
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            raise

    def get_embedding(self, text: str) -> List[float]:
        """Fetch embedding for a single text using Gemini API."""
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            logger.warning("Gemini API key not configured for embeddings. Using dummy zero embeddings.")
            return [0.0] * 768
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {e}")
            return [0.0] * 768

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Fetch embeddings for a batch of texts using Gemini API."""
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            return [[0.0] * 768 for _ in texts]
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=texts,
                task_type="retrieval_document"
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Gemini batch embedding generation failed: {e}")
            return [[0.0] * 768 for _ in texts]

    def ingest_documents(self, collection_name: str, documents: List[Dict]):
        """
        Ingest documents, calculate embeddings, and store them in memory.
        """
        if not self._initialized:
            self.initialize()

        try:
            if collection_name not in self.collections:
                self.collections[collection_name] = []

            existing_ids = {doc["id"] for doc in self.collections[collection_name]}
            new_docs = [doc for doc in documents if doc["id"] not in existing_ids]

            if not new_docs:
                logger.info(f"Collection '{collection_name}' already populated, skipping ingestion")
                return

            logger.info(f"Generating embeddings for {len(new_docs)} new documents in '{collection_name}'...")
            texts = [doc["text"] for doc in new_docs]
            
            # Embed in batches of 100 to avoid request size limits
            batch_size = 100
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_embeddings = self.get_embeddings_batch(batch_texts)
                embeddings.extend(batch_embeddings)

            # Store documents with their embeddings
            for doc, emb in zip(new_docs, embeddings):
                self.collections[collection_name].append({
                    "id": doc["id"],
                    "text": doc["text"],
                    "metadata": doc.get("metadata", {}),
                    "embedding": emb
                })

            logger.info(f"Ingested {len(new_docs)} documents into '{collection_name}' successfully")

        except Exception as e:
            logger.error(f"Ingestion failed for '{collection_name}': {e}")
            raise

    def semantic_search(
        self, query: str, collection_name: str, n_results: int = 5
    ) -> List[Dict]:
        """
        Perform semantic search against in-memory collection using cosine similarity.
        """
        if not self._initialized:
            self.initialize()

        try:
            docs = self.collections.get(collection_name, [])
            if not docs:
                logger.warning(f"Collection '{collection_name}' is empty or does not exist")
                return []

            # Get query embedding
            query_emb = self.get_embedding(query)

            # Calculate similarity for each document
            scored_docs = []
            for doc in docs:
                sim = cosine_similarity(query_emb, doc["embedding"])
                scored_docs.append({
                    "text": doc["text"],
                    "score": round(sim, 4),
                    "metadata": doc["metadata"]
                })

            # Sort by score descending and return top n_results
            scored_docs.sort(key=lambda x: x["score"], reverse=True)
            results = scored_docs[:n_results]

            logger.info(f"Search '{query}' in '{collection_name}': {len(results)} results")
            return results

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
