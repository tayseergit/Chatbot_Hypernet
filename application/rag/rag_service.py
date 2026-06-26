"""
RAG service — main orchestrator for document retrieval and context building.

Handles: XLS loading -> chunking -> embedding -> ChromaDB -> retrieval -> reranking -> context.
"""

import time
from typing import Any, Dict, List, Optional

from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.aspects.exception_aspect import handle_exceptions
from application.rag.document_retriever import DocumentRetriever
from application.rag.reranker import Reranker
from application.rag.context_builder import ContextBuilder
from application.shared.dto.service_result import ServiceResult
from application.shared.configuration.app_config import RAGConfig
from application.shared.exceptions.app_exceptions import RAGRetrievalError


class RAGService:
    """
    Main RAG orchestrator.

    Initializes the knowledge base from XLS file, and handles queries
    through retrieval -> reranking -> context building pipeline.
    """

    def __init__(self, config: RAGConfig):
        self._config = config
        self._logger = AppLogger.get_logger("rag_service")
        self._retriever: Optional[DocumentRetriever] = None
        self._reranker = Reranker(distance_threshold=config.distance_threshold)
        self._context_builder = ContextBuilder()
        self._embedding_model = None
        self._collection = None
        self._initialized = False

    @log_operation()
    def initialize(self, knowledge_file: str = None) -> None:
        """Load knowledge base from XLS file into ChromaDB."""
        file_path = knowledge_file or self._config.knowledge_file
        self._logger.info(f"Initializing RAG from: {file_path}")

        # Load embedding model
        from sentence_transformers import SentenceTransformer
        self._embedding_model = SentenceTransformer(self._config.embedding_model)

        # Read XLS file
        text = self._read_xls(file_path)
        self._logger.info(f"Loaded {len(text)} characters from XLS")

        # Chunk the text
        chunks = self._split_text(text, self._config.chunk_size, self._config.overlap)
        self._logger.info(f"Created {len(chunks)} chunks")

        # Initialize ChromaDB
        import sqlite3
        if sqlite3.sqlite_version_info < (3, 35, 0):
            sqlite3.sqlite_version_info = (3, 35, 0)
        import chromadb
        chroma_client = chromadb.Client()
        try:
            chroma_client.delete_collection(self._config.collection_name)
        except Exception:
            pass

        self._collection = chroma_client.create_collection(self._config.collection_name)

        # Embed and store chunks
        for i, chunk in enumerate(chunks):
            embedding = self._embedding_model.encode("passage: " + chunk).tolist()
            self._collection.add(
                ids=[str(i)], documents=[chunk], embeddings=[embedding],
            )

        # Create retriever
        self._retriever = DocumentRetriever(self._collection, self._embedding_model)
        self._initialized = True
        self._logger.info("RAG initialization complete")

    @log_operation()
    @track_metrics("rag_query")
    @handle_exceptions(reraise=True)
    def query(self, question: str, n_results: int = None) -> ServiceResult:
        """
        Query the RAG system.

        Returns ServiceResult with context and retrieved documents.
        """
        if not self._initialized:
            return ServiceResult.failure("RAG", "RAG service not initialized")

        start = time.time()
        n = n_results or self._config.n_results

        # Retrieve
        raw_results = self._retriever.retrieve(question, n_results=n)

        # Rerank
        ranked = self._reranker.rerank(
            raw_results["documents"], raw_results["distances"],
        )

        # Build context
        context = self._context_builder.build_context(ranked)

        latency = (time.time() - start) * 1000
        return ServiceResult(
            source="RAG", success=True,
            data={"context": context, "documents": [d for d, _ in ranked],
                  "distances": [dist for _, dist in ranked]},
            latency_ms=latency,
        )

    def _read_xls(self, path: str) -> str:
        """Read text content from an XLS/XLSX file."""
        import pandas as pd
        try:
            df = pd.read_excel(path)
            text_parts = []
            for _, row in df.iterrows():
                row_text = " ".join(str(val) for val in row.values if pd.notna(val))
                if row_text.strip():
                    text_parts.append(row_text.strip())
            return "\n".join(text_parts)
        except Exception as e:
            self._logger.error(f"Failed to read XLS file: {e}")
            raise RAGRetrievalError(f"Failed to read knowledge file: {e}")

    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap
        return chunks
