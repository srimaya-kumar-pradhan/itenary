"""
RAG Pipeline — ChromaDB vector store + SentenceTransformer embeddings.
Handles document ingestion, semantic search, and context assembly for LLM prompts.
"""

import logging
from typing import List, Dict, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Production-grade RAG system for travel data retrieval."""

    def __init__(self):
        """Initialize RAG components with lazy loading."""
        self.embedding_model: Optional[SentenceTransformer] = None
        self.chroma_client: Optional[chromadb.ClientAPI] = None
        self.collections: Dict = {}
        self._initialized = False

    def initialize(self):
        """Initialize embedding model and vector database."""
        if self._initialized:
            return

        try:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self.embedding_model = SentenceTransformer(settings.embedding_model)

            logger.info(f"Initializing ChromaDB at: {settings.vector_db_path}")
            self.chroma_client = chromadb.PersistentClient(
                path=settings.vector_db_path
            )

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
                    name=collection_name
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

        Args:
            destination: Target city
            preferences: User travel preferences
            budget: Total trip budget

        Returns:
            Assembled context string for LLM prompt
        """
        context_parts = []

        # Build search queries from destination + preferences
        queries = [
            f"Top tourist attractions and monuments in {destination}",
            f"Best restaurants and food in {destination}",
            f"Things to do and activities in {destination}",
        ]

        for pref in preferences:
            queries.append(f"{pref} experiences in {destination}")

        if budget < 5000:
            queries.append(f"Budget-friendly options in {destination}")
        elif budget > 30000:
            queries.append(f"Luxury experiences in {destination}")

        # Search each collection
        collection_names = ["monuments", "restaurants", "activities"]
        for coll_name in collection_names:
            for query in queries[:3]:  # Limit queries per collection
                results = self.semantic_search(query, coll_name, n_results=3)
                for r in results:
                    if r["score"] >= settings.similarity_threshold:
                        context_parts.append(r["text"])

        # Deduplicate and truncate
        seen = set()
        unique_parts = []
        for part in context_parts:
            key = part[:80]
            if key not in seen:
                seen.add(key)
                unique_parts.append(part)

        context = "\n\n".join(unique_parts[: 20])  # Cap at 20 entries
        if len(context) > settings.max_context_length:
            context = context[: settings.max_context_length]

        logger.info(f"Built context: {len(context)} chars, {len(unique_parts)} entries")
        return context


# Singleton instance
rag_pipeline = RAGPipeline()
