"""Document retriever — wraps ChromaDB vector queries."""

from typing import Any, Dict, List, Optional, Tuple
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics


class DocumentRetriever:
    """Retrieves relevant documents from ChromaDB vector store."""

    def __init__(self, collection, embedding_model):
        self._collection = collection
        self._embedding_model = embedding_model
        self._logger = AppLogger.get_logger("document_retriever")

    @log_operation()
    @track_metrics("rag_retrieve")
    def retrieve(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant documents for a query.

        Returns dict with 'documents', 'distances', 'ids'.
        """
        query_embedding = self._embedding_model.encode("query: " + query).tolist()

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "distances"],
        )

        self._logger.info(f"Retrieved {len(results['documents'][0])} documents")
        return {
            "documents": results["documents"][0],
            "distances": results["distances"][0],
            "ids": results["ids"][0],
        }
