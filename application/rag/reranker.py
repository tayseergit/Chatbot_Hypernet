"""Reranker — re-scores and filters retrieved documents by relevance."""

from typing import Any, Dict, List, Tuple
from application.monitoring.logger import AppLogger


class Reranker:
    """Re-scores and filters retrieved documents based on distance thresholds."""

    def __init__(self, distance_threshold: float = 1.5):
        self._threshold = distance_threshold
        self._logger = AppLogger.get_logger("reranker")

    def rerank(self, documents: List[str], distances: List[float]) -> List[Tuple[str, float]]:
        """
        Rerank documents by distance and filter low-relevance results.

        Returns list of (document, distance) tuples sorted by relevance.
        """
        pairs = list(zip(documents, distances))
        # Filter by threshold
        filtered = [(doc, dist) for doc, dist in pairs if dist <= self._threshold]
        # Sort by distance (lower = more relevant)
        filtered.sort(key=lambda x: x[1])

        self._logger.info(
            f"Reranked: {len(pairs)} -> {len(filtered)} documents "
            f"(threshold={self._threshold})"
        )
        return filtered
